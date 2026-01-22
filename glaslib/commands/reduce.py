from __future__ import annotations

import shlex
from typing import Optional, Tuple

from glaslib.commands.common import AppState
from glaslib.core.parallel import run_jobs
from glaslib.reduce import prepare_reduce_project


def _parse_args(arg: str) -> Tuple[Optional[int], bool]:
    toks = shlex.split(arg)
    jobs: Optional[int] = None
    micoef: bool = False
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == "--jobs" and i + 1 < len(toks):
            jobs = int(toks[i + 1])
            i += 2
            continue
        if t == "--jobs":
            raise ValueError("Missing value after --jobs")
        if t == "--micoef":
            micoef = True
            i += 1
            continue
        i += 1
    return jobs, micoef


def _resolve_jobs(state: AppState, jobs: Optional[int]) -> int:
    if jobs is not None:
        return max(1, int(jobs))
    meta_jobs = None
    if isinstance(state.ctx.meta, dict):
        meta_jobs = state.ctx.meta.get("jobs_requested")
    try:
        return max(1, int(meta_jobs or 1))
    except Exception:
        return 1


def run(state: AppState, arg: str) -> None:
    try:
        jobs_opt, micoef = _parse_args(arg)
    except ValueError as exc:
        print(f"Usage: reduce [--jobs K] [--micoef] ({exc})")
        return

    if not state.ensure_run():
        return

    jobs_req = _resolve_jobs(state, jobs_opt)

    try:
        out = prepare_reduce_project(state.ctx.run_dir, jobs=jobs_req, micoef=micoef)
    except Exception as exc:
        print(f"[reduce] Error: {exc}")
        return

    form_dir = out["form_dir"]
    jobs_eff = out["jobs_effective"]
    drivers = out["drivers"]
    master_driver = out.get("master_driver")
    sum_driver = out.get("sum_master_driver")

    tasks = [(f"reduce_J{k}of{jobs_eff}", form_dir, drv) for k, drv in drivers.items()]
    ok_reduce = run_jobs(state.form_exe, tasks, max_workers=jobs_eff)

    ok_master = True
    if ok_reduce and master_driver is not None:
        ok_master = run_jobs(
            state.form_exe,
            [("MasterCoefficients", form_dir, master_driver)],
            max_workers=1,
        )
        if ok_master:
            print("[reduce] Master coefficient projection finished OK.")
    elif master_driver is not None:
        print("[reduce] Skipping master coefficient projection because reduction failed.")

    ok_sum = True
    if ok_reduce and ok_master and sum_driver is not None:
        ok_sum = run_jobs(
            state.form_exe,
            [("SumMasterCoefs", form_dir, sum_driver)],
            max_workers=1,
        )
        if ok_sum:
            print("[reduce] Master coefficient summation finished OK.")
    elif sum_driver is not None:
        print("[reduce] Skipping master coefficient summation because prior steps failed.")

    if ok_reduce and ok_master and ok_sum:
        print("[reduce] All jobs finished OK.")

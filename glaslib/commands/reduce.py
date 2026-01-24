from __future__ import annotations

import shlex
from typing import Optional, Tuple

from glaslib.commands.common import AppState
from glaslib.core.logging import LOG_SUBDIR_REDUCE
from glaslib.core.parallel import run_jobs
from glaslib.reduce import prepare_reduce_project


def _parse_args(arg: str) -> Tuple[Optional[int], bool]:
    """Parse reduce arguments.
    
    Returns:
        (jobs, verbose)
    """
    toks = shlex.split(arg)
    jobs: Optional[int] = None
    verbose: bool = False
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == "--jobs" and i + 1 < len(toks):
            jobs = int(toks[i + 1])
            i += 2
            continue
        if t == "--jobs":
            raise ValueError("Missing value after --jobs")
        if t in ("--verbose", "-v"):
            verbose = True
            i += 1
            continue
        if t in ("--quiet", "-q"):
            verbose = False
            i += 1
            continue
        i += 1
    return jobs, verbose


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
    """
    Run the reduce command (M0M1top -> M0M1Reduced).
    
    Usage:
        reduce [--jobs K] [--verbose] - Run IBP reduction to produce M0M1Reduced
    """
    try:
        jobs_opt, verbose = _parse_args(arg)
    except ValueError as exc:
        print(f"Usage: reduce [--jobs K] [--verbose] ({exc})")
        return

    verbose = verbose or state.verbose

    if not state.ensure_run():
        return

    jobs_req = _resolve_jobs(state, jobs_opt)

    try:
        out = prepare_reduce_project(state.ctx.run_dir, jobs=jobs_req)
    except Exception as exc:
        print(f"[reduce] Error: {exc}")
        return

    form_dir = out["form_dir"]
    jobs_eff = out["jobs_effective"]
    drivers = out["drivers"]

    tasks = [(f"reduce_J{k}of{jobs_eff}", form_dir, drv) for k, drv in drivers.items()]
    ok_reduce = run_jobs(
        state.form_exe,
        tasks,
        max_workers=jobs_eff,
        verbose=verbose,
        run_dir=state.ctx.run_dir,
        log_subdir=LOG_SUBDIR_REDUCE,
    )

    if ok_reduce:
        print("[reduce] All reduction jobs finished OK.")
    else:
        print("[reduce] Reduction failed. Check logs.")

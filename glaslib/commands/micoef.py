from __future__ import annotations

import shlex
from typing import Optional, Tuple

from glaslib.commands.common import AppState
from glaslib.core.logging import LOG_SUBDIR_REDUCE, ensure_logs_dir
from glaslib.core.parallel import run_jobs
from glaslib.reduce import prepare_micoef_project


def _parse_args(arg: str) -> Tuple[Optional[int], bool, bool]:
    """Parse micoef arguments.
    
    Returns:
        (jobs, combine, verbose)
    """
    toks = shlex.split(arg)
    jobs: Optional[int] = None
    combine: bool = False
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
        if t == "--combine":
            combine = True
            i += 1
            continue
        if t in ("--verbose", "-v"):
            verbose = True
            i += 1
            continue
        if t in ("--quiet", "-q"):
            verbose = False
            i += 1
            continue
        i += 1
    return jobs, combine, verbose


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
    Run the micoef command (master integral coefficient extraction).
    
    Usage:
        micoef [--jobs K] [--verbose]           - Run MasterCoefficients only (parallelized by nmis)
        micoef --combine [--jobs K] [--verbose] - Run MasterCoefficients + SumMasterCoefs
    """
    try:
        jobs_opt, combine, verbose = _parse_args(arg)
    except ValueError as exc:
        print(f"Usage: micoef [--jobs K] [--combine] [--verbose] ({exc})")
        return

    verbose = verbose or state.verbose

    if not state.ensure_run():
        return

    jobs_req = _resolve_jobs(state, jobs_opt)

    try:
        out = prepare_micoef_project(state.ctx.run_dir, jobs=jobs_req)
    except Exception as exc:
        print(f"[micoef] Error: {exc}")
        return

    form_dir = out["form_dir"]
    jobs_eff_master = out["jobs_eff_master"]
    jobs_eff_sum = out["jobs_eff_sum"]
    n0l = out["n0l"]
    nmis = out["nmis"]
    master_drivers = out["master_drivers"]
    sum_drivers = out["sum_drivers"]

    # Always run MasterCoefficients (parallelized by n0l)
    print(f"[micoef] Running MasterCoefficients ({jobs_eff_master} jobs for {n0l} tree diagrams)...")
    master_tasks = [
        (f"MasterCoefficients_J{k}of{jobs_eff_master}", form_dir, drv)
        for k, drv in master_drivers.items()
    ]
    ok_master = run_jobs(
        state.form_exe,
        master_tasks,
        max_workers=jobs_eff_master,
        verbose=verbose,
        run_dir=state.ctx.run_dir,
        log_subdir=LOG_SUBDIR_REDUCE,
    )

    if not ok_master:
        print("[micoef] MasterCoefficients failed. Check logs.")
        return

    print("[micoef] MasterCoefficients finished OK.")

    if combine:
        # Also run SumMasterCoefs (parallelized by nmis)
        print(f"[micoef --combine] Running SumMasterCoefs ({jobs_eff_sum} jobs for {nmis} master integrals)...")
        sum_tasks = [
            (f"SumMasterCoefs_J{k}of{jobs_eff_sum}", form_dir, drv)
            for k, drv in sum_drivers.items()
        ]
        ok_sum = run_jobs(
            state.form_exe,
            sum_tasks,
            max_workers=jobs_eff_sum,
            verbose=verbose,
            run_dir=state.ctx.run_dir,
            log_subdir=LOG_SUBDIR_REDUCE,
        )

        if ok_sum:
            print("[micoef --combine] SumMasterCoefs finished OK.")
        else:
            print("[micoef --combine] SumMasterCoefs failed. Check logs.")
    else:
        print("[micoef] Run 'micoef --combine' to sum coefficients across diagrams.")

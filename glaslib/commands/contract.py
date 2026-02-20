from __future__ import annotations

from typing import Optional

from glaslib.commands.common import AppState, MODES, parse_mode_and_flags
from glaslib.contracts import prepare_lo, prepare_mct, prepare_nlo
from glaslib.core.logging import LOG_SUBDIR_CONTRACT
from glaslib.core.parallel import run_jobs


def _resolve_jobs_requested(state: AppState, jobs: Optional[int]) -> int:
    if jobs is not None:
        return max(1, int(jobs))
    meta_jobs = state.ctx.meta.get("jobs_requested") if isinstance(state.ctx.meta, dict) else None
    try:
        return max(1, int(meta_jobs or 1))
    except Exception:
        return 1


def run(state: AppState, arg: str) -> None:
    mode, jobs, _, verbose = parse_mode_and_flags(arg, allow_dirac=False)
    verbose = verbose or state.verbose  # Also check state.verbose
    if mode not in MODES:
        print("Usage: contract {lo|nlo|mct} [--jobs K] [--verbose]")
        return
    if not state.ensure_run():
        return

    # Check if massless model - no mass counterterms needed
    model_id = state.ctx.meta.get("model_id", "qcd_massive") if isinstance(state.ctx.meta, dict) else "qcd_massive"
    if mode == "mct" and model_id == "qcd_massless":
        print("[contract mct] Skipped: mass counterterms are zero for massless QCD.")
        return

    jobs_req = _resolve_jobs_requested(state, jobs)
    process_str = state.ctx.meta.get("process", "") if isinstance(state.ctx.meta, dict) else ""
    gluon_refs = state.refs().get_or_prompt(process_str)

    try:
        if mode == "lo":
            out = prepare_lo(state.ctx, gluon_refs=gluon_refs, jobs=jobs_req)
        elif mode == "nlo":
            out = prepare_nlo(state.ctx, gluon_refs=gluon_refs, jobs=jobs_req)
        else:
            out = prepare_mct(state.ctx, gluon_refs=gluon_refs, jobs=jobs_req)
    except Exception as exc:
        print(f"Error: {exc}")
        return

    form_dir = out["form_dir"]
    jobs_eff = out["jobs_effective"]
    tasks = [(f"contract_{mode}_J{k}of{jobs_eff}", form_dir, drv) for k, drv in out["drivers"].items()]
    ok = run_jobs(state.form_exe, tasks, max_workers=jobs_eff, verbose=verbose, run_dir=state.ctx.run_dir, log_subdir=LOG_SUBDIR_CONTRACT)
    if ok:
        print(f"[contract {mode}] All jobs finished OK.")

from __future__ import annotations

from glaslib.commands.common import AppState, parse_simple_flags
from glaslib.ioperator import prepare_ioperator_master, prepare_ir_full, prepare_total_lo
from glaslib.core.logging import LOG_SUBDIR_IOPERATOR
from glaslib.core.parallel import run_jobs


def run(state: AppState, arg: str) -> None:
    # Parse --verbose flag
    remainder, verbose = parse_simple_flags(arg)
    verbose = verbose or state.verbose  # Also check state.verbose
    
    if remainder.strip():
        print("Usage: ioperator [--verbose]")
        return
    if not state.ensure_run():
        return

    meta = state.ctx.meta
    process_str = meta.get("process", "") if isinstance(meta, dict) else ""
    gluon_refs = state.refs().get_or_prompt(process_str)

    try:
        bundle = prepare_ir_full(state.ctx, gluon_refs=gluon_refs)
    except Exception as exc:
        print(f"Error preparing Ioperators: {exc}")
        return

    jobs = [(f"Ioperator_{i}x{j}", info["form_dir"], info["driver"]) for i, j, info in bundle["drivers"]]
    ok_pairs = run_jobs(state.form_exe, jobs, max_workers=min(len(jobs), 4), verbose=verbose, run_dir=state.ctx.run_dir, log_subdir=LOG_SUBDIR_IOPERATOR) if jobs else True
    if not ok_pairs:
        return

    try:
        tot = prepare_total_lo(state.ctx)
    except Exception as exc:
        print(f"Error preparing TotalLO: {exc}")
        return
    ok_total = run_jobs(state.form_exe, [("TotalLO", tot["form_dir"], tot["driver"])], max_workers=1, verbose=verbose, run_dir=state.ctx.run_dir, log_subdir=LOG_SUBDIR_IOPERATOR)
    if not ok_total:
        return

    try:
        master = prepare_ioperator_master(state.ctx, gluon_refs=gluon_refs)
    except Exception as exc:
        print(f"Error preparing master Ioperator: {exc}")
        return

    ok_master = run_jobs(state.form_exe, [("Ioperator_master", master["form_dir"], master["driver"])], max_workers=1, verbose=verbose, run_dir=state.ctx.run_dir, log_subdir=LOG_SUBDIR_IOPERATOR)
    if ok_master:
        print("[ioperator] Completed.")

from __future__ import annotations

from glas.commands.common import AppState
from glaslib.ioperator import prepare_ioperator_master, prepare_ir_full, prepare_total_lo
from glaslib.parallel import run_jobs


def run(state: AppState, arg: str) -> None:
    if arg.strip():
        print("Usage: ioperator")
        return
    if not state.ensure_run():
        return

    meta = state.ctx.meta
    process_str = meta.get("process", "") if isinstance(meta, dict) else ""
    gluon_refs = state.get_or_prompt_gluon_refs(process_str)

    try:
        bundle = prepare_ir_full(state.ctx, gluon_refs=gluon_refs)
    except Exception as exc:
        print(f"Error preparing Ioperators: {exc}")
        return

    jobs = [(f"Ioperator_{i}x{j}", info["form_dir"], info["driver"]) for i, j, info in bundle["drivers"]]
    ok_pairs = run_jobs(state.config.form_exe, jobs, max_workers=min(len(jobs), 4)) if jobs else True
    if not ok_pairs:
        return

    try:
        tot = prepare_total_lo(state.ctx)
    except Exception as exc:
        print(f"Error preparing TotalLO: {exc}")
        return
    ok_total = run_jobs(state.config.form_exe, [("TotalLO", tot["form_dir"], tot["driver"])], max_workers=1)
    if not ok_total:
        return

    try:
        master = prepare_ioperator_master(state.ctx, gluon_refs=gluon_refs)
    except Exception as exc:
        print(f"Error preparing master Ioperator: {exc}")
        return

    ok_master = run_jobs(state.config.form_exe, [("Ioperator_master", master["form_dir"], master["driver"])], max_workers=1)
    if ok_master:
        print("[ioperator] Completed.")

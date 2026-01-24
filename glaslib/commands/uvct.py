from __future__ import annotations

from glaslib.commands.common import AppState, parse_simple_flags
from glaslib.getct import prepare_getct
from glaslib.mathematica_totals import write_total_to_uvct
from glaslib.core.logging import LOG_SUBDIR_UVCT
from glaslib.core.parallel import run_jobs


def run(state: AppState, arg: str) -> None:
    # Parse --verbose flag
    remainder, verbose = parse_simple_flags(arg)
    verbose = verbose or state.verbose  # Also check state.verbose
    
    if remainder.strip():
        print("Usage: uvct [--verbose]")
        return
    if not state.ensure_run():
        return

    try:
        drivers = prepare_getct(state.ctx, form_exe=state.form_exe)
    except Exception as exc:
        print(f"Error: {exc}")
        return

    for name in ("Vas", "Vzt", "Vg"):
        driver = drivers.get(name)
        if not driver:
            print(f"Error: missing driver for {name}")
            return
        form_dir = driver.parent
        ok = run_jobs(state.form_exe, [(name, form_dir, driver)], max_workers=1, verbose=verbose, run_dir=state.ctx.run_dir, log_subdir=LOG_SUBDIR_UVCT)
        if not ok:
            return
        if state.ctx.run_dir and write_total_to_uvct(state.ctx.run_dir, name, name):
            print(f"  UVCT/{name}.m updated.")
        else:
            print(f"  UVCT/{name}.m not written (missing inputs).")

    if state.ctx.run_dir and write_total_to_uvct(state.ctx.run_dir, "Vm", "Vm"):
        print("  UVCT/Vm.m updated.")
    else:
        print("  UVCT/Vm.m not written (missing inputs).")

    print("[uvct] Completed.")

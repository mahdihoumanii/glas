from __future__ import annotations

import json
from pathlib import Path

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

    is_massless = drivers.get("is_massless", False)
    is_higgs = drivers.get("is_higgs", False)

    # Standard counterterms: Vas, Vzt, Vg
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

    # Vyuk (Yukawa counterterm) for Higgs+QCD model
    if is_higgs and "Vyuk" in drivers:
        driver = drivers["Vyuk"]
        form_dir = driver.parent
        ok = run_jobs(state.form_exe, [("Vyuk", form_dir, driver)], max_workers=1, verbose=verbose, run_dir=state.ctx.run_dir, log_subdir=LOG_SUBDIR_UVCT)
        if not ok:
            return
        if state.ctx.run_dir and write_total_to_uvct(state.ctx.run_dir, "Vyuk", "Vyuk"):
            print("  UVCT/Vyuk.m updated.")
        else:
            print("  UVCT/Vyuk.m not written (missing inputs).")
    elif is_higgs:
        # No Yukawa vertices in this process
        if state.ctx.run_dir:
            uvct_dir = Path(state.ctx.run_dir) / "Mathematica" / "Files" / "UVCT"
            uvct_dir.mkdir(parents=True, exist_ok=True)
            (uvct_dir / "Vyuk.m").write_text("Vyuk = 0;\n", encoding="utf-8")
            print("  UVCT/Vyuk.m = 0 (no Yukawa vertices).")

    # Write Vm: for massless, just write Vm = 0
    if is_massless:
        if state.ctx.run_dir:
            uvct_dir = Path(state.ctx.run_dir) / "Mathematica" / "Files" / "UVCT"
            uvct_dir.mkdir(parents=True, exist_ok=True)
            (uvct_dir / "Vm.m").write_text("Vm = 0;\n", encoding="utf-8")
            print("  UVCT/Vm.m = 0 (massless QCD: no mass counterterms).")
    else:
        if state.ctx.run_dir and write_total_to_uvct(state.ctx.run_dir, "Vm", "Vm"):
            print("  UVCT/Vm.m updated.")
        else:
            print("  UVCT/Vm.m not written (missing inputs).")

    print("[uvct] Completed.")

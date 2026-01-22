from __future__ import annotations

import os
import subprocess
from pathlib import Path

from glaslib.commands.common import AppState


def run(state: AppState, arg: str) -> None:
    if arg.strip():
        print("Usage: linrels")
        return
    if not state.ensure_run():
        return

    run_dir = state.ctx.run_dir
    if not run_dir:
        print("[linrels] Error: no run attached.")
        return

    repo_root = Path(__file__).resolve().parents[2]
    src = repo_root / "mathematica" / "scripts" / "LinearRelations.m"
    if not src.exists():
        print(f"[linrels] Missing script: {src}")
        return

    run_mat_dir = run_dir / "Mathematica"
    run_mat_dir.mkdir(parents=True, exist_ok=True)
    (run_mat_dir / "Files").mkdir(parents=True, exist_ok=True)
    dst = run_mat_dir / "LinearRelations.m"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    env = os.environ.copy()

    log_out = run_mat_dir / "LinearRelations.stdout.log"
    log_err = run_mat_dir / "LinearRelations.stderr.log"

    print("[linrels] Running LinearRelations.m ...")
    res = subprocess.run(
        ["wolframscript", "-file", str(dst)],
        cwd=str(run_mat_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    log_out.write_text(res.stdout or "", encoding="utf-8")
    log_err.write_text(res.stderr or "", encoding="utf-8")

    if res.returncode != 0:
        print(f"[linrels] Failed (code={res.returncode}).")
        print(f"  stdout: {log_out}")
        print(f"  stderr: {log_err}")
        return

    expected = run_mat_dir / "Files" / "MasterCoefficients.m"
    if expected.exists():
        print(f"[linrels] OK -> {expected}")
    else:
        print("[linrels] Completed but Files/MasterCoefficients.m not found. Check logs.")
        print(f"  stdout: {log_out}")
        print(f"  stderr: {log_err}")

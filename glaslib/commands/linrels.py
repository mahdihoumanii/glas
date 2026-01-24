from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Tuple

from glaslib.commands.common import AppState
from glaslib.core.logging import LOG_SUBDIR_LINRELS, ensure_logs_dir
from glaslib.core.proc import run_streaming


def _parse_args(arg: str) -> Tuple[bool, bool]:
    """Parse linrels arguments.
    
    Returns:
        (combine, verbose)
    """
    toks = shlex.split(arg)
    combine: bool = False
    verbose: bool = False
    for t in toks:
        if t == "--combine":
            combine = True
        elif t in ("--verbose", "-v"):
            verbose = True
        elif t in ("--quiet", "-q"):
            verbose = False
    return combine, verbose


def run(state: AppState, arg: str) -> None:
    """
    Run the linrels command.
    
    Usage:
        linrels [--verbose]           - Run LinearRelations.m only
        linrels --combine [--verbose] - Run LinearRelations.m then CombineLinearRelations.m
    """
    combine, verbose = _parse_args(arg)
    verbose = verbose or state.verbose  # Also check state.verbose
    
    if not state.ensure_run():
        return

    run_dir = state.ctx.run_dir
    if not run_dir:
        print("[linrels] Error: no run attached.")
        return

    repo_root = Path(__file__).resolve().parents[2]
    run_mat_dir = run_dir / "Mathematica"
    run_mat_dir.mkdir(parents=True, exist_ok=True)
    (run_mat_dir / "Files").mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()

    # Create logs directory using centralized constants
    logs_dir = ensure_logs_dir(run_dir, LOG_SUBDIR_LINRELS)

    # Always run LinearRelations.m first
    src_linrel = repo_root / "mathematica" / "scripts" / "LinearRelations.m"
    if not src_linrel.exists():
        print(f"[linrels] Missing script: {src_linrel}")
        return

    dst_linrel = run_mat_dir / "LinearRelations.m"
    dst_linrel.write_text(src_linrel.read_text(encoding="utf-8"), encoding="utf-8")

    log_linrel = logs_dir / "LinearRelations.log"

    if verbose:
        print("[mma linrels] Running LinearRelations.m...")
    else:
        print("[linrels] Running LinearRelations.m ...")

    rc = run_streaming(
        cmd=["wolframscript", "-file", str(dst_linrel)],
        cwd=run_mat_dir,
        env=env,
        log_path=log_linrel,
        prefix="mma linrels",
        verbose=verbose,
    )
    if rc != 0:
        print(f"[linrels] Failed (code={rc}). See {log_linrel}")
        return

    print(f"[linrels] LinearRelations.m OK. (log: {log_linrel})")

    if combine:
        # Also run CombineLinearRelations.m
        src_combine = repo_root / "mathematica" / "scripts" / "CombineLinearRelations.m"
        if not src_combine.exists():
            print(f"[linrels --combine] Missing script: {src_combine}")
            return

        dst_combine = run_mat_dir / "CombineLinearRelations.m"
        dst_combine.write_text(src_combine.read_text(encoding="utf-8"), encoding="utf-8")

        log_combine = logs_dir / "CombineLinearRelations.log"

        if verbose:
            print("[mma linrels --combine] Running CombineLinearRelations.m...")
        else:
            print("[linrels --combine] Running CombineLinearRelations.m ...")

        rc = run_streaming(
            cmd=["wolframscript", "-file", str(dst_combine)],
            cwd=run_mat_dir,
            env=env,
            log_path=log_combine,
            prefix="mma linrels --combine",
            verbose=verbose,
        )
        if rc != 0:
            print(f"[linrels --combine] Failed (code={rc}). See {log_combine}")
            return

        expected = run_mat_dir / "Files" / "MasterCoefficients.m"
        if expected.exists():
            if not verbose:
                print(f"[linrels --combine] OK -> {expected} (log: {log_combine})")
            else:
                print(f"[linrels --combine] OK -> {expected}")
            
            # Copy AmpResult script based on particle count
            _copy_amp_result_script(run_dir, run_mat_dir, repo_root, state)
        else:
            print(f"[linrels --combine] Completed but Files/MasterCoefficients.m not found. See {log_combine}")


def _copy_amp_result_script(run_dir: Path, run_mat_dir: Path, repo_root: Path, state: AppState) -> None:
    """Copy appropriate AmpResult script based on particle count."""
    import json
    
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        print("[linrels --combine] Warning: meta.json not found, skipping AmpResult.m")
        return
    
    meta = json.loads(meta_path.read_text())
    n_in = meta.get("n_in", 0)
    n_out = meta.get("n_out", 0)
    n_particles = n_in + n_out
    
    if n_particles <= 4:
        src_script = repo_root / "mathematica" / "scripts" / "AmpResult4.m"
        if src_script.exists():
            dst_script = run_mat_dir / "AmpResult.m"
            dst_script.write_text(src_script.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"[linrels --combine] Copied AmpResult4.m -> {dst_script}")
        else:
            print(f"[linrels --combine] Warning: {src_script} not found")
    elif n_particles == 5:
        src_script = repo_root / "mathematica" / "scripts" / "AmpResult5.m"
        if src_script.exists():
            dst_script = run_mat_dir / "AmpResult.m"
            dst_script.write_text(src_script.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"[linrels --combine] Copied AmpResult5.m -> {dst_script}")
        else:
            print(f"[linrels --combine] Warning: AmpResult5.m not found for n=5 particles")
    else:
        print(f"[linrels --combine] Warning: No AmpResult template for n={n_particles} particles")
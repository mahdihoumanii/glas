"""
ktexpand command: Collinear expansion of tree-level and one-loop amplitudes.

Usage:
    ktexpand lo [--verbose]  - Expand tree-level amplitudes (runs Expand0l.m)
    ktexpand nlo [--verbose] - Expand one-loop amplitudes (runs Expand1l.m)

Requires Sudakov.m to be run first (auto-runs if Files/Sudakov.m not found).
"""

from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Tuple, Optional

from glaslib.commands.common import AppState
from glaslib.core.logging import LOG_SUBDIR_KTEXPAND, ensure_logs_dir
from glaslib.core.proc import run_streaming


def _parse_args(arg: str) -> Tuple[Optional[str], bool]:
    """Parse ktexpand arguments.
    
    Returns:
        (mode, verbose) where mode is 'lo' or 'nlo' or None
    """
    toks = shlex.split(arg)
    mode: Optional[str] = None
    verbose: bool = False
    
    for t in toks:
        if t in ("lo", "nlo"):
            mode = t
        elif t in ("--verbose", "-v"):
            verbose = True
        elif t in ("--quiet", "-q"):
            verbose = False
    
    return mode, verbose


def _run_sudakov(state: AppState, run_dir: Path, run_mat_dir: Path, logs_dir: Path, 
                 repo_root: Path, env: dict, verbose: bool) -> bool:
    """Run Sudakov.m to generate Sudakov decomposition.
    
    Returns:
        True if successful, False otherwise.
    """
    src_sudakov = repo_root / "mathematica" / "scripts" / "Sudakov.m"
    if not src_sudakov.exists():
        print(f"[ktexpand] Missing script: {src_sudakov}")
        return False

    dst_sudakov = run_mat_dir / "Sudakov.m"
    dst_sudakov.write_text(src_sudakov.read_text(encoding="utf-8"), encoding="utf-8")

    log_sudakov = logs_dir / "Sudakov.log"

    if verbose:
        print("[mma ktexpand] Running Sudakov.m...")
    else:
        print("[ktexpand] Running Sudakov.m ...")

    rc = run_streaming(
        cmd=["wolframscript", "-file", str(dst_sudakov)],
        cwd=run_mat_dir,
        env=env,
        log_path=log_sudakov,
        prefix="mma sudakov",
        verbose=verbose,
    )
    if rc != 0:
        print(f"[ktexpand] Sudakov.m failed (code={rc}). See {log_sudakov}")
        return False

    expected_sudakov = run_mat_dir / "Files" / "Sudakov.m"
    if not expected_sudakov.exists():
        print(f"[ktexpand] Sudakov.m completed but Files/Sudakov.m not created. See {log_sudakov}")
        return False

    if verbose:
        print(f"[mma sudakov] OK -> Files/Sudakov.m")
    else:
        print(f"[ktexpand] Sudakov.m OK -> Files/Sudakov.m")
    
    return True


def run(state: AppState, arg: str) -> None:
    """
    Run the ktexpand command.
    
    Usage:
        ktexpand lo [--verbose]  - Expand tree-level amplitudes
        ktexpand nlo [--verbose] - Expand one-loop amplitudes
    """
    mode, verbose = _parse_args(arg)
    verbose = verbose or state.verbose

    if mode is None:
        print("[ktexpand] Usage: ktexpand {lo|nlo} [--verbose]")
        return

    if not state.ensure_run():
        return

    run_dir = state.ctx.run_dir
    if not run_dir:
        print("[ktexpand] Error: no run attached.")
        return

    repo_root = Path(__file__).resolve().parents[2]
    run_mat_dir = run_dir / "Mathematica"
    run_mat_dir.mkdir(parents=True, exist_ok=True)
    (run_mat_dir / "Files").mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()

    # Create logs directory
    logs_dir = ensure_logs_dir(run_dir, LOG_SUBDIR_KTEXPAND)

    # Check if Sudakov.m has been run (Files/Sudakov.m exists)
    sudakov_output = run_mat_dir / "Files" / "Sudakov.m"
    if not sudakov_output.exists():
        print("[ktexpand] Files/Sudakov.m not found, running Sudakov.m first...")
        if not _run_sudakov(state, run_dir, run_mat_dir, logs_dir, repo_root, env, verbose):
            return

    # Determine script to run based on mode
    if mode == "lo":
        script_name = "Expand0l.m"
        log_name = "Expand0l.log"
        output_file = "Files/Expansion0l.m"
    else:  # nlo
        script_name = "Expand1l.m"
        log_name = "Expand1l.log"
        output_file = "Files/Expansion1l.m"

    src_script = repo_root / "mathematica" / "scripts" / script_name
    if not src_script.exists():
        print(f"[ktexpand] Missing script: {src_script}")
        return

    dst_script = run_mat_dir / script_name
    dst_script.write_text(src_script.read_text(encoding="utf-8"), encoding="utf-8")

    log_path = logs_dir / log_name

    if verbose:
        print(f"[mma ktexpand {mode}] Running {script_name}...")
    else:
        print(f"[ktexpand {mode}] Running {script_name} ...")

    rc = run_streaming(
        cmd=["wolframscript", "-file", str(dst_script)],
        cwd=run_mat_dir,
        env=env,
        log_path=log_path,
        prefix=f"mma ktexpand {mode}",
        verbose=verbose,
    )
    if rc != 0:
        print(f"[ktexpand {mode}] Failed (code={rc}). See {log_path}")
        return

    expected = run_mat_dir / output_file
    if expected.exists():
        if verbose:
            print(f"[mma ktexpand {mode}] OK -> {output_file}")
        else:
            print(f"[ktexpand {mode}] OK -> {output_file} (log: {log_path})")
    else:
        print(f"[ktexpand {mode}] Completed but {output_file} not created. See {log_path}")

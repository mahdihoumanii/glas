from __future__ import annotations

import os
from pathlib import Path

from glaslib.commands.common import AppState, parse_simple_flags
from glaslib.core.logging import LOG_SUBDIR_RATCOMBINE, ensure_logs_dir
from glaslib.core.proc import run_streaming


def run(state: AppState, arg: str) -> None:
    """
    Run the ratcombine command.
    
    Usage:
        ratcombine [--verbose]  - Combine rational functions from master coefficients
    
    This command runs CombineRationalFunctions.m to combine all independent
    rational functions found during the micoef stage into a final simplified form.
    
    Prerequisite: micoef must have been run first to generate MasterCoefficients/mi{i}/ files.
    """
    remainder, verbose = parse_simple_flags(arg)
    remainder = remainder.strip()
    verbose = verbose or state.verbose
    
    if remainder:
        print("Usage: ratcombine [--verbose]")
        return

    if not state.ensure_run():
        return

    run_dir = state.ctx.run_dir
    if not run_dir:
        print("[ratcombine] Error: no run attached.")
        return

    repo_root = Path(__file__).resolve().parents[2]
    run_mat_dir = run_dir / "Mathematica"
    run_mat_dir.mkdir(parents=True, exist_ok=True)
    (run_mat_dir / "Files").mkdir(parents=True, exist_ok=True)
    _copy_amp_results_template(run_dir, repo_root)

    env = os.environ.copy()

    # Create logs directory
    logs_dir = ensure_logs_dir(run_dir, LOG_SUBDIR_RATCOMBINE)

    # Copy script to run directory
    src_script = repo_root / "mathematica" / "scripts" / "CombineRationalFunctions.m"
    if not src_script.exists():
        print(f"[ratcombine] Missing script: {src_script}")
        return

    dst_script = run_mat_dir / "CombineRationalFunctions.m"
    dst_script.write_text(src_script.read_text(encoding="utf-8"), encoding="utf-8")

    log_file = logs_dir / "CombineRationalFunctions.log"

    # Check prerequisites: MasterCoefficients directory should exist with files
    mi_dir = run_mat_dir / "Files" / "MasterCoefficients"
    if not mi_dir.exists() or not any(mi_dir.iterdir()):
        print("[ratcombine] Error: Files/MasterCoefficients/ is empty or missing.")
        print("  Run 'micoef' first to generate master coefficient files.")
        return

    if verbose:
        print("[mma ratcombine] Running CombineRationalFunctions.m...")
    else:
        print("[ratcombine] Running CombineRationalFunctions.m ...")

    rc = run_streaming(
        cmd=["wolframscript", "-file", str(dst_script)],
        cwd=run_mat_dir,
        env=env,
        log_path=log_file,
        prefix="mma ratcombine",
        verbose=verbose,
    )

    if rc != 0:
        print(f"[ratcombine] Failed (code={rc}). See {log_file}")
        return

    # Check output file was created
    output_file = run_mat_dir / "Files" / "MasterCoefficients.m"
    if not output_file.exists():
        print(f"[ratcombine] Completed but Files/MasterCoefficients.m not created.")
        print(f"  See log: {log_file}")
        return

    if not verbose:
        print(f"[ratcombine] OK -> Files/MasterCoefficients.m (log: {log_file})")
    else:
        print("[ratcombine] OK -> Files/MasterCoefficients.m")


def _copy_amp_results_template(run_dir: Path, repo_root: Path) -> None:
    """Copy AmpResultN template to runs/process/mathematica/AmpResultsN.m based on meta.json."""
    import json

    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        print("[ratcombine] Warning: meta.json not found, skipping AmpResultsN.m copy.")
        return

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    n_in = int(meta.get("n_in", 0) or 0)
    n_out = int(meta.get("n_out", 0) or 0)
    n_particles = n_in + n_out
    if n_particles <= 0:
        print("[ratcombine] Warning: Particle count missing in meta.json, skipping AmpResultsN.m copy.")
        return

    src_script = repo_root / "mathematica" / "scripts" / f"AmpResult{n_particles}.m"
    if not src_script.exists():
        print(f"[ratcombine] Warning: {src_script} not found for n={n_particles} particles.")
        return

    dst_dir = run_dir / "mathematica"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_script = dst_dir / f"AmpResults{n_particles}.m"
    dst_script.write_text(src_script.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[ratcombine] Copied AmpResult{n_particles}.m -> {dst_script}")

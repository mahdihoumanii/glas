from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from glaslib.commands.common import AppState, parse_simple_flags, update_meta
from glaslib.core.logging import LOG_SUBDIR_EXTRACT, LOG_SUBDIR_IBP, LOG_SUBDIR_TOPOFORMAT, ensure_logs_dir
from glaslib.core.parallel import run_jobs
from glaslib.core.proc import get_project_python, run_streaming
from glaslib.topoformat import prepare_topoformat_project


def _parse_extract_args(arg: str) -> tuple[str, bool, bool]:
    toks = shlex.split(arg)
    verbose = False
    delete = False
    target_parts = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in ("--verbose", "-v"):
            verbose = True
            i += 1
            continue
        if t == "--delete":
            delete = True
            i += 1
            continue
        if t.startswith("-"):
            raise ValueError(f"Unknown flag: {t}")
        target_parts.append(t)
        i += 1
    return " ".join(target_parts).strip().lower(), verbose, delete


def run(state: AppState, arg: str) -> None:
    try:
        target, verbose, delete = _parse_extract_args(arg)
    except ValueError as exc:
        print(f"Usage: extract topologies [--delete] [--verbose] ({exc})")
        return

    verbose = verbose or state.verbose

    if not target:
        print("Usage: extract topologies [--delete] [--verbose]")
        return
    if target != "topologies":
        print("Usage: extract topologies [--delete] [--verbose]")
        return
    if not state.ensure_run():
        return

    run_dir = state.ctx.run_dir
    if not run_dir:
        print("Error: no run attached.")
        return

    repo_root = Path(__file__).resolve().parents[2]
    stage1_src = repo_root / "mathematica" / "scripts" / "extract_topologies_stage1.m"
    stage2_src = repo_root / "mathematica" / "scripts" / "extract_topologies_stage2.m"
    if not stage1_src.exists() or not stage2_src.exists():
        print("Error: missing stage scripts in mathematica/scripts.")
        return

    run_mat_dir = run_dir / "Mathematica"
    run_mat_dir.mkdir(parents=True, exist_ok=True)
    stage1_dst = run_mat_dir / "extract_topologies_stage1.m"
    stage2_dst = run_mat_dir / "extract_topologies_stage2.m"
    stage1_dst.write_text(stage1_src.read_text(encoding="utf-8"), encoding="utf-8")
    stage2_dst.write_text(stage2_src.read_text(encoding="utf-8"), encoding="utf-8")
    extend_src = repo_root / "extend.py"
    if not extend_src.exists():
        print(f"Error: missing extend.py at {extend_src}")
        return
    extend_dst = run_mat_dir / "extend.py"
    extend_dst.write_text(extend_src.read_text(encoding="utf-8"), encoding="utf-8")

    env = os.environ.copy()

    # Use project venv python
    python_exe = str(get_project_python())
    env["GLAS_PYTHON"] = python_exe

    sympy_check = subprocess.run(
        [python_exe, "-c", "import sympy"],
        cwd=str(run_mat_dir),
        capture_output=True,
        text=True,
    )
    if sympy_check.returncode != 0:
        print("[extract] Error: selected python cannot import sympy (required by extend.py).")
        print(f"  python: {python_exe}")
        print("  Ensure GLAS runs with the Python environment that has sympy.")
        return

    # Create logs directory using centralized constants
    logs_dir = ensure_logs_dir(run_dir, LOG_SUBDIR_EXTRACT)

    stage1_log = logs_dir / "stage1.log"
    extend_log = logs_dir / "extend.log"
    stage2_log = logs_dir / "stage2.log"

    # Stage 1: Extract topologies
    if verbose:
        print("[mma stage1] Running extract_topologies_stage1.m...")
    else:
        print("[extract] Running stage1...")

    rc1 = run_streaming(
        cmd=["wolframscript", "-file", str(stage1_dst)],
        cwd=run_mat_dir,
        env=env,
        log_path=stage1_log,
        prefix="mma stage1",
        verbose=verbose,
    )
    if rc1 != 0:
        print(f"[extract] Stage1 failed (code={rc1}). See {stage1_log}")
        return

    if not verbose:
        print(f"[extract] Stage1 OK (log: {stage1_log})")

    # Stage 2: Extend topologies with Python
    if verbose:
        print("[py extend] Running extend.py...")
    else:
        print("[extract] Running extend.py...")

    rc_ext = run_streaming(
        cmd=[python_exe, str(extend_dst)],
        cwd=run_mat_dir,
        env=env,
        log_path=extend_log,
        prefix="py extend",
        verbose=verbose,
    )
    if rc_ext != 0:
        print(f"[extract] extend.py failed (code={rc_ext}). See {extend_log}")
        return

    if not verbose:
        print(f"[extract] extend.py OK (log: {extend_log})")

    # Stage 2b: Topology mapping with Mathematica
    if verbose:
        print("[mma stage2] Running extract_topologies_stage2.m...")
    else:
        print("[extract] Running stage2...")

    rc2 = run_streaming(
        cmd=["wolframscript", "-file", str(stage2_dst)],
        cwd=run_mat_dir,
        env=env,
        log_path=stage2_log,
        prefix="mma stage2",
        verbose=verbose,
    )
    if rc2 != 0:
        print(f"[extract] Stage2 failed (code={rc2}). See {stage2_log}")
        return

    expected = [
        run_mat_dir / "Files" / "integrals.m",
        run_mat_dir.parent / "form" / "Files" / "intrule.h",
    ]
    missing = [p for p in expected if not p.exists()]
    if missing:
        print("[extract] Completed but outputs are missing:")
        for p in missing:
            print(f"  missing: {p}")
        print(f"  Check logs in: {logs_dir}")
        return

    if not verbose:
        print(f"[extract] Stage2 OK (log: {stage2_log})")

    print("[extract] OK -> Files/integrals.m, ../form/Files/intrule.h")

    # Capture ntop (number of topologies) from Mathematica output
    len_topos_path = run_mat_dir / "Files" / "lenTopos.txt"
    if len_topos_path.exists():
        try:
            ntop_val = int(len_topos_path.read_text(encoding="utf-8").strip())
            update_meta(run_dir, {"ntop": ntop_val})
            if isinstance(state.ctx.meta, dict):
                state.ctx.meta["ntop"] = ntop_val
            print(f"[extract] Recorded ntop = {ntop_val} in meta.json")
        except Exception as exc:
            print(f"[extract] Warning: could not parse lenTopos.txt ({exc})")
    else:
        print("[extract] Warning: lenTopos.txt not found; ntop not recorded. Run extract_topologies_stage2.m output check.")

    print("[extract] Stage 3: Topology formatting with FORM (ToTopos)...")
    _run_topos_extraction(state, run_dir, repo_root, verbose=verbose, delete_m0m1=delete)


def ibp(state: AppState, arg: str) -> None:
    # Parse --verbose flag
    remainder, verbose = parse_simple_flags(arg)
    remainder = remainder.strip()

    # Also check state.verbose
    verbose = verbose or state.verbose

    if remainder:
        print("Usage: ibp [--verbose]")
        return
    if not state.ensure_run():
        return

    run_dir = state.ctx.run_dir
    if not run_dir:
        print("Error: no run attached.")
        return

    repo_root = Path(__file__).resolve().parents[2]
    mandibp_src = repo_root / "mathematica" / "scripts" / "mandIBP.m"
    ibp_src = repo_root / "mathematica" / "scripts" / "IBP.m"
    symrel_src = repo_root / "mathematica" / "scripts" / "SymmetryRelations.m"
    if not mandibp_src.exists() or not ibp_src.exists() or not symrel_src.exists():
        print("Error: missing IBP scripts in mathematica/scripts.")
        return

    run_mat_dir = run_dir / "Mathematica"
    run_mat_dir.mkdir(parents=True, exist_ok=True)
    mandibp_dst = run_mat_dir / "mandIBP.m"
    ibp_dst = run_mat_dir / "IBP.m"
    symrel_dst = run_mat_dir / "SymmetryRelations.m"
    mandibp_dst.write_text(mandibp_src.read_text(encoding="utf-8"), encoding="utf-8")
    ibp_dst.write_text(ibp_src.read_text(encoding="utf-8"), encoding="utf-8")
    symrel_dst.write_text(symrel_src.read_text(encoding="utf-8"), encoding="utf-8")

    env = os.environ.copy()

    # Create logs directory for ibp using centralized constants
    logs_dir = ensure_logs_dir(run_dir, LOG_SUBDIR_IBP)

    mandibp_log = logs_dir / "mandIBP.log"
    ibp_log_file = logs_dir / "IBP.log"
    symrel_log = logs_dir / "SymmetryRelations.log"

    # Stage 1: mandIBP
    if verbose:
        print("[mma mandIBP] Running mandIBP.m...")
    else:
        print("[ibp] Running mandIBP.m...")

    rc1 = run_streaming(
        cmd=["wolframscript", "-file", str(mandibp_dst)],
        cwd=run_mat_dir,
        env=env,
        log_path=mandibp_log,
        prefix="mma mandIBP",
        verbose=verbose,
    )
    if rc1 != 0:
        print(f"[ibp] mandIBP.m failed (code={rc1}). See {mandibp_log}")
        return

    mands_file = run_mat_dir / "Files" / "mands.m"
    if not mands_file.exists():
        print(f"[ibp] mandIBP.m completed but Files/mands.m not created.")
        print(f"  See log: {mandibp_log}")
        return

    if not verbose:
        print(f"[ibp] mandIBP.m OK -> Files/mands.m (log: {mandibp_log})")

    # Stage 2: IBP.m
    if verbose:
        print("[mma IBP] Running IBP.m...")
    else:
        print("[ibp] Running IBP.m...")

    rc2 = run_streaming(
        cmd=["wolframscript", "-file", str(ibp_dst)],
        cwd=run_mat_dir,
        env=env,
        log_path=ibp_log_file,
        prefix="mma IBP",
        verbose=verbose,
    )
    if rc2 != 0:
        print(f"[ibp] IBP.m failed (code={rc2}). See {ibp_log_file}")
        return

    ibp_dir = run_mat_dir / "Files" / "IBP"
    if not ibp_dir.exists() or not any(ibp_dir.iterdir()):
        print(f"[ibp] IBP.m completed but Files/IBP/ is empty or missing.")
        print(f"  See log: {ibp_log_file}")
        return

    if not verbose:
        print(f"[ibp] IBP.m OK -> Files/IBP/ ({len(list(ibp_dir.glob('*.m')))} topology files) (log: {ibp_log_file})")

    # Stage 3: SymmetryRelations.m
    if verbose:
        print("[mma SymRel] Running SymmetryRelations.m...")
    else:
        print("[ibp] Running SymmetryRelations.m...")

    rc3 = run_streaming(
        cmd=["wolframscript", "-file", str(symrel_dst)],
        cwd=run_mat_dir,
        env=env,
        log_path=symrel_log,
        prefix="mma SymRel",
        verbose=verbose,
    )
    if rc3 != 0:
        print(f"[ibp] SymmetryRelations.m failed (code={rc3}). See {symrel_log}")
        return

    symrel_file = run_mat_dir / "Files" / "SymmetryRelations.m"
    if not symrel_file.exists():
        print(f"[ibp] SymmetryRelations.m completed but Files/SymmetryRelations.m not created.")
        print(f"  See log: {symrel_log}")
        return

    if not verbose:
        print(f"[ibp] SymmetryRelations.m OK -> Files/SymmetryRelations.m (log: {symrel_log})")

    # Capture nmis (number of master integrals) from SymmetryRelations.m output
    len_masters_path = run_mat_dir / "Files" / "lenMasters.txt"
    if len_masters_path.exists():
        try:
            nmis_val = int(len_masters_path.read_text(encoding="utf-8").strip())
            update_meta(run_dir, {"nmis": nmis_val})
            if isinstance(state.ctx.meta, dict):
                state.ctx.meta["nmis"] = nmis_val
            print(f"[ibp] Recorded nmis = {nmis_val} in meta.json")
        except Exception as exc:
            print(f"[ibp] Warning: could not parse lenMasters.txt ({exc})")
    else:
        print("[ibp] Warning: lenMasters.txt not found; nmis not recorded. Check SymmetryRelations.m output.")

    # Verify MastersToSym.h was created
    masters_sym_path = run_dir / "form" / "Files" / "MastersToSym.h"
    if not masters_sym_path.exists():
        print(f"[ibp] Warning: MastersToSym.h not found in ../form/Files/")
    else:
        print("[ibp] Also generated ../form/Files/MastersToSym.h (master integral substitution rules)")


def _run_topos_extraction(
    state: AppState,
    run_dir: Path,
    repo_root: Path,
    verbose: bool = False,
    delete_m0m1: bool = False,
) -> None:
    """
    Stage 3: Run ToTopos FORM driver in parallel to format topology integrals.
    
    Prompts user for number of parallel jobs (1 = no parallelism, N > 1 = N jobs).
    Generates ToTopos_J{k}of{N}.frm drivers and executes them in parallel.
    """
    # Read n0l from meta.json to determine max parallelism
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        print("[extract] Error: no meta.json found in run directory.")
        return
    
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        n0l = int(meta.get("n0l", 0))
        if n0l <= 0:
            print("[extract] Error: n0l is 0 or missing from meta.json.")
            return
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[extract] Error reading meta.json: {e}")
        return
    
    # Validate that required files exist
    try:
        config_info = prepare_topoformat_project(run_dir, jobs=1)
    except (FileNotFoundError, ValueError) as e:
        print(f"[extract] ToTopos preparation failed: {e}")
        return

    print(f"[extract] Topology extraction is ready to run with up to {n0l} parallel job(s).")
    print(f"[extract] Enter number of parallel jobs: 1 = serial, {n0l} = maximum parallelism")
    
    jobs_requested = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            jobs_input = input(f"[extract] Jobs (1-{n0l}): ").strip()
            if not jobs_input:
                print("[extract] Cancelled.")
                return
            jobs_requested = int(jobs_input)
            if jobs_requested < 1 or jobs_requested > n0l:
                print(f"[extract] Invalid: must be 1-{n0l}. Try again.")
                continue
            break
        except ValueError:
            print(f"[extract] Invalid: must be an integer 1-{n0l}. Try again.")
            continue
    
    if jobs_requested is None or jobs_requested < 1 or jobs_requested > n0l:
        print("[extract] Cancelled: invalid input.")
        return

    print(f"[extract] Running ToTopos with {jobs_requested} parallel job(s)...")

    config_info = prepare_topoformat_project(run_dir, jobs=jobs_requested)
    form_dir = config_info["form_dir"]
    drivers = config_info["drivers"]
    jobs_effective = config_info["jobs_effective"]

    form_exe = shutil.which("form")
    if not form_exe:
        print("[extract] Error: FORM executable not found on PATH.")
        return

    jobs_list = [
        (f"ToTopos_J{k}of{jobs_effective}", form_dir, drivers[k])
        for k in sorted(drivers.keys())
    ]

    if not run_jobs(form_exe, jobs_list, jobs_effective, verbose=verbose, run_dir=run_dir, log_subdir=LOG_SUBDIR_TOPOFORMAT):
        print(f"[extract] ToTopos failed on one or more jobs.")
        print(f"  Check logs in: {run_dir / 'logs' / LOG_SUBDIR_TOPOFORMAT}")
        return

    m0m1top_form = form_dir / "Files" / "M0M1top"
    m0m1top_math = run_dir / "Mathematica" / "Files" / "M0M1top"

    # Check for output files with better diagnostics
    if not m0m1top_form.exists():
        print(f"[extract] ToTopos completed but output directory not found: {m0m1top_form}")
        return
    
    h_files = list(m0m1top_form.glob("*.h"))
    if not h_files:
        print(f"[extract] ToTopos completed but no .h files found in {m0m1top_form}")
        print(f"  Directory contents: {list(m0m1top_form.iterdir())}")
        return

    print(f"[extract] ToTopos OK -> Files/M0M1top/ ({len(h_files)} .h files)")
    if m0m1top_math.exists():
        m_files = list(m0m1top_math.glob("*.m"))
        if m_files:
            print(f"[extract] Also generated Mathematica files -> ../Mathematica/Files/M0M1top/ ({len(m_files)} .m files)")
    if delete_m0m1:
        m0m1_form = form_dir / "Files" / "M0M1"
        m0m1_math = run_dir / "Mathematica" / "Files" / "M0M1"
        if m0m1_form.exists():
            shutil.rmtree(m0m1_form)
            print(f"[extract] Deleted {m0m1_form}")
        if m0m1_math.exists():
            shutil.rmtree(m0m1_math)
            print(f"[extract] Deleted {m0m1_math}")
    print("[extract] Topology extraction complete!")

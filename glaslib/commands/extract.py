from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from glaslib.commands.common import AppState, update_meta
from glaslib.core.parallel import run_jobs
from glaslib.topoformat import prepare_topoformat_project


def run(state: AppState, arg: str) -> None:
    target = arg.strip().lower()
    if not target:
        print("Usage: extract topologies")
        return
    if target != "topologies":
        print("Usage: extract topologies")
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

    cwd = Path.cwd()
    repo_venv_python = repo_root / ".venv" / "bin" / "python"
    repo_venv_python3 = repo_root / ".venv" / "bin" / "python3"
    candidates = [
        str(repo_venv_python),
        str(repo_venv_python3),
        env.get("GLAS_PYTHON", ""),
        sys.executable,
        str(cwd / ".venv" / "bin" / "python"),
        str(cwd / ".venv" / "bin" / "python3"),
        str(run_dir / ".venv" / "bin" / "python"),
        str(run_dir / ".venv" / "bin" / "python3"),
        str(run_mat_dir / ".venv" / "bin" / "python"),
        str(run_mat_dir / ".venv" / "bin" / "python3"),
    ]
    if repo_venv_python.exists():
        python_exe = str(repo_venv_python)
    elif repo_venv_python3.exists():
        python_exe = str(repo_venv_python3)
    else:
        python_exe = next((p for p in candidates if p and Path(p).exists()), "python3")
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
        print("  Install it with: python3 -m pip install sympy")
        print("  Or set GLAS_PYTHON to your venv python (e.g. /path/to/.venv/bin/python).")
        print(f"  repo_root: {repo_root}")
        print(f"  repo .venv python exists: {repo_venv_python.exists()}")
        print(f"  repo .venv python3 exists: {repo_venv_python3.exists()}")
        print("  Checked:")
        for p in candidates:
            if p:
                print(f"    {p}")
        return

    stage1_log = run_mat_dir / "extract_topologies_stage1.stdout.log"
    stage1_err = run_mat_dir / "extract_topologies_stage1.stderr.log"
    stage2_log = run_mat_dir / "extract_topologies_stage2.stdout.log"
    stage2_err = run_mat_dir / "extract_topologies_stage2.stderr.log"
    extend_out = run_mat_dir / "extract_topologies_extend.stdout.log"
    extend_err = run_mat_dir / "extract_topologies_extend.stderr.log"

    res1 = subprocess.run(
        ["wolframscript", "-file", str(stage1_dst)],
        cwd=str(run_mat_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    stage1_log.write_text(res1.stdout or "", encoding="utf-8")
    stage1_err.write_text(res1.stderr or "", encoding="utf-8")
    if res1.returncode != 0:
        print(f"[extract] Stage1 failed (code={res1.returncode}).")
        print(f"  stdout: {stage1_log}")
        print(f"  stderr: {stage1_err}")
        return

    ext_res = subprocess.run(
        [python_exe, str(extend_dst)],
        cwd=str(run_mat_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    extend_out.write_text(ext_res.stdout or "", encoding="utf-8")
    extend_err.write_text(ext_res.stderr or "", encoding="utf-8")
    if ext_res.returncode != 0:
        print(f"[extract] extend.py failed (code={ext_res.returncode}).")
        print(f"  stdout: {extend_out}")
        print(f"  stderr: {extend_err}")
        return

    res2 = subprocess.run(
        ["wolframscript", "-file", str(stage2_dst)],
        cwd=str(run_mat_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    stage2_log.write_text(res2.stdout or "", encoding="utf-8")
    stage2_err.write_text(res2.stderr or "", encoding="utf-8")
    if res2.returncode != 0:
        print(f"[extract] Stage2 failed (code={res2.returncode}).")
        print(f"  stdout: {stage2_log}")
        print(f"  stderr: {stage2_err}")
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
        print(f"  stage1 stdout: {stage1_log}")
        print(f"  stage1 stderr: {stage1_err}")
        print(f"  extend stdout: {extend_out}")
        print(f"  extend stderr: {extend_err}")
        print(f"  stage2 stdout: {stage2_log}")
        print(f"  stage2 stderr: {stage2_err}")
        return

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
    _run_topos_extraction(state, run_dir, repo_root)


def ibp(state: AppState, arg: str) -> None:
    if arg.strip():
        print("Usage: ibp")
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

    mandibp_log = run_mat_dir / "mandIBP.stdout.log"
    mandibp_err = run_mat_dir / "mandIBP.stderr.log"
    ibp_log = run_mat_dir / "IBP.stdout.log"
    ibp_err = run_mat_dir / "IBP.stderr.log"

    print("[ibp] Running mandIBP.m...")
    res1 = subprocess.run(
        ["wolframscript", "-file", str(mandibp_dst)],
        cwd=str(run_mat_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    mandibp_log.write_text(res1.stdout or "", encoding="utf-8")
    mandibp_err.write_text(res1.stderr or "", encoding="utf-8")
    if res1.returncode != 0:
        print(f"[ibp] mandIBP.m failed (code={res1.returncode}).")
        print(f"  stdout: {mandibp_log}")
        print(f"  stderr: {mandibp_err}")
        return

    mands_file = run_mat_dir / "Files" / "mands.m"
    if not mands_file.exists():
        print(f"[ibp] mandIBP.m completed but Files/mands.m not created.")
        print(f"  stdout: {mandibp_log}")
        print(f"  stderr: {mandibp_err}")
        return

    print("[ibp] mandIBP.m OK -> Files/mands.m")
    print("[ibp] Running IBP.m...")
    res2 = subprocess.run(
        ["wolframscript", "-file", str(ibp_dst)],
        cwd=str(run_mat_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    ibp_log.write_text(res2.stdout or "", encoding="utf-8")
    ibp_err.write_text(res2.stderr or "", encoding="utf-8")
    if res2.returncode != 0:
        print(f"[ibp] IBP.m failed (code={res2.returncode}).")
        print(f"  stdout: {ibp_log}")
        print(f"  stderr: {ibp_err}")
        return

    ibp_dir = run_mat_dir / "Files" / "IBP"
    if not ibp_dir.exists() or not any(ibp_dir.iterdir()):
        print(f"[ibp] IBP.m completed but Files/IBP/ is empty or missing.")
        print(f"  stdout: {ibp_log}")
        print(f"  stderr: {ibp_err}")
        return

    print(f"[ibp] OK -> Files/IBP/ ({len(list(ibp_dir.glob('*.m')))} topology files)")

    print("[ibp] Running SymmetryRelations.m...")
    symrel_log = run_mat_dir / "SymmetryRelations.stdout.log"
    symrel_err = run_mat_dir / "SymmetryRelations.stderr.log"
    res3 = subprocess.run(
        ["wolframscript", "-file", str(symrel_dst)],
        cwd=str(run_mat_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    symrel_log.write_text(res3.stdout or "", encoding="utf-8")
    symrel_err.write_text(res3.stderr or "", encoding="utf-8")
    if res3.returncode != 0:
        print(f"[ibp] SymmetryRelations.m failed (code={res3.returncode}).")
        print(f"  stdout: {symrel_log}")
        print(f"  stderr: {symrel_err}")
        return

    symrel_file = run_mat_dir / "Files" / "SymmetryRelations.m"
    if not symrel_file.exists():
        print(f"[ibp] SymmetryRelations.m completed but Files/SymmetryRelations.m not created.")
        print(f"  stdout: {symrel_log}")
        print(f"  stderr: {symrel_err}")
        return

    print(f"[ibp] OK -> Files/SymmetryRelations.m")

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


def _run_topos_extraction(state: AppState, run_dir: Path, repo_root: Path) -> None:
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

    if not run_jobs(form_exe, jobs_list, jobs_effective):
        print(f"[extract] ToTopos failed on one or more jobs.")
        print(f"  Check logs in: {form_dir}")
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
    print("[extract] Topology extraction complete!")

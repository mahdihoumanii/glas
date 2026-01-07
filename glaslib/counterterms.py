from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _resolve_procedures_dir(project_root: Path) -> Path:
    from glaslib.core.paths import procedures_dir

    return procedures_dir()


def _ensure_symlink_or_copy(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    try:
        os.symlink(str(src.resolve()), str(dst.resolve()), target_is_directory=True)
    except Exception:
        shutil.copytree(src, dst)


def _run_form(form_exe: str, cwd: Path, frm_path: Path, stdout_log: Path, stderr_log: Path) -> None:
    res = subprocess.run(
        [form_exe, frm_path.name],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout_log.write_text(res.stdout or "", encoding="utf-8")
    stderr_log.write_text(res.stderr or "", encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(
            f"FORM failed (code={res.returncode}).\n"
            f"stdout: {stdout_log}\n"
            f"stderr: {stderr_log}"
        )


def _read_int(p: Path) -> int:
    s = p.read_text(encoding="utf-8").strip()
    if not s:
        return 0
    return int(s)


def _chunk_range_1based(total: int, jobs: int, job_index: int) -> Tuple[int, int]:
    if total <= 0:
        return 1, 0
    base = total // jobs
    rem = total % jobs
    if job_index <= rem:
        size = base + 1
        start = (job_index - 1) * size + 1
    else:
        size = base
        start = rem * (base + 1) + (job_index - rem - 1) * base + 1
    end = start + size - 1
    if size <= 0:
        return 1, 0
    return start, end


def _probe_single_diagram_gs_power(
    output_dir: Path,
    *,
    diagram_index: int,
    form_exe: str = "form",
) -> int:
    """
    Probe max power of gs in a single 1-loop diagram header Files/Amps/amp1l/d{diagram_index}.h
    Writes to Files/gs_probe.txt and returns that value.
    """
    output_dir = Path(output_dir).resolve()
    form_dir = output_dir / "form"
    files_dir = form_dir / "Files"

    project_root = output_dir.parent
    procs = _resolve_procedures_dir(project_root)
    _ensure_symlink_or_copy(procs, form_dir / "procedures")

    out_txt = files_dir / "gs_probe.txt"
    out_txt.parent.mkdir(parents=True, exist_ok=True)

    frm = form_dir / "probe_gs_single.frm"

    frm.write_text(
        f"""#-
#: IncDir procedures
Off Statistics;

#include declarations.h
.sort

#include Files/Amps/amp1l/d{diagram_index}.h

L F = d{diagram_index};
.sort

#$max = 0;
if ( count(gs,1) > $max ) $max = count_(gs,1);

Print ">> diagram {diagram_index}: Max power of gs is %$", $max;
.sort
#write <Files/gs_probe.txt> "`$max'"

.end
""",
        encoding="utf-8",
    )

    _run_form(
        form_exe=form_exe,
        cwd=form_dir,
        frm_path=frm,
        stdout_log=form_dir / f"probe_gs_d{diagram_index}.stdout.log",
        stderr_log=form_dir / f"probe_gs_d{diagram_index}.stderr.log",
    )

    return _read_int(out_txt)


def detect_gs_power_from_oneloop(output_dir: Path, *, form_exe: str = "form") -> Tuple[int, int]:
    """
    Scan 1-loop diagrams (amp1l/d{i}.h) until we find a non-zero max power of gs.
    Returns: (N, i_found)
    """
    output_dir = Path(output_dir).resolve()
    meta_path = output_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in {output_dir}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    n1l = int(meta.get("n1l") or 0)
    if n1l <= 0:
        raise ValueError("n1l is 0: no 1-loop diagrams recorded in meta.json")

    form_dir = output_dir / "form"
    amp1l_dir = form_dir / "Files" / "Amps" / "amp1l"
    if not amp1l_dir.exists():
        raise FileNotFoundError(
            f"Missing {amp1l_dir}. Run 'evaluate' first to generate amp1l headers."
        )

    for i in range(1, n1l + 1):
        if not (amp1l_dir / f"d{i}.h").exists():
            continue
        N = _probe_single_diagram_gs_power(output_dir, diagram_index=i, form_exe=form_exe)
        if N > 0:
            (form_dir / "Files" / "gs_power_1l_from_diagram.txt").write_text(
                f"{N} (from d{i})\n", encoding="utf-8"
            )
            return N, i

    raise RuntimeError(
        "Could not find a non-zero gs power in any amp1l diagram.\n"
        "Check that your amp1l/*.h files contain gs and are non-zero."
    )


def prepare_mass_ct_project(
    output_dir: Path,
    *,
    form_exe: str = "form",
    jobs: int = 1,
) -> Dict[str, Any]:
    """
    Stage A: generate RAW mass counterterm amplitudes into:
        form/Files/Amps/mct/d<i>.h
      (NO DiracSimplify here)

    Stage B: DiracSimplify mct (handled by dirac.py) writes simplified CTs to:
        form/Files/Amps/mct/d<i>.h

    Returns chunked drivers for Stage A so glas.py can run them in parallel.
    """
    output_dir = Path(output_dir).resolve()
    meta_path = output_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in {output_dir}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    n0l = int(meta.get("n0l") or 0)
    if n0l <= 0:
        raise ValueError("n0l is 0: no tree diagrams recorded in meta.json")

    form_dir = output_dir / "form"
    files_dir = form_dir / "Files"

    tree_main = meta.get("tree_main") or meta.get("tag", "") + "0l"
    tree_file = files_dir / tree_main
    if not tree_file.exists():
        raise FileNotFoundError(
            f"Missing tree diagram file: {tree_file}\n"
            f"Run: glas> formprep   (it copies diagrams into form/Files/)"
        )

    N, i_found = detect_gs_power_from_oneloop(output_dir, form_exe=form_exe)

    project_root = output_dir.parent
    procs = _resolve_procedures_dir(project_root)
    _ensure_symlink_or_copy(procs, form_dir / "procedures")

    mct_dir = files_dir / "Amps" / "mct"
    mct_dir.mkdir(parents=True, exist_ok=True)
    (files_dir / "Amps" / "mct").mkdir(parents=True, exist_ok=True)

    mand_define = meta.get("mand_define") or '#define mand "#call mandelstam2x3(p1,p2,p3,p4,p5,0,0,mt,mt,0)"'

    jobs_requested = max(1, int(jobs))
    jobs_effective = max(1, min(jobs_requested, n0l))

    drivers: Dict[int, Path] = {}

    for k in range(1, jobs_effective + 1):
        i0, i1 = _chunk_range_1based(n0l, jobs_effective, k)
        if i0 > i1:
            continue

        frm_path = form_dir / f"mass_ct_J{k}of{jobs_effective}.frm"
        frm_path.write_text(
            f"""#- 
#:IncDir procedures
Off Statistics;

{mand_define}

#include declarations.h
.sort

#do i = {i0}, {i1}

#include Files/{tree_main}
#call MassCT(mt, {N})
`mand'

.sort
L amp = d`i';
.sort
Drop d1,...,d{n0l};

*  output for later DiracSimplify stage:
#write <Files/Amps/mct/d`i'.h> "l d`i' = (%E);\\n" amp
.sort
Drop;

#message mct_raw `i'
#enddo

.end
""",
            encoding="utf-8",
        )
        drivers[k] = frm_path

    (form_dir / "Files" / "gs_power_1l_from_diagram.txt").write_text(
        f"{N} (from d{i_found})\n", encoding="utf-8"
    )

    return {
        "form_dir": form_dir,
        "jobs_requested": jobs_requested,
        "jobs_effective": jobs_effective,
        "drivers": drivers,
        "N": N,
        "raw_dir": mct_dir,
    }


def prepare_mass_ct(ctx, form_exe: str, jobs: int) -> Dict[str, Any]:
    if not ctx.run_dir:
        raise RuntimeError("No run attached.")
    return prepare_mass_ct_project(ctx.run_dir, form_exe=form_exe, jobs=jobs)

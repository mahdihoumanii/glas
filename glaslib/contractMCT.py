from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Tuple, List, Optional, Any


def _ensure_symlink_or_copy(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    try:
        os.symlink(str(src.resolve()), str(dst.resolve()), target_is_directory=True)
    except Exception:
        shutil.copytree(src, dst)


def _resolve_procedures_dir(project_root: Path) -> Path:
    from glaslib.core.paths import procedures_dir

    return procedures_dir()


def _count_diagrams(dir_path: Path) -> int:
    n = 0
    while True:
        cand = dir_path / f"d{n+1}.h"
        if cand.exists():
            n += 1
        else:
            break
    return n


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


def _polarization_rules_form(gluon_refs: Dict[str, str]) -> str:
    if not gluon_refs:
        return (
            "b epseps, eps,epsC;\n"
            "    .sort\n"
            "keep brackets;\n\n"
            "repeat id eps(mu1?,p?) *epsC(mu2?,p?) = epseps(mu1 , mu2, p);\n"
            "id epseps(mu1?,mu2?,p?) = -d_(mu1,mu2);\n"
        )

    lines: List[str] = []
    lines.append("b epseps, eps,epsC;")
    lines.append("    .sort")
    lines.append("keep brackets;")
    lines.append("")
    lines.append("repeat id eps(mu1?,p?) *epsC(mu2?,p?) = epseps(mu1 , mu2, p);")

    for gm, ref in gluon_refs.items():
        lines.append(
            f"id epseps(mu1?, mu2?, {gm}) = -d_(mu1, mu2) +"
            f"(({gm}(mu1)*{ref}(mu2) + {gm}(mu2)*{ref}(mu1))*den({gm}.{ref}));"
        )
        lines.append("`mand'")
        lines.append("    .sort")
        lines.append("#call RationalFunction")
        lines.append("")

    return "\n".join(lines) + "\n"


def prepare_contractMCT_project(
    output_dir: Path,
    *,
    gluon_refs: Optional[Dict[str, str]] = None,
    jobs: int = 1,
) -> Dict[str, Any]:
    """
    Chunked drivers:
      form/contractMCT_JkofN.frm

    Outer loop chunked over i=1..nct
    Each job runs all j=1..ntree
    """
    output_dir = Path(output_dir).resolve()
    meta_path = output_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in {output_dir}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    form_dir = output_dir / "form"
    files_dir = form_dir / "Files"

    mct_dir = files_dir / "Amps" / "mct"
    tree_dir = files_dir / "Amps" / "amp0l"

    if not mct_dir.exists():
        raise FileNotFoundError(
            f"Missing simplified CT amplitudes folder: {mct_dir}\n"
            f"Run: evaluate mct --dirac (or evaluate mct then setrefs + --dirac)."
        )
    if not tree_dir.exists():
        raise FileNotFoundError(
            f"Missing tree amplitudes folder: {tree_dir}\n"
            f"Run: glas> evaluate first."
        )

    nct = _count_diagrams(mct_dir)
    ntree = _count_diagrams(tree_dir)
    n0l = int(meta.get("n0l") or 0)
    if nct <= 0:
        raise RuntimeError(f"No CT diagrams found in {mct_dir}")
    if ntree <= 0:
        raise RuntimeError(f"No tree diagrams found in {tree_dir}")

    project_root = output_dir.parent
    procs = _resolve_procedures_dir(project_root)
    _ensure_symlink_or_copy(procs, form_dir / "procedures")

    math_out = output_dir / "Mathematica" / "Files" / "Vm"
    math_out.mkdir(parents=True, exist_ok=True)

    mand_define = meta.get("mand_define") or '#define mand "#call mandelstam2x3(p1,p2,p3,p4,p5,0,0,mt,mt,0)"'

    gluon_refs = gluon_refs or {}
    pol_block = _polarization_rules_form(gluon_refs)

    jobs_requested = max(1, int(jobs))
    jobs_effective = max(1, min(jobs_requested, nct, n0l or nct))

    drivers: Dict[int, Path] = {}

    for k in range(1, jobs_effective + 1):
        i0, i1 = _chunk_range_1based(nct, jobs_effective, k)
        if i0 > i1:
            continue

        frm_path = form_dir / f"contractMCT_J{k}of{jobs_effective}.frm"
        frm_path.write_text(
            f"""#- 
#: IncDir procedures
Off Statistics;

#include declarations.h

{mand_define}

#do i = {i0}, {i1}
#do j = 1, {ntree}
    .sort 
#include Files/Amps/mct/d`i'.h
    .sort 
l amp = d`i'; 
    .sort 
Drop d`i'; 
    .sort
#include Files/Amps/amp0l/d`j'.h
Local ampC = -2* dC`j';
    .sort 

Mul ampC; 
    .sort 

Drop d`j',dC`j', ampC;
    .sort 

#call color

{pol_block}

repeat id D = 4-2*ep; 
#call RationalFunction
#call PolyRat

#call PolarizationSums(5)
id D = 4-2 *ep;
`mand'
    .sort 

id ep^pow? = Pole(ep, pow);

id Pole(ep, 0) = 1;
id Pole(ep, -1) = 1/ep;
    .sort 
id Pole(?a) = 0;
    .sort 

#call Together
Format Mathematica; 
    .sort 
Format Mathematica; 
    .sort 

#write <../Mathematica/Files/Vm/d`i'x`j'.m> "d[`i',`j'] = (%E );" amp

    .sort 
Drop;

#message `i'x`j'
#enddo
#enddo
    .end
""",
            encoding="utf-8",
        )
        drivers[k] = frm_path

    return {
        "form_dir": form_dir,
        "jobs_requested": jobs_requested,
        "jobs_effective": jobs_effective,
        "drivers": drivers,
    }

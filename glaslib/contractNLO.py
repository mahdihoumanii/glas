from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


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


def _split_process(process_str: str) -> Tuple[List[str], List[str]]:
    s = process_str.strip()
    if "->" in s:
        lhs, rhs = s.split("->", 1)
    elif ">" in s:
        lhs, rhs = s.split(">", 1)
    else:
        raise ValueError("Process must contain '>' or '->'")
    lhs_tokens = [t.strip() for t in lhs.strip().split() if t.strip()]
    rhs_tokens = [t.strip() for t in rhs.strip().split() if t.strip()]
    return lhs_tokens, rhs_tokens


def _mass_for_token(tok: str, model_id: Optional[str] = None) -> str:
    from glaslib.core.models import get_mass_for_particle
    return get_mass_for_particle(tok, model_id or "qcd_massive")


def _build_mandelstam_define(process_str: str, model_id: Optional[str] = None) -> str:
    lhs, rhs = _split_process(process_str)
    tokens = [t.lower() for t in (lhs + rhs)]
    n_in = len(lhs)
    n_out = len(rhs)

    momenta = [f"p{i}" for i in range(1, len(tokens) + 1)]
    masses = [_mass_for_token(t, model_id) for t in tokens]
    return f'#define mand "#call mandelstam{n_in}x{n_out}({",".join(momenta)},{",".join(masses)})"'


def _collect_gluon_momenta(process_str: str) -> List[str]:
    lhs, rhs = _split_process(process_str)
    tokens = [t.lower() for t in (lhs + rhs)]
    moms = [f"p{i}" for i in range(1, len(tokens) + 1)]
    return [m for t, m in zip(tokens, moms) if t == "g"]


def _write_gluon_polarization_section(process_str: str, gluon_refs: Dict[str, str]) -> str:
    gluon_moms = _collect_gluon_momenta(process_str)
    if not gluon_moms:
        return ""

    lines: List[str] = []
    lines.append("b epseps, eps,epsC; ")
    lines.append("    .sort ")
    lines.append("keep brackets;")
    lines.append("")
    lines.append("repeat id eps(mu1?,p?) *epsC(mu2?,p?) = epseps(mu1 , mu2, p);")
    lines.append("")

    if len(gluon_moms) == 1:
        lines.append("id epseps(mu1?,mu2?, p?) = -d_(mu1,mu2);")
        lines.append("`mand'")
        lines.append("#call SymToRat")
        lines.append("    .sort ")
        lines.append("")
        return "\n".join(lines)

    for idx, pG in enumerate(gluon_moms):
        if pG not in gluon_refs:
            raise ValueError(f"Missing reference momentum for gluon {pG} (need >=2 gluons).")
        pR = gluon_refs[pG]

        if idx > 0:
            lines.append("b epseps; ")
            lines.append("    .sort ")
            lines.append("keep brackets;")
            lines.append("")

        lines.append(
            f"id epseps(mu1?, mu2?, {pG}) = -d_(mu1, mu2) +({pG}(mu1)*{pR}(mu2) + {pG}(mu2)*{pR}(mu1) )*den({pG}.{pR});"
        )
        lines.append("`mand'")
        lines.append("#call SymToRat")
        lines.append("    .sort ")
        lines.append("")

    return "\n".join(lines)


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


def prepare_contractNLO_project(
    output_dir: Path,
    *,
    gluon_refs: Optional[Dict[str, str]] = None,
    jobs: int = 1,
) -> Dict[str, Any]:
    """
    Writes chunked drivers:
      form/contractNLO_JkofN.frm

    Input required:
      form/Files/Amps/amp0l/*.h and form/Files/Amps/amp1l/*.h exist.

    Output:
      form/Files/M0M1/*.h  and ../Mathematica/Files/M0M1/*.m

    Chunking:
      split outer loop i=1..n0l across jobs
      each job runs all j=1..n1l
    """
    gluon_refs = gluon_refs or {}
    output_dir = Path(output_dir).resolve()

    meta_path = output_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in: {output_dir}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    process_str = meta["process"]
    n0l = int(meta.get("n0l") or 0)
    n1l = int(meta.get("n1l") or 0)

    if n0l <= 0:
        raise ValueError("n0l is 0: no tree amplitudes found.")
    if n1l <= 0:
        raise ValueError("n1l is 0: no 1-loop amplitudes found.")
    model_id = meta.get("model_id")
    mand_define = meta.get("mand_define") or _build_mandelstam_define(process_str, model_id)
    pol_section = _write_gluon_polarization_section(process_str, gluon_refs)

    form_dir = output_dir / "form"
    files_dir = form_dir / "Files"

    amps_src0 = files_dir / "Amps" / "amp0l"
    amps_src1 = files_dir / "Amps" / "amp1l"
    if not amps_src0.exists():
        raise FileNotFoundError(f"Missing simplify output folder: {amps_src0}")
    if not amps_src1.exists():
        raise FileNotFoundError(f"Missing simplify output folder: {amps_src1}")

    (files_dir / "M0M1").mkdir(parents=True, exist_ok=True)
    (output_dir / "Mathematica" / "Files" / "M0M1").mkdir(parents=True, exist_ok=True)

    project_root = output_dir.parent
    procs_global = _resolve_procedures_dir(project_root)
    _ensure_symlink_or_copy(procs_global, form_dir / "procedures")

    if not (form_dir / "procedures" / "declarations.h").exists():
        raise FileNotFoundError(f"declarations.h not found in: {form_dir / 'procedures'}")

    jobs_requested = max(1, int(jobs))
    jobs_effective = max(1, min(jobs_requested, n0l))

    drivers: Dict[int, Path] = {}

    for k in range(1, jobs_effective + 1):
        i0, i1 = _chunk_range_1based(n0l, jobs_effective, k)
        if i0 > i1:
            continue  # should not happen with clamp, but safe

        contract_frm = form_dir / f"contractNLO_J{k}of{jobs_effective}.frm"

        contract_text = f"""#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;

{mand_define}
#include declarations.h
    .sort 
PolyRatFun rat;

#do i = {i0},{i1}
#do j = 1,{n1l}

    .sort 
#include Files/Amps/amp0l/d`i'.h
    .sort
Drop d`i';
#include Files/Amps/amp1l/d`j'.h
    .sort 
Mul dC`i';
    .sort 
Drop dC`i';
#call color

{pol_section}
repeat id D = 4-2*ep; 
#call SymToRat
    .sort
repeat id D = 4-2*ep;

#call PolarizationSums(5)

    .sort 
repeat id D = 4-2*ep; 

#call SymToRat
id p1?.p2? = SPD(p1,p2);
    .sort 
repeat id D = 4-2*ep; 

Mul LoopInt(1);
    .sort 
repeat id LoopInt(?a)*SPD(p1?,p2?) = LoopInt(?a,SPD(p1,p2));
repeat id LoopInt(?a)*FAD(?b) = LoopInt(?a,FAD(?b));
repeat id LoopInt(x1?,x2?,?a) = LoopInt(x1*x2,?a);
format;
.sort 
b LoopInt, gs, i_; 
    .sort 
#write <Files/M0M1/d`i'x`j'.h> "l d`i'x`j' = (%E); \\n" d`j'
    .sort 
id i_=I; 
format mathematica;
b LoopInt, gs, i_; 
    .sort 
#write <../Mathematica/Files/M0M1/d`i'x`j'.m> " d[`i',`j'] = (%E); \\n" d`j'
    .sort 
Drop;
    .sort 
#message `i'x`j'
#enddo
#enddo

.end.
"""
        contract_frm.write_text(contract_text, encoding="utf-8")
        drivers[k] = contract_frm

    return {
        "form_dir": form_dir,
        "jobs_requested": jobs_requested,
        "jobs_effective": jobs_effective,
        "drivers": drivers,
    }

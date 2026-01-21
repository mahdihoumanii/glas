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


def _mass_for_token(tok: str) -> str:
    tok = tok.lower()
    if tok in ("t", "t~", "tbar"):
        return "mt"
    return "0"


def _build_mandelstam_define(process_str: str) -> str:
    lhs, rhs = _split_process(process_str)
    tokens = [t.lower() for t in (lhs + rhs)]
    n_in = len(lhs)
    n_out = len(rhs)
    momenta = [f"p{i}" for i in range(1, len(tokens) + 1)]
    masses = [_mass_for_token(t) for t in tokens]
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


def prepare_contractLO_project(
    output_dir: Path,
    *,
    gluon_refs: Optional[Dict[str, str]] = None,
    jobs: int = 1,
) -> Dict[str, Any]:
    """
    Chunked LO contraction drivers:
      form/contractLO_JkofN.frm

    Assumption:
      Uses Files/Amps/amp0l/d<i>.h containing d<i> and dC<i>.

    Chunking:
      outer i=1..n0l split across jobs, each job runs all j=1..n0l
    """
    gluon_refs = gluon_refs or {}
    output_dir = Path(output_dir).resolve()

    meta_path = output_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in: {output_dir}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    process_str = meta["process"]
    n0l = int(meta.get("n0l") or 0)
    if n0l <= 0:
        raise ValueError("n0l is 0: no tree amplitudes found.")

    mand_define = _build_mandelstam_define(process_str)
    pol_section = _write_gluon_polarization_section(process_str, gluon_refs)

    form_dir = output_dir / "form"
    files_dir = form_dir / "Files"

    amps0 = files_dir / "Amps" / "amp0l"
    if not amps0.exists():
        raise FileNotFoundError(f"Missing {amps0}. Run evaluate first.")

    (files_dir / "M0M0").mkdir(parents=True, exist_ok=True)
    (output_dir / "Mathematica" / "Files" / "M0M0").mkdir(parents=True, exist_ok=True)

    project_root = output_dir.parent
    procs_global = _resolve_procedures_dir(project_root)
    _ensure_symlink_or_copy(procs_global, form_dir / "procedures")

    jobs_requested = max(1, int(jobs))
    jobs_effective = max(1, min(jobs_requested, n0l))

    drivers: Dict[int, Path] = {}

    for k in range(1, jobs_effective + 1):
        i0, i1 = _chunk_range_1based(n0l, jobs_effective, k)
        if i0 > i1:
            continue

        frm = form_dir / f"contractLO_J{k}of{jobs_effective}.frm"

        # NOTE: if your LO body differs, paste it inside the do-loops below.
        frm.write_text(
            f"""#-
#: IncDir procedures
Off Statistics;

{mand_define}
#include declarations.h
    .sort
PolyRatFun rat;

#do i = {i0},{i1}
#do j = 1,{n0l}

    .sort
#include Files/Amps/amp0l/d`i'.h
    .sort
#include Files/Amps/amp0l/d`j'.h

* Example: amp_i * (amp_j)^*
* You likely already have your own exact conventions:
Mul dC`j';
    .sort
#call color

{pol_section}
repeat id D = 4-2*ep;
#call SymToRat
    .sort
repeat id D = 4-2*ep;

#call PolarizationSums(5)

repeat id D = 4-2*ep;

    .sort
#call SymToRat

format;
.sort
#write <Files/M0M0/d`i'x`j'.h> "l d`i'x`j' = (%E);\\n" d`i'
.sort
format mathematica;
.sort
#write <../Mathematica/Files/M0M0/d`i'x`j'.m> "d[`i',`j'] = (%E);\\n" d`i'
.sort
Drop;
#message `i'x`j'

#enddo
#enddo

.end
""",
            encoding="utf-8",
        )
        drivers[k] = frm

    return {
        "form_dir": form_dir,
        "jobs_requested": jobs_requested,
        "jobs_effective": jobs_effective,
        "drivers": drivers,
    }

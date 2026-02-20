from __future__ import annotations

import json
import os
import shutil
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


def _count_diagrams(folder: Path) -> int:
    n = 0
    while (folder / f"d{n + 1}.h").exists():
        n += 1
    return n


def _mass_for_token(tok: str, model_id: Optional[str] = None) -> str:
    from glaslib.core.models import get_mass_for_particle
    return get_mass_for_particle(tok, model_id or "qcd_massive")


def _split_process(process_str: str) -> Tuple[list, list]:
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


def _build_mand_define(process_str: str, model_id: Optional[str] = None) -> str:
    lhs, rhs = _split_process(process_str)
    tokens = [t.lower() for t in (lhs + rhs)]
    n_in = len(lhs)
    n_out = len(rhs)
    momenta = [f"p{i}" for i in range(1, len(tokens) + 1)]
    masses = [_mass_for_token(t, model_id) for t in tokens]
    return f'#define mand "#call mandelstam{n_in}x{n_out}({",".join(momenta)},{",".join(masses)})"'


def _orthogonality_block(gluon_orth: Optional[Dict[str, str]]) -> str:
    if not gluon_orth:
        return ""
    lines = []
    for gluon_mom, ref in gluon_orth.items():
        lines.append(f"id eps({ref},{gluon_mom}) = 0;")
    return "\n".join(lines) + ("\n" if lines else "")


def _write_dirac_driver(
    *,
    dst: Path,
    incdir: Path,
    src_dir: str,
    dst_dir: str,
    total: int,
    i0: int,
    i1: int,
    orth_block: str,
    mand_define: str,
    write_conjugate: bool = False,
) -> None:
    if write_conjugate:
        conjugate_block = "#call Conjugate(amp, ampC)\n    .sort\n"
        write_block = (
            f"#write <Files/Amps/{dst_dir}/d`i'.h> \"l d`i' = (%E);\\n\" amp\n"
            f"#write <Files/Amps/{dst_dir}/d`i'.h> \"l dC`i' = (%E);\\n\" ampC\n"
        )
    else:
        conjugate_block = ""
        write_block = f"#write <Files/Amps/{dst_dir}/d`i'.h> \"l d`i' = (%E);\\n\" amp\n"

    text = f"""#-
#: IncDir {incdir}
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;

{mand_define}

#include declarations.h
.sort
PolyRatFun rat;
.sort

#do i = {i0},{i1}
#include Files/Amps/{src_dir}/d`i'.h
    .sort
L amp = d`i';
    .sort
Drop d1,...,d{total};

#call SymToRat
#call DiracSimplify
{orth_block}#call SymToRat
{conjugate_block}b diracChain,Color,i_,gs,eps,epsC,FAD;
    .sort
{write_block}    .sort
Drop;
#message dirac_{dst_dir} `i'
#enddo

.end
"""
    dst.write_text(text, encoding="utf-8")


def prepare_dirac_projects(
    output_dir: Path,
    *,
    mode: str = "2",
    jobs: int = 1,
    gluon_orth: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Generates chunked DiracSimplify driver files.

    mode:
      "0"   -> simplify tree only (amp0l)
      "1"   -> simplify one-loop only (amp1l)
      "2"   -> simplify both tree and loop
      "mct" -> simplify mass counterterms (mct_raw -> mct)

    Returns dict with per-target driver maps and job counts.
    """
    output_dir = Path(output_dir).resolve()
    meta_path = output_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in: {output_dir}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    n0l = int(meta.get("n0l") or 0)
    n1l = int(meta.get("n1l") or 0)

    form_dir = output_dir / "form"
    files_dir = form_dir / "Files"

    amps0 = files_dir / "Amps" / "amp0l"
    amps1 = files_dir / "Amps" / "amp1l"
    mct_raw = files_dir / "Amps" / "mct_raw"
    mct_out = files_dir / "Amps" / "mct"

    project_root = output_dir.parent
    procs = _resolve_procedures_dir(project_root)
    _ensure_symlink_or_copy(procs, form_dir / "procedures")

    incdir = form_dir / "procedures"
    if not (incdir / "declarations.h").exists():
        raise FileNotFoundError(f"declarations.h not found in: {incdir}")

    mode = str(mode).strip().lower() or "2"
    if mode not in ("0", "1", "2", "mct"):
        raise ValueError("DiracSimplify mode must be one of: 0, 1, 2, mct")

    model_id = meta.get("model_id")
    mand_define = meta.get("mand_define") or _build_mand_define(meta["process"], model_id)

    jobs_requested = max(1, int(jobs))
    orth_block = _orthogonality_block(gluon_orth)

    result: Dict[str, Any] = {
        "form_dir": form_dir,
        "jobs_requested": jobs_requested,
        "target": mode,
    }

    if mode in ("0", "2"):
        if n0l <= 0:
            raise ValueError("n0l is 0: no tree amplitudes recorded. Run evaluate first.")
        if not amps0.exists():
            raise FileNotFoundError(f"Missing tree amplitudes: {amps0}. Run evaluate first.")
        jobs_eff_tree = max(1, min(jobs_requested, n0l or 1))
        tree_drivers: Dict[int, Path] = {}
        for k in range(1, jobs_eff_tree + 1):
            i0, i1 = _chunk_range_1based(n0l, jobs_eff_tree, k)
            if i0 > i1:
                continue
            frm = form_dir / f"dirac_simplify_tree_J{k}of{jobs_eff_tree}.frm"
            _write_dirac_driver(
                dst=frm,
                incdir=incdir,
                src_dir="amp0l",
                dst_dir="amp0l",
                total=n0l,
                i0=i0,
                i1=i1,
                orth_block=orth_block,
                mand_define=mand_define,
                write_conjugate=True,
            )
            tree_drivers[k] = frm
        result["tree"] = {"drivers": tree_drivers, "jobs_effective": jobs_eff_tree}

    if mode in ("1", "2"):
        if n1l <= 0:
            raise ValueError("n1l is 0: no one-loop amplitudes recorded. Run evaluate first.")
        if not amps1.exists():
            raise FileNotFoundError(f"Missing one-loop amplitudes: {amps1}. Run evaluate first.")
        jobs_eff_loop = max(1, min(jobs_requested, n1l or 1))
        loop_drivers: Dict[int, Path] = {}
        for k in range(1, jobs_eff_loop + 1):
            j0, j1 = _chunk_range_1based(n1l, jobs_eff_loop, k)
            if j0 > j1:
                continue
            frm = form_dir / f"dirac_simplify_loop_J{k}of{jobs_eff_loop}.frm"
            _write_dirac_driver(
                dst=frm,
                incdir=incdir,
                src_dir="amp1l",
                dst_dir="amp1l",
                total=n1l,
                i0=j0,
                i1=j1,
                orth_block=orth_block,
                mand_define=mand_define,
            )
            loop_drivers[k] = frm
        result["loop"] = {"drivers": loop_drivers, "jobs_effective": jobs_eff_loop}

    if mode == "mct":
        if not mct_raw.exists():
            raise FileNotFoundError(
                f"Missing RAW CT amplitudes: {mct_raw}\n"
                f"Run: evaluate mct --dirac (or evaluate mct then setrefs + --dirac)."
            )
        nct_raw = _count_diagrams(mct_raw)
        if nct_raw <= 0:
            raise RuntimeError(f"No CT amplitudes found in {mct_raw}")
        mct_out.mkdir(parents=True, exist_ok=True)
        jobs_eff_mct = max(1, min(jobs_requested, nct_raw))
        mct_drivers: Dict[int, Path] = {}
        for k in range(1, jobs_eff_mct + 1):
            c0, c1 = _chunk_range_1based(nct_raw, jobs_eff_mct, k)
            if c0 > c1:
                continue
            frm = form_dir / f"dirac_simplify_mct_J{k}of{jobs_eff_mct}.frm"
            _write_dirac_driver(
                dst=frm,
                incdir=incdir,
                src_dir="mct_raw",
                dst_dir="mct",
                total=nct_raw,
                i0=c0,
                i1=c1,
                orth_block=orth_block,
                mand_define=mand_define,
            )
            mct_drivers[k] = frm
        result["mct"] = {"drivers": mct_drivers, "jobs_effective": jobs_eff_mct}

    return result


def prepare_dirac(ctx, mode: str, jobs: int, gluon_orth: Dict[str, str]):
    if not ctx.run_dir:
        raise RuntimeError("No run attached.")
    return prepare_dirac_projects(ctx.run_dir, mode=mode, jobs=jobs, gluon_orth=gluon_orth)

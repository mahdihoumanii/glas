from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Tuple, Dict, List, Optional


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


def _count_external(process_str: str) -> Tuple[int, int, int]:
    """
    Returns:
      n_ext  : total external legs
      nhext  : number of external massive mt legs (t,t~ aliases)
      ng     : number of gluons
    """
    lhs, rhs = _split_process(process_str)
    toks = [t.lower() for t in (lhs + rhs)]
    n_ext = len(toks)

    massive_aliases = {"t", "t~", "tbar", "top", "topb", "top~", "tb", "t_b"}
    nhext = sum(1 for t in toks if t in massive_aliases)

    ng = sum(1 for t in toks if t == "g")
    return n_ext, nhext, ng


def _read_meta(output_dir: Path) -> Dict:
    meta_path = output_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in {output_dir}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _resolve_procedures_dir(project_root: Path) -> Path:
    from glaslib.core.paths import procedures_dir

    return procedures_dir()


def _ensure_symlink_or_copy(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    try:
        os.symlink(str(src.resolve()), str(dst.resolve()), target_is_directory=True)
    except Exception:
        import shutil
        shutil.copytree(src, dst)


def _count_m0m0_pairs(m0m0_dir: Path) -> Tuple[int, int]:
    """
    Infers max i and max j from Files/M0M0/dixj.h files.
    Assumes square (same range), returns (imax, jmax).
    """
    pat = re.compile(r"^d(\d+)x(\d+)\.h$")
    imax = 0
    jmax = 0
    for f in m0m0_dir.iterdir():
        if not f.is_file():
            continue
        m = pat.match(f.name)
        if not m:
            continue
        i = int(m.group(1))
        j = int(m.group(2))
        imax = max(imax, i)
        jmax = max(jmax, j)
    if imax == 0 or jmax == 0:
        raise FileNotFoundError(f"No M0M0 pair files found in {m0m0_dir} (expected d1x1.h etc.)")
    return imax, jmax


def _mand_define_from_process(process_str: str) -> str:
    n_ext, _, _ = _count_external(process_str)
    if n_ext == 4:
        return '#define mand "#call mandelstam2x2(p1,p2,p3,p4,0,0,mt,mt)"'
    elif n_ext == 5:
        return '#define mand "#call mandelstam2x3(p1,p2,p3,p4,p5,0,0,mt,mt,0)"'
    else:
        # extend later if you need 2->4 etc.
        return '#define mand "#call mandelstam2x3(p1,p2,p3,p4,p5,0,0,mt,mt,0)"'


def _probe_gs_power_from_amp1l(output_dir: Path, form_exe: str = "form") -> Optional[int]:
    """
    Tries to determine max gs power from Files/Amps/amp1l/dk.h by running FORM.
    Returns None if amp1l not available or probe fails.
    """
    form_dir = output_dir / "form"
    files_dir = form_dir / "Files"
    amp1l_dir = files_dir / "Amps" / "amp1l"
    if not amp1l_dir.exists():
        return None

    candidates = sorted(
        amp1l_dir.glob("d*.h"),
        key=lambda p: int(p.stem[1:]) if p.stem[1:].isdigit() else 10**9,
    )
    if not candidates:
        return None

    probe_frm = form_dir / "probe_gs_power.frm"
    out_txt = files_dir / "gs_power_1l.txt"

    for hfile in candidates[:200]:  # safety cap
        probe_frm.write_text(
            f"""#-
#: IncDir procedures
Off Statistics;

#include declarations.h
    .sort

#include Files/Amps/amp1l/{hfile.name}
    .sort

#$max = 0;
if ( count(gs,1) > $max ) $max = count_(gs,1);

    .sort
#write <Files/gs_power_1l.txt> "%$" $max
.end
""",
            encoding="utf-8",
        )

        res = subprocess.run(
            [form_exe, probe_frm.name],
            cwd=str(form_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            continue

        if out_txt.exists():
            s = out_txt.read_text(encoding="utf-8").strip()
            if s.isdigit() and int(s) > 0:
                return int(s)

    return None


def _read_gs_power_1l(output_dir: Path, process_str: str, form_exe: str = "form") -> int:
    """
    Independent gs power determination:
      1) use Files/gs_power_1l.txt if exists
      2) else probe from Files/Amps/amp1l/ using FORM (after DiracSimplify)
      3) else fallback: gs_power_1l = n_external_legs (QCD estimate)
    """
    form_dir = output_dir / "form"
    p = form_dir / "Files" / "gs_power_1l.txt"
    if p.exists():
        s = p.read_text(encoding="utf-8").strip()
        if s.isdigit():
            return int(s)

    probed = _probe_gs_power_from_amp1l(output_dir, form_exe=form_exe)
    if probed is not None:
        return probed

    n_ext, _, _ = _count_external(process_str)
    return n_ext


def _ensure_dirs(output_dir: Path) -> Dict[str, Path]:
    form_dir = output_dir / "form"
    files_dir = form_dir / "Files"
    m0m0_dir = files_dir / "M0M0"

    math_base = output_dir / "Mathematica" / "Files"
    vas_dir = math_base / "Vas"
    vzt_dir = math_base / "Vzt"
    vg_dir = math_base / "Vg"

    vas_dir.mkdir(parents=True, exist_ok=True)
    vzt_dir.mkdir(parents=True, exist_ok=True)
    vg_dir.mkdir(parents=True, exist_ok=True)

    return {
        "form_dir": form_dir,
        "files_dir": files_dir,
        "m0m0_dir": m0m0_dir,
        "vas_dir": vas_dir,
        "vzt_dir": vzt_dir,
        "vg_dir": vg_dir,
    }


def _form_common_tail(out_subdir: str) -> str:
    return f"""
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

#write <../Mathematica/Files/{out_subdir}/d`i'x`j'.m> "d[`i',`j'] = (%E );" d`i'x`j'

    .sort 
Drop;
    .sort 
#message `i'x`j'
"""


def _write_driver(
    form_dir: Path,
    *,
    name: str,
    mand_define: str,
    b_val: int,
    nhext_val: int,
    ng_val: int,
    imax: int,
    jmax: int,
    mul_line: str,
    out_subdir: str,
) -> Path:
    frm_path = form_dir / name
    frm_path.write_text(
        f"""#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;

{mand_define}
#define b "{b_val}"
#define nhext "{nhext_val}"
#define ng "{ng_val}"

#include declarations.h
    .sort 
PolyRatFun rat;

#do i =1, {imax}
#do j =1, {jmax}

#include Files/M0M0/d`i'x`j'.h
    .sort

{mul_line}
    .sort
{_form_common_tail(out_subdir)}
#enddo
#enddo

b nl,nh,ep,gs,Pi;
Print; 
    .end
""",
        encoding="utf-8",
    )
    return frm_path


def prepare_getct_projects(output_dir: Path, *, form_exe: str = "form") -> Dict[str, Path]:
    """
    Creates three FORM drivers:
      - Vas.frm
      - Vzt.frm
      - Vg.frm

    Also ensures form/procedures exists (IncDir procedures).
    """
    output_dir = Path(output_dir).resolve()
    meta = _read_meta(output_dir)
    process_str = meta.get("process")
    if not process_str:
        raise ValueError("meta.json missing 'process' field")

    dirs = _ensure_dirs(output_dir)
    form_dir = dirs["form_dir"]
    files_dir = dirs["files_dir"]
    m0m0_dir = dirs["m0m0_dir"]

    if not m0m0_dir.exists():
        raise FileNotFoundError(
            f"Missing {m0m0_dir}. You need to generate M0M0 first (tree×tree contraction output)."
        )

    # Ensure IncDir procedures works
    project_root = output_dir.parent
    procs = _resolve_procedures_dir(project_root)
    _ensure_symlink_or_copy(procs, form_dir / "procedures")

    imax, jmax = _count_m0m0_pairs(m0m0_dir)

    # b = (gs power of one-loop amplitude) - 1  (independent now)
    gs_power_1l = _read_gs_power_1l(output_dir, process_str, form_exe=form_exe)
    b_val = gs_power_1l - 2
    if b_val < 0:
        b_val = 0

    _, nhext_val, ng_val = _count_external(process_str)
    mand_define = _mand_define_from_process(process_str)

    mul_vas = "Mul (`b'*gs^2*(-33 + 2*nh + 2*nl))/(48*ep*Pi^2) + (`b'*gs^2*nh*Log(Mu^2/mt^2))/(24*Pi^2);"
    mul_vzt = "Mul (-1/3*(gs^2*`nhext')/Pi^2 - (gs^2*`nhext')/(4*ep*Pi^2) - (gs^2*`nhext'*Log(Mu^2/mt^2))/(4*Pi^2));"
    mul_vg  = "Mul -1/24*(gs^2*`ng'*nh)/(ep*Pi^2) - (gs^2*`ng'*nh*Log(Mu^2/mt^2))/(24*Pi^2);"

    p_vas = _write_driver(
        form_dir,
        name="Vas.frm",
        mand_define=mand_define,
        b_val=b_val,
        nhext_val=nhext_val,
        ng_val=ng_val,
        imax=imax,
        jmax=jmax,
        mul_line=mul_vas,
        out_subdir="Vas",
    )
    p_vzt = _write_driver(
        form_dir,
        name="Vzt.frm",
        mand_define=mand_define,
        b_val=b_val,
        nhext_val=nhext_val,
        ng_val=ng_val,
        imax=imax,
        jmax=jmax,
        mul_line=mul_vzt,
        out_subdir="Vzt",
    )
    p_vg = _write_driver(
        form_dir,
        name="Vg.frm",
        mand_define=mand_define,
        b_val=b_val,
        nhext_val=nhext_val,
        ng_val=ng_val,
        imax=imax,
        jmax=jmax,
        mul_line=mul_vg,
        out_subdir="Vg",
    )

    # Always write the constants you wanted to see
    dbg = files_dir / "getct_meta.txt"
    dbg.write_text(
        f"process={process_str}\n"
        f"gs_power_1l={gs_power_1l}\n"
        f"b={b_val}\n"
        f"nhext={nhext_val}\n"
        f"ng={ng_val}\n"
        f"imax={imax}\n"
        f"jmax={jmax}\n",
        encoding="utf-8",
    )

    return {"Vas": p_vas, "Vzt": p_vzt, "Vg": p_vg}


def prepare_getct(ctx, form_exe: str):
    if not ctx.run_dir:
        raise RuntimeError("No run attached.")
    return prepare_getct_projects(ctx.run_dir, form_exe=form_exe)

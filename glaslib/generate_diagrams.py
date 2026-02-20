from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from glaslib.core.models import get_qgraf_model

# -----------------------------
# Physics name → QGRAF symbol
# -----------------------------
PARTICLE_MAP: Dict[str, str] = {
    "q": "q",
    "q~": "qB",
    "qbar": "qB",
    "t": "top",
    "t~": "topB",
    "tbar": "topB",
    "g": "g",
}

_ARROW_RE = re.compile(r"\s*(?:->|>)\s*")
_LOCAL_D_RE = re.compile(r"(?m)^\s*Local\s+d(\d+)\s*=")


@dataclass(frozen=True)
class Leg:
    symbol: str
    momentum: str

    def to_qgraf(self) -> str:
        return f"{self.symbol}[{self.momentum}]"


@dataclass
class QGrafSpec:
    output: str
    style: str
    model: str
    incoming: List[Leg]
    outgoing: List[Leg]
    loops: int
    loop_momentum: str = "lm"
    options: Optional[List[str]] = None

    def to_text(self) -> str:
        inc = ",".join(leg.to_qgraf() for leg in self.incoming)
        out = ",".join(leg.to_qgraf() for leg in self.outgoing)
        opts = ",".join(self.options or [])
        return (
            f" output= '{self.output}' ; \n \n"
            f" style= '{self.style}' ; \n\n"
            f" model= '{self.model}'; \n\n"
            f" in= {inc}; \n\n"
            f" out= {out};\n\n"
            f" loops= {self.loops}; \n\n"
            f" loop_momentum= {self.loop_momentum}; \n\n"
            f" options= {opts};"
        )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_process(process_str: str) -> Tuple[List[str], List[str]]:
    parts = _ARROW_RE.split(process_str.strip())
    if len(parts) != 2:
        raise ValueError('Process must look like: "a b > c d" or "a b -> c d"')

    lhs, rhs = parts
    lhs_toks = [t.strip().lower() for t in lhs.split() if t.strip()]
    rhs_toks = [t.strip().lower() for t in rhs.split() if t.strip()]

    if not lhs_toks or not rhs_toks:
        raise ValueError("Initial and final states must be non-empty")

    for tok in lhs_toks + rhs_toks:
        if tok not in PARTICLE_MAP:
            raise ValueError(f"Unknown particle {tok!r}. Allowed: {sorted(PARTICLE_MAP)}")

    return lhs_toks, rhs_toks


def build_legs(lhs: List[str], rhs: List[str]) -> Tuple[List[Leg], List[Leg]]:
    all_tokens = lhs + rhs
    momenta = [f"p{i}" for i in range(1, len(all_tokens) + 1)]

    def sym(tok: str) -> str:
        return PARTICLE_MAP[tok]

    incoming = [Leg(sym(tok), momenta[i]) for i, tok in enumerate(lhs)]
    outgoing = [Leg(sym(tok), momenta[len(lhs) + j]) for j, tok in enumerate(rhs)]
    return incoming, outgoing


def process_to_tag(lhs: List[str], rhs: List[str]) -> str:
    def one(tok: str) -> str:
        tok = tok.lower()
        if tok == "q":
            return "q"
        if tok in ("q~", "qbar"):
            return "qb"
        if tok == "t":
            return "t"
        if tok in ("t~", "tbar"):
            return "tb"
        if tok == "g":
            return "g"
        if tok == "h":
            return "h"
        raise ValueError(f"Unsupported token in tag: {tok!r}")

    return "".join(one(t) for t in (lhs + rhs))


def _count_diagrams_from_text(text: str) -> int:
    nums = [int(m.group(1)) for m in _LOCAL_D_RE.finditer(text)]
    return len(set(nums))


def _find_main_qgraf_output(workdir: Path, prefix_name: str) -> Path:
    workdir = Path(workdir)
    exact = workdir / prefix_name
    candidates = sorted([p for p in workdir.glob(prefix_name + "*") if p.is_file()])

    if exact.exists() and exact.is_file():
        candidates = [exact] + [p for p in candidates if p != exact]

    for p in candidates:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if _LOCAL_D_RE.search(txt):
            return p

    if not candidates:
        raise FileNotFoundError(f"No QGRAF output files found for prefix '{prefix_name}' in {workdir}")
    return candidates[0]


def _sanitize_out_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("out name cannot be empty")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("out name must match [A-Za-z0-9_-]+ (no spaces)")
    return name


def _model_suffix(model_id: str) -> str:
    """Return the suffix to add to run directory names based on model.
    
    - qcd_massive: no suffix (default)
    - qcd_massless: '_massless'
    - higgs_qcd: '_higgs'
    """
    if model_id == "qcd_massless":
        return "_massless"
    elif model_id == "higgs_qcd":
        return "_higgs"
    return ""


def _next_auto_output_dir(project_root: Path, tag: str, model_id: str = "qcd_massive") -> Path:
    project_root = project_root.resolve()
    suffix = _model_suffix(model_id)
    base_tag = f"{tag}{suffix}"
    existing = []
    for p in project_root.glob(f"{base_tag}_*"):
        if p.is_dir():
            m = re.match(rf"{re.escape(base_tag)}_(\d+)$", p.name)
            if m:
                existing.append(int(m.group(1)))
    n = (max(existing) + 1) if existing else 1
    return project_root / f"{base_tag}_{n:04d}"


def _acquire_lock(lock_path: Path) -> None:
    lock_path = Path(lock_path)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        raise RuntimeError(
            f"QGRAF lock exists: {lock_path}\n"
            f"Another run may be in progress (or a stale lock). Remove it if you're sure."
        )


def _release_lock(lock_path: Path) -> None:
    try:
        Path(lock_path).unlink(missing_ok=True)
    except Exception:
        pass


def _run_qgraf(qgraf_exe: Path, cwd: Path) -> subprocess.CompletedProcess:
    qgraf_exe = Path(qgraf_exe)
    if not qgraf_exe.exists():
        raise FileNotFoundError(f"QGRAF executable not found: {qgraf_exe}")
    if os.name != "nt" and not os.access(qgraf_exe, os.X_OK):
        raise PermissionError(f"{qgraf_exe} is not executable. Run: chmod +x {qgraf_exe}")

    return subprocess.run(
        [str(qgraf_exe)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


# -----------------------------
# Diagram generation
# -----------------------------
def generate_both(
    *,
    process_str: str,
    project_root: Path,
    tools_dir: Path,
    qgraf_exe: Path,
    style_file: Path,
    model_id: str,
    options: Optional[List[str]] = None,
    keep_temp: bool = False,
    out_name: Optional[str] = None,
) -> Dict[str, Any]:
    project_root = Path(project_root).resolve()
    tools_dir = Path(tools_dir).resolve()
    qgraf_exe = Path(qgraf_exe).resolve()
    style_file = Path(style_file).resolve()

    if options is None:
        options = ["onshell", "nosnails"]

    project_root = Path(project_root).resolve()
    runs_root = (project_root / "runs").resolve()
    runs_root.mkdir(parents=True, exist_ok=True)
    lhs, rhs = parse_process(process_str)
    incoming, outgoing = build_legs(lhs, rhs)
    tag = process_to_tag(lhs, rhs)
    n_in = len(lhs)
    n_out = len(rhs)
    shape = f"{n_in}>{n_out}"
    particles = [
        {"token": tok, "momentum": f"p{i+1}", "side": "in" if i < n_in else "out"}
        for i, tok in enumerate(lhs + rhs)
    ]

    if out_name is not None:
        out_name = _sanitize_out_name(out_name)
        output_dir = runs_root / out_name
        if output_dir.exists():
            raise FileExistsError(f"Output folder already exists: {output_dir}")
    else:
        output_dir = _next_auto_output_dir(runs_root, tag, model_id)

    output_dir.mkdir(parents=True, exist_ok=False)

    # Get QGRAF model filename from model_id
    qgraf_model = get_qgraf_model(model_id)

    meta_path = output_dir / "meta.json"
    meta: Dict[str, Any] = {
        "created_at_utc": _utc_now_iso(),
        "process": process_str,
        "tag": tag,
        "shape": shape,
        "n_in": n_in,
        "n_out": n_out,
        "model_id": model_id,
        "options": options,
        "output_dir": str(output_dir),
        "n0l": None,
        "n1l": None,
        "particles": particles,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    diagrams_root = output_dir / "diagrams"
    diagrams_root.mkdir(parents=True, exist_ok=True)

    qgraf_dat = tools_dir / "qgraf.dat"
    lock_path = tools_dir / ".qgraf.lock"
    _acquire_lock(lock_path)

    try:
        tree_main: Optional[Path] = None
        loop_main: Optional[Path] = None
        n0l = 0
        n1l = 0

        for loops in (0, 1):
            suffix = f"{loops}l"
            loop_out_dir = diagrams_root / suffix
            loop_out_dir.mkdir(parents=True, exist_ok=False)

            prefix_name = f"{tag}{suffix}"
            temp_prefix = f"__tmp__{tag}__{output_dir.name}__{suffix}"

            spec = QGrafSpec(
                output=temp_prefix,
                style=style_file.name,
                model=qgraf_model,
                incoming=incoming,
                outgoing=outgoing,
                loops=loops,
                loop_momentum="lm",
                options=options,
            )

            qgraf_dat.write_text(spec.to_text() + "\n", encoding="utf-8")
            res = _run_qgraf(qgraf_exe=qgraf_exe, cwd=tools_dir)

            (loop_out_dir / f"qgraf_{suffix}.stdout.log").write_text(res.stdout or "", encoding="utf-8")
            (loop_out_dir / f"qgraf_{suffix}.stderr.log").write_text(res.stderr or "", encoding="utf-8")

            if res.returncode != 0:
                raise RuntimeError(f"QGRAF failed for loops={loops}. See logs in {loop_out_dir}")

            combined = ((res.stdout or "") + "\n" + (res.stderr or "")).lower()
            if "error:" in combined:
                raise RuntimeError(f"QGRAF reported an error for loops={loops}. See logs in {loop_out_dir}")

            produced = sorted([p for p in tools_dir.glob(temp_prefix + "*") if p.is_file()])
            if not produced:
                raise RuntimeError(
                    f"QGRAF returned success but produced no files for temp prefix '{temp_prefix}'. "
                    f"See logs in {loop_out_dir}"
                )

            for p in produced:
                new_name = p.name.replace(temp_prefix, prefix_name, 1)
                shutil.move(str(p), str(loop_out_dir / new_name))

            shutil.copy2(str(qgraf_dat), str(loop_out_dir / "qgraf.dat"))
            shutil.copy2(str(style_file), str(loop_out_dir / style_file.name))

            main_out = _find_main_qgraf_output(loop_out_dir, prefix_name)
            txt = main_out.read_text(encoding="utf-8", errors="ignore")
            ndiagrams = _count_diagrams_from_text(txt)
            if ndiagrams == 0:
                raise RuntimeError(f"Main output '{main_out.name}' has no Local dN blocks; cannot count diagrams.")

            loop_meta = {
                "created_at_utc": _utc_now_iso(),
                "process": process_str,
                "tag": tag,
                "shape": shape,
                "n_in": n_in,
                "n_out": n_out,
                "model_id": model_id,
                "options": options,
                "loop": loops,
                "suffix": suffix,
                "main_output_file": main_out.name,
                "ndiagrams": ndiagrams,
            }
            (loop_out_dir / "meta.json").write_text(json.dumps(loop_meta, indent=2) + "\n", encoding="utf-8")

            if loops == 0:
                tree_main = main_out
                n0l = ndiagrams
            else:
                loop_main = main_out
                n1l = ndiagrams

        meta["n0l"] = n0l
        meta["n1l"] = n1l
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

        if not keep_temp:
            qgraf_dat.unlink(missing_ok=True)

        return {
            "process": process_str,
            "tag": tag,
            "shape": shape,
            "n_in": n_in,
            "n_out": n_out,
            "output_dir": output_dir,
            "meta_path": meta_path,
            "tree_main": tree_main,
            "loop_main": loop_main,
            "n0l": n0l,
            "n1l": n1l,
        }

    finally:
        _release_lock(lock_path)


# -----------------------------
# FORM prep (RAW evaluate only)
# -----------------------------
def _mass_for_particle_token(tok: str, model_id: Optional[str] = None) -> str:
    from glaslib.core.models import get_mass_for_particle
    return get_mass_for_particle(tok, model_id or "qcd_massive")


def _build_mand_define(process_str: str, model_id: Optional[str] = None) -> str:
    lhs, rhs = parse_process(process_str)
    tokens = lhs + rhs
    n_in, n_out = len(lhs), len(rhs)

    momenta = [f"p{i}" for i in range(1, len(tokens) + 1)]
    masses = [_mass_for_particle_token(t, model_id) for t in tokens]

    return f'#define mand "#call mandelstam{n_in}x{n_out}({",".join(momenta)},{",".join(masses)})"'


def _resolve_form_procedures_dir(project_root: Path) -> Path:
    from glaslib.core.paths import procedures_dir

    return procedures_dir()


def _chunk_range_1based(total: int, jobs: int, job_index: int) -> Tuple[int, int]:
    """
    Returns inclusive [start,end] in 1-based indexing.
    If total==0 -> (1,0) (empty).
    jobs is assumed >=1, job_index in [1..jobs].
    """
    if total <= 0:
        return 1, 0

    base = total // jobs
    rem = total % jobs

    # first 'rem' jobs get +1
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


def _write_evaluate_driver(
    *,
    dst: Path,
    incdir: Path,
    tag: str,
    n0l: int,
    n1l: int,
    mand_define_line: str,
    i0: int,
    i1: int,
    j0: int,
    j1: int,
) -> None:
    """
    RAW evaluation only:
      - tree: writes Files/Amps/amp0l/d<i>.h with d<i> and dC<i>
      - loop: writes Files/Amps/amp1l/d<i>.h with d<i>
    """
    tree_block = ""
    if i0 <= i1:
        tree_block = f"""
#do i={i0},{i1}
#include Files/{tag}0l
    .sort
l amp = d`i';
    .sort
Drop d1,...,d{n0l};
#call FeynmanRules
`mand'
#call SymToRat
#call Conjugate(amp,ampC)
    .sort
b diracChain,Color,i_,gs,eps,epsC;
    .sort
#write <Files/Amps/amp0l/d`i'.h> "l d`i' = (%E);\\n" amp
#write <Files/Amps/amp0l/d`i'.h> "l dC`i' = (%E);\\n" ampC
    .sort
Drop;
#enddo
"""
    else:
        tree_block = "\n* (no tree diagrams in this chunk)\n"

    loop_block = ""
    if j0 <= j1:
        loop_block = f"""
#do i={j0},{j1}
#include Files/{tag}1l
    .sort
l amp = d`i';
    .sort
Drop d1,...,d{n1l};
#call FeynmanRules
`mand'
#call SymToRat
    .sort
b diracChain,Color,i_,gs,eps,epsC,FAD;
    .sort
#write <Files/Amps/amp1l/d`i'.h> "l d`i' = (%E);\\n" amp
    .sort
Drop;
#message loop `i' done
#enddo
"""
    else:
        loop_block = "\n* (no loop diagrams in this chunk)\n"

    text = f"""#-
#: IncDir {incdir}
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;

#define n1l "{n1l}"
#define n0l "{n0l}"

{mand_define_line}

#include declarations.h
.sort
PolyRatFun rat;
.sort

* ---- TREE (this chunk) ----
{tree_block}

#message done with tree-level chunk

* ---- ONE-LOOP (this chunk) ----
{loop_block}

.end
"""
    dst.write_text(text, encoding="utf-8")


def _write_dirac_driver(
    *,
    dst: Path,
    incdir: Path,
    tag: str,
    n0l: int,
    n1l: int,
    mand_define_line: str,
    i0: int,
    i1: int,
    j0: int,
    j1: int,
) -> None:
    """
    Default DiracSimplify driver (no orthogonality constraints).
    Used only for the formprep return payload; the interactive DiracSimplify
    command uses dirac.py for customized drivers.
    """
    tree_block = ""
    if i0 <= i1:
        tree_block = f"""
* ---- TREE ----
#do i = {i0},{i1}
#include Files/Amps/amp0l/d`i'.h
    .sort
l amp = d`i';
    .sort
Drop d1,...,d{n0l};

#call SymToRat
#call DiracSimplify
#call SymToRat

b diracChain,Color,i_,gs,eps,epsC,FAD;
    .sort
#write <Files/Amps/amp0l/d`i'.h> "l d`i' = (%E);\\n" amp
    .sort
Drop;
#message dirac_tree `i'
#enddo
"""
    else:
        tree_block = "\n* (no tree diagrams in this chunk)\n"

    loop_block = ""
    if j0 <= j1:
        loop_block = f"""
* ---- ONE-LOOP ----
#do i = {j0},{j1}
#include Files/Amps/amp1l/d`i'.h
    .sort
l amp = d`i';
    .sort
Drop d1,...,d{n1l};

#call SymToRat
#call DiracSimplify
#call SymToRat

b diracChain,Color,i_,gs,eps,epsC,FAD;
    .sort
#write <Files/Amps/amp1l/d`i'.h> "l d`i' = (%E);\\n" amp
    .sort
Drop;
#message dirac_loop `i'
#enddo
"""
    else:
        loop_block = "\n* (no one-loop diagrams in this chunk)\n"

    text = f"""#-
#: IncDir {incdir}
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;

#define n1l "{n1l}"
#define n0l "{n0l}"

{mand_define_line}

#include declarations.h
.sort
PolyRatFun rat;
.sort

{tree_block}
{loop_block}

.end
"""
    dst.write_text(text, encoding="utf-8")


def prepare_form_project(output_dir: Path, *, jobs: int = 1) -> Dict[str, Any]:
    """
    Prepares:
      <output_dir>/form/Files/{tag}0l, {tag}1l
      <output_dir>/form/Files/Amps/amp0l
      <output_dir>/form/Files/Amps/amp1l

    Writes chunked evaluate drivers:
      simplify_amplitude_eval_JkofN.frm

    IMPORTANT: DiracSimplify is NOT part of evaluation anymore.
    """
    output_dir = Path(output_dir).resolve()
    meta_path = output_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in {output_dir}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    process_str = meta["process"]
    tag = meta["tag"]
    n0l = int(meta.get("n0l") or 0)
    n1l = int(meta.get("n1l") or 0)

    m0 = json.loads((output_dir / "diagrams" / "0l" / "meta.json").read_text(encoding="utf-8"))
    m1 = json.loads((output_dir / "diagrams" / "1l" / "meta.json").read_text(encoding="utf-8"))

    tree_main = output_dir / "diagrams" / "0l" / m0["main_output_file"]
    loop_main = output_dir / "diagrams" / "1l" / m1["main_output_file"]

    if not tree_main.exists():
        raise FileNotFoundError(f"Missing tree diagrams file: {tree_main}")
    if not loop_main.exists():
        raise FileNotFoundError(f"Missing loop diagrams file: {loop_main}")

    project_root = output_dir.parent
    incdir = _resolve_form_procedures_dir(project_root)
    if not (incdir / "declarations.h").exists():
        raise FileNotFoundError(f"declarations.h not found in procedures dir: {incdir}")

    model_id = meta.get("model_id")
    mand_define_line = _build_mand_define(process_str, model_id)

    form_dir = output_dir / "form"
    files_dir = form_dir / "Files"
    amps0 = files_dir / "Amps" / "amp0l"
    amps1 = files_dir / "Amps" / "amp1l"

    amps0.mkdir(parents=True, exist_ok=True)
    amps1.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)

    # Copy diagram files into form Files/
    shutil.copy2(str(tree_main), str(files_dir / f"{tag}0l"))
    shutil.copy2(str(loop_main), str(files_dir / f"{tag}1l"))

    # clamp jobs to n0l (avoid empty tree chunks)
    jobs_requested = max(1, int(jobs))
    jobs_effective = max(1, min(jobs_requested, n0l or 1))

    eval_drivers: Dict[int, Path] = {}
    dirac_drivers: Dict[int, Path] = {}

    meta["tree_main"] = f"{tag}0l"
    meta["loop_main"] = f"{tag}1l"
    meta["mand_define"] = mand_define_line
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    for j in range(1, jobs_effective + 1):
        # tree chunk based on n0l
        i0, i1 = _chunk_range_1based(n0l, jobs_effective, j)
        # loop chunk distributed over same number of jobs (can be empty if n1l is small)
        j0, j1 = _chunk_range_1based(n1l, jobs_effective, j)

        drv = form_dir / f"simplify_amplitude_eval_J{j}of{jobs_effective}.frm"
        _write_evaluate_driver(
            dst=drv,
            incdir=incdir,
            tag=tag,
            n0l=n0l,
            n1l=n1l,
            mand_define_line=mand_define_line,
            i0=i0,
            i1=i1,
            j0=j0,
            j1=j1,
        )
        eval_drivers[j] = drv

        dirac_drv = form_dir / f"dirac_simplify_both_J{j}of{jobs_effective}.frm"
        _write_dirac_driver(
            dst=dirac_drv,
            incdir=incdir,
            tag=tag,
            n0l=n0l,
            n1l=n1l,
            mand_define_line=mand_define_line,
            i0=i0,
            i1=i1,
            j0=j0,
            j1=j1,
        )
        dirac_drivers[j] = dirac_drv

    return {
        "jobs_requested": jobs_requested,
        "jobs_effective": jobs_effective,
        "form_dir": form_dir,
        "evaluate": {
            "form_dir": form_dir,
            "drivers": eval_drivers,
            "jobs_effective": jobs_effective,
        },
        "dirac": {
            "form_dir": form_dir,
            "drivers": dirac_drivers,
            "jobs_effective": jobs_effective,
        },
    }

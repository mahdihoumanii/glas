from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, Optional

from glaslib.commands.common import AppState, MODES, clamp_jobs, parse_mode_and_flags
from glaslib.counterterms import prepare_mass_ct
from glaslib.dirac import prepare_dirac
from glaslib.formprep import prepare_form
from glaslib.core.logging import LOG_SUBDIR_EVALUATE, LOG_SUBDIR_DIRAC
from glaslib.core.parallel import chunk_range_1based, run_jobs
from glaslib.core.paths import procedures_dir, setup_run_procedures


def _write_eval_driver(
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
    mode: str,
) -> None:
    tree_block = "\n* (tree skipped)\n"
    if mode == "lo" and i0 <= i1:
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

    loop_block = "\n* (loop skipped)\n"
    if mode == "nlo" and j0 <= j1:
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

* ---- ONE-LOOP (this chunk) ----
{loop_block}

.end
"""
    dst.write_text(text, encoding="utf-8")


def _prepare_eval_drivers(
    *,
    form_dir: Path,
    incdir: Path,
    tag: str,
    n0l: int,
    n1l: int,
    mand_define: str,
    jobs_effective: int,
    mode: str,
) -> Dict[int, Path]:
    drivers: Dict[int, Path] = {}
    total = n0l if mode == "lo" else n1l
    for k in range(1, jobs_effective + 1):
        i0, i1 = chunk_range_1based(total, jobs_effective, k)
        if total <= 0 or i0 > i1:
            continue
        if mode == "lo":
            j0, j1 = 1, 0
        else:
            j0, j1 = i0, i1
            i0, i1 = 1, 0
        drv = form_dir / f"eval_{mode}_J{k}of{jobs_effective}.frm"
        _write_eval_driver(
            dst=drv,
            incdir=incdir,
            tag=tag,
            n0l=n0l,
            n1l=n1l,
            mand_define_line=mand_define,
            i0=i0,
            i1=i1,
            j0=j0,
            j1=j1,
            mode=mode,
        )
        drivers[k] = drv
    return drivers


def _resolve_jobs_requested(state: AppState, jobs: Optional[int]) -> int:
    if jobs is not None:
        return max(1, int(jobs))
    meta_jobs = state.ctx.meta.get("jobs_requested") if isinstance(state.ctx.meta, dict) else None
    try:
        return max(1, int(meta_jobs or 1))
    except Exception:
        return 1


def run(state: AppState, arg: str) -> None:
    mode, jobs, use_dirac, verbose = parse_mode_and_flags(arg, allow_dirac=True)
    verbose = verbose or state.verbose  # Also check state.verbose
    if mode not in MODES:
        print("Usage: evaluate {lo|nlo|mct} [--jobs K] [--dirac] [--verbose]")
        return
    if not state.ensure_run():
        return

    jobs_req = _resolve_jobs_requested(state, jobs)
    meta = state.ctx.meta
    n0l = int(meta.get("n0l") or 0)
    n1l = int(meta.get("n1l") or 0)

    if mode in ("lo", "nlo"):
        prepare_form(state.ctx, jobs=jobs_req)
        meta_path = state.ctx.run_dir / "meta.json"  # type: ignore[operator]
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        state.ctx.meta = meta
        form_dir = state.ctx.prep_form_dir or state.ctx.run_dir / "form"  # type: ignore[operator]
        if not form_dir:
            print("Error: form directory not prepared. Run generate first.")
            return

        # Set up model-specific procedures directory
        feynman_rules_prc = state.get_feynman_rules_file()
        incdir = setup_run_procedures(state.ctx.run_dir, feynman_rules_prc)  # type: ignore[arg-type]
        mand_define = meta.get("mand_define")
        if not mand_define:
            print("Error: mand_define missing in meta.json (run generate first).")
            return

        n_diagrams = n0l if mode == "lo" else n1l
        if n_diagrams <= 0:
            print(f"Error: no diagrams recorded for mode {mode}.")
            return

        jobs_req, jobs_eff = clamp_jobs(jobs_req, n_diagrams)
        drivers = _prepare_eval_drivers(
            form_dir=form_dir,
            incdir=incdir,
            tag=meta["tag"],
            n0l=n0l,
            n1l=n1l,
            mand_define=mand_define,
            jobs_effective=jobs_eff,
            mode=mode,
        )
        tasks = [(f"evaluate_{mode}_J{k}of{jobs_eff}", form_dir, drv) for k, drv in drivers.items()]
        ok = run_jobs(state.form_exe, tasks, max_workers=jobs_eff, verbose=verbose, run_dir=state.ctx.run_dir, log_subdir=LOG_SUBDIR_EVALUATE)
        if not ok:
            return
        print(f"[evaluate {mode}] All jobs finished OK.")

        if use_dirac:
            process_str = meta.get("process", "") or ""
            gluon_refs = state.refs().get_or_prompt(process_str)
            dirac_mode = "0" if mode == "lo" else "1"
            out = prepare_dirac(state.ctx, mode=dirac_mode, jobs=jobs_req, gluon_orth=gluon_refs)
            info = out.get("tree") if mode == "lo" else out.get("loop")
            if not info:
                print("[dirac] No drivers produced.")
                return
            tasks = [
                (f"DiracSimplify_{mode}_J{k}of{info.get('jobs_effective', jobs_req)}", out["form_dir"], drv)
                for k, drv in info.get("drivers", {}).items()
            ]
            ok_dirac = run_jobs(state.form_exe, tasks, max_workers=info.get("jobs_effective", jobs_req), verbose=verbose, run_dir=state.ctx.run_dir, log_subdir=LOG_SUBDIR_DIRAC)
            if ok_dirac:
                print(f"[dirac {mode}] All jobs finished OK.")
        return

    # mode == "mct"
    # Check if massless model - no mass counterterms needed
    model_id = meta.get("model_id", "qcd_massive")
    if model_id == "qcd_massless":
        print("[evaluate mct] Skipped: mass counterterms are zero for massless QCD.")
        return

    try:
        out = prepare_mass_ct(state.ctx, form_exe=state.form_exe, jobs=jobs_req)
    except Exception as exc:
        print(f"Error: {exc}")
        return
    tasks = [
        (f"mct_J{k}of{out['jobs_effective']}", out["form_dir"], drv)
        for k, drv in out["drivers"].items()
    ]
    ok = run_jobs(state.form_exe, tasks, max_workers=out["jobs_effective"], verbose=verbose, run_dir=state.ctx.run_dir, log_subdir=LOG_SUBDIR_EVALUATE)
    if not ok:
        return
    print("[evaluate mct] All jobs finished OK.")

    if use_dirac:
        form_dir = out["form_dir"]
        mct_dir = Path(form_dir) / "Files" / "Amps" / "mct"
        mct_raw = Path(form_dir) / "Files" / "Amps" / "mct_raw"
        if mct_raw.exists():
            shutil.rmtree(mct_raw)
        if mct_dir.exists():
            shutil.copytree(mct_dir, mct_raw)

        process_str = meta.get("process", "") or ""
        gluon_refs = state.refs().get_or_prompt(process_str)
        try:
            out_dirac = prepare_dirac(state.ctx, mode="mct", jobs=jobs_req, gluon_orth=gluon_refs)
        except Exception as exc:
            print(f"Error: {exc}")
            return
        info = out_dirac.get("mct") or {}
        tasks = [
            (f"DiracSimplify_mct_J{k}of{info.get('jobs_effective', jobs_req)}", out_dirac["form_dir"], drv)
            for k, drv in info.get("drivers", {}).items()
        ]
        ok_dirac = run_jobs(state.form_exe, tasks, max_workers=info.get("jobs_effective", jobs_req), verbose=verbose, run_dir=state.ctx.run_dir, log_subdir=LOG_SUBDIR_DIRAC)
        if ok_dirac:
            print("[dirac mct] All jobs finished OK.")

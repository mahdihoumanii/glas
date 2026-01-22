from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from glaslib.core.parallel import chunk_range_1based, effective_jobs


class ReduceConfigError(Exception):
    pass


def _load_meta(run_dir: Path) -> Dict[str, Any]:
    meta_path = Path(run_dir) / "meta.json"
    if not meta_path.exists():
        raise ReduceConfigError(f"Missing meta.json in {run_dir}")
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ReduceConfigError(f"Failed to read meta.json: {exc}")


def _validate_inputs(form_dir: Path, n0l: int, n1l: int, ntop: int, nmis: int) -> None:
    files_dir = form_dir / "Files"
    m0m1top = files_dir / "M0M1top"
    ibp_dir = files_dir / "IBP"
    symrel = files_dir / "SymmetryRelations.h"

    if n0l <= 0:
        raise ReduceConfigError("n0l <= 0 (no tree amplitudes)")
    if n1l <= 0:
        raise ReduceConfigError("n1l <= 0 (no loop amplitudes)")
    if ntop <= 0:
        raise ReduceConfigError("ntop <= 0 (no topologies recorded; rerun extract topologies)")
    if nmis <= 0:
        raise ReduceConfigError("nmis <= 0 (no master integrals recorded; rerun ibp)")

    if not m0m1top.exists():
        raise ReduceConfigError(f"Missing {m0m1top} (run 'extract topologies' stage 3 first)")
    if not ibp_dir.exists() or not list(ibp_dir.glob("IBP*.h")):
        raise ReduceConfigError(f"Missing IBP reduction files in {ibp_dir} (run ibp)")
    if not symrel.exists():
        raise ReduceConfigError(f"Missing {symrel} (run ibp to generate SymmetryRelations.h)")


def prepare_reduce_project(run_dir: Path, *, jobs: int = 1, micoef: bool = False) -> Dict[str, Any]:
    """
    Generate chunked FORM drivers for final reduction (M0M1top -> M0M1Reduced).
    Splits outer i=1..n0l across jobs; inner loops cover all j=1..n1l and k=1..ntop.
    Also writes a MasterCoefficients.frm driver to project master integral coefficients.
    If micoef=True, also writes SumMasterCoefs.frm to sum coefficients across diagrams.
    """
    run_dir = Path(run_dir).resolve()
    meta = _load_meta(run_dir)

    n0l = int(meta.get("n0l", 0) or 0)
    n1l = int(meta.get("n1l", 0) or 0)
    ntop = int(meta.get("ntop", 0) or 0)
    nmis = int(meta.get("nmis", 0) or 0)

    form_dir = run_dir / "form"
    files_dir = form_dir / "Files"

    _validate_inputs(form_dir, n0l, n1l, ntop, nmis)

    m0m1red_form = files_dir / "M0M1Reduced"
    m0m1red_form.mkdir(parents=True, exist_ok=True)

    m0m1red_math = run_dir / "Mathematica" / "Files" / "M0M1Reduced"
    m0m1red_math.mkdir(parents=True, exist_ok=True)

    master_form = files_dir / "MasterCoefficients"
    master_form.mkdir(parents=True, exist_ok=True)

    master_math = run_dir / "Mathematica" / "Files" / "MasterCoefficients"
    master_math.mkdir(parents=True, exist_ok=True)

    for k in range(1, nmis + 1):
        (master_form / f"mi{k}").mkdir(parents=True, exist_ok=True)
        (master_math / f"mi{k}").mkdir(parents=True, exist_ok=True)

    jobs_requested = max(1, int(jobs))
    jobs_effective = effective_jobs(n0l, jobs_requested)

    drivers: Dict[int, Path] = {}
    for k in range(1, jobs_effective + 1):
        i0, i1 = chunk_range_1based(n0l, jobs_effective, k)
        if i0 > i1:
            continue

        frm = form_dir / f"reduce_J{k}of{jobs_effective}.frm"
        frm.write_text(
            f"""#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;
#include declarations.h
#define n0l \"{n0l}\"
#define n1l \"{n1l}\"
#define ntop \"{ntop}\"
.sort
#do i ={i0},{i1}
#do j =1,`n1l'

#include Files/M0M1top/d`i'x`j'.h

#do k = 1, `ntop'
if (match(GLI(top`k',?a)));
#include Files/IBP/IBP`k'.h
endif;
    .sort 
#enddo 

#include Files/SymmetryRelations.h
    .sort 
id rat(x1?,x2?) = x1*den(x2);
    .sort
#call RationalFunction
repeat id s12?{{s12,s23,s34,s45,s15,s13,s14,mt}}^-1 = den(s12);
    .sort
Format;
b GLI, ep,gs,PaVeFun;
    .sort 
#write <Files/M0M1Reduced/d`i'x`j'.h> \"l d`i'x`j' = (%E ); \\n\" d`i'x`j'
    .sort 
id i_ = I;
Format mathematica; 
b GLI, ep,gs,PaVeFun;
    .sort
#write <../Mathematica/Files/M0M1Reduced/d`i'x`j'.m> \"d[`i',`j'] = (%E ); \\n\" d`i'x`j'

    .sort 
Drop; 
    .sort 
#message Reduced d`i'x`j' saved.
#enddo 
#enddo 
.end
""",
            encoding="utf-8",
        )
        drivers[k] = frm

    master_driver = form_dir / "MasterCoefficients.frm"
    master_driver.write_text(
        f"""#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;



#define n1l \"{n1l}\"
#define n0l \"{n0l}\"
#define nmis \"{nmis}\"


#include declarations.h
.sort

#do i  = 1,`n0l'
#do j  = 1,`n1l'
#do k  = 1,`nmis'
#include Files/M0M1Reduced/d`i'x`j'.h
#include Files/MastersToSym.h 
id mis`k' = 1;
.sort 
id mis?{{mis1,...,mis`nmis'}} = 0;
    .sort 
Mul mis`k'; 
    .sort
#include Files/SymToMasters.h
    .sort
#call rationals
Format;
b GLI, ep,gs,PaVeFun,den,rat;
    .sort 
#write <Files/MasterCoefficients/mi`k'/d`i'x`j'.h> \"l d`i'x`j' = (%E ); \\n\" d`i'x`j'
    .sort 
id i_ = I;
Format mathematica; 
b GLI, ep,gs,PaVeFun,den,rat;
    .sort
#write <../Mathematica/Files/MasterCoefficients/mi`k'/d`i'x`j'.m> \"d[`i',`j'] = (%E ); \\n\" d`i'x`j'

    .sort 
Drop; 
    .sort 

#enddo
#enddo
#enddo


b PaVeFun,ep,gs; 
Print; 
    .end
""",
        encoding="utf-8",
    )

    sum_master_driver = None
    if micoef:
        sum_master_driver = form_dir / "SumMasterCoefs.frm"
        sum_master_driver.write_text(
            f"""#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;



#define n1l \"{n1l}\"
#define n0l \"{n0l}\"
#define nmis \"{nmis}\"



#include declarations.h
.sort
#do k = 1, `nmis'
#do i = 1, `n0l'
#do j = 1, `n1l'

#include Files/MasterCoefficients/mi`k'/d`i'x`j'.h
    .sort
id rat(?a) = Rat(?a);
    .sort
#enddo
l coef`k'x`i' = d`i'x1+...+d`i'x`n1l';
    .sort
Drop d`i'x1,...,d`i'x`n1l';
    .sort
#enddo
l coef`k' = coef`k'x1+...+coef`k'x`n0l';
    .sort
Drop coef`k'x1,...,coef`k'x`n0l';
    .sort
PolyratFun rat; 
#do i = 1,1
    .sort 
ab A0, B0, C0, D0,den,ep;
    .sort 
keep Brackets; 
id once, Rat(x1?,x2?) = rat(x1,x2); 
if (count(Rat,1)!= 0); 
    redefine i \"0\";
endif; 
    .sort
#enddo
PolyRatFun;
    .sort 
id i_ = I;
format mathematica;
b den,gs, ep, rat,PaVeFun,i_;
    .sort
#write <../Mathematica/Files/MasterCoefficients/mi`k'/MasterCoefficient`k'.m> \"coef[`k'] = (%E ); \\n\" coef`k'
    .sort
Drop;
    .sort 
#enddo

Print;
    .end
""",
            encoding="utf-8",
        )

    return {
        "form_dir": form_dir,
        "jobs_requested": jobs_requested,
        "jobs_effective": jobs_effective,
        "drivers": drivers,
        "master_driver": master_driver,
        "sum_master_driver": sum_master_driver,
    }

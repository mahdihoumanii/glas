from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


def _chunk_range_1based(total: int, jobs: int, job_index: int) -> Tuple[int, int]:
    """Compute inclusive 1-based range [start, end] for job_index of jobs."""
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


def prepare_topoformat_project(
    output_dir: Path,
    *,
    jobs: int = 1,
) -> Dict[str, Any]:
    """
    Generate parallel ToTopos.frm drivers for topology extraction.
    
    Assumes:
      - Files/M0M1/ contains d<i>x<j>.h files from IBP reduction (M0×M1 contractions)
      - Files/intrule.h exists (integral substitution rules)
      - ../Mathematica/Files/M0M1top/ will receive .m output
      - ../Mathematica/Files/M0M1top/ will receive .h output
    
    Chunking:
      Outer loop i=1..n0l split across jobs; inner loop j always runs 1..n1l
      Each job writes:
        - form/Files/M0M1top/d<i>x<j>.h (FORM format)
        - Mathematica/Files/M0M1top/d<i>x<j>.m (Mathematica format)
    """
    output_dir = Path(output_dir).resolve()

    meta_path = output_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in: {output_dir}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    n0l = int(meta.get("n0l") or 0)
    n1l = int(meta.get("n1l") or 0)
    
    if n0l <= 0:
        raise ValueError("n0l is 0: no tree amplitudes found.")
    if n1l <= 0:
        raise ValueError("n1l is 0: no loop amplitudes found.")

    form_dir = output_dir / "form"
    files_dir = form_dir / "Files"

    m0m1_dir = files_dir / "M0M1"
    if not m0m1_dir.exists():
        raise FileNotFoundError(
            f"Missing {m0m1_dir}. Run contract nlo first to generate M0×M1 amplitudes."
        )

    intrule_file = files_dir / "intrule.h"
    if not intrule_file.exists():
        raise FileNotFoundError(
            f"Missing {intrule_file}. Run extract topologies (stage2) first."
        )

    m0m1top_form = files_dir / "M0M1top"
    m0m1top_form.mkdir(parents=True, exist_ok=True)

    m0m1top_math = output_dir / "Mathematica" / "Files" / "M0M1top"
    m0m1top_math.mkdir(parents=True, exist_ok=True)

    jobs_requested = max(1, int(jobs))
    jobs_effective = max(1, min(jobs_requested, n0l))

    drivers: Dict[int, Path] = {}

    for k in range(1, jobs_effective + 1):
        i0, i1 = _chunk_range_1based(n0l, jobs_effective, k)
        if i0 > i1:
            continue

        frm = form_dir / f"ToTopos_J{k}of{jobs_effective}.frm"

        frm.write_text(
            f"""#-
#: IncDir procedures
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;
#include declarations.h
.sort
PolyRatFun rat;
.sort
Cfun SPD(symmetric);
.sort
#define n1l "{n1l}"
#define n0l "{n0l}"


#do i={i0},{i1}
#do j=1,`n1l'

#include Files/M0M1/d`i'x`j'.h
    .sort
#include Files/intrule.h
    .sort

if((occurs(LoopInt) == 1)||(occurs(SPD) == 1)||(occurs(lm1) == 1));
exit "Loop integrals still present in raw form in d`i'xd`j'";

else;
#message all integrals reduced to scalar integrals for `i'x`j'
endif;
    .sort 
#call SymToRat
    .sort 
Format;
b GLI, ep,gs;
    .sort 
#write <Files/M0M1top/d`i'x`j'.h> "l d`i'x`j' = (%E ); \\n" d`i'x`j'
    .sort 
id i_ = I;
Format mathematica; 
b GLI, ep,gs;
    .sort
#write <../Mathematica/Files/M0M1top/d`i'x`j'.m> "d[`i',`j'] = (%E ); \\n" d`i'x`j'

    .sort 
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

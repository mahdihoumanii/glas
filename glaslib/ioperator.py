from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from glaslib.generate_diagrams import parse_process
from glaslib.contractLO import _collect_gluon_momenta, _write_gluon_polarization_section
from glaslib.core.paths import ensure_symlink_or_copy, procedures_dir
from glaslib.core.run_manager import RunContext
from glaslib.core.parallel import run_jobs


def _particles_from_meta(meta: Dict[str, Any]) -> List[Dict[str, str]]:
    parts = meta.get("particles")
    if isinstance(parts, list):
        filtered = [p for p in parts if isinstance(p, dict)]
        if filtered:
            return filtered

    proc = meta.get("process")
    if isinstance(proc, str) and proc.strip():
        lhs, rhs = parse_process(proc)
        n_in = len(lhs)
        tokens = lhs + rhs
        return [
            {"token": tok, "momentum": f"p{i+1}", "side": "in" if i < n_in else "out"}
            for i, tok in enumerate(tokens)
        ]
    return []


def _t_definition(idx: int, token: str, side: str) -> str:
    tok = token.lower()
    side = side.lower()
    if tok == "g":
        return f"id T({idx}) = i_ *f( b{idx}, c, c{idx});"

    is_quark = tok in ("q", "t")
    is_antiquark = tok in ("q~", "qbar", "t~", "tbar")
    if not (is_quark or is_antiquark):
        raise ValueError(f"Unsupported particle token for T definition: {token!r}")

    outgoing_quark_like = side == "out" and is_quark
    outgoing_anti_like = side == "out" and is_antiquark
    incoming_quark_like = side == "in" and is_quark
    incoming_anti_like = side == "in" and is_antiquark

    if outgoing_quark_like or incoming_anti_like:
        return f"id T({idx}) =  T(c, a{idx}, c{idx});"
    if outgoing_anti_like or incoming_quark_like:
        return f"id T({idx}) = - T(c, c{idx}, a{idx});"
    raise ValueError(f"Cannot build T definition for leg {idx} ({token}, side={side}).")


def _build_driver_text(
    *,
    incdir: Path,
    n0l: int,
    mand_define: str,
    leg_i: int,
    leg_j: int,
    t_defs: List[str],
    pol_block: str,
    gluon_count: int,
    output_rel: str,
    form_output_rel: str,
) -> str:
    pol_section = pol_block.rstrip() + "\n" if pol_block.strip() else ""
    pol_call = f"#call PolarizationSums({gluon_count})\n" if gluon_count > 0 else ""
    return f"""#-
#: IncDir {incdir}
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;
#define n0l "{n0l}"
#define in1 "{leg_i}"
#define in2 "{leg_j}"

{mand_define}
#include declarations.h
    .sort 

#do i =1, `n0l'

#include Files/Amps/amp0l/d`i'.h
    .sort
#enddo
    .sort 

L amp = d1+...+d`n0l';
L ampC = dC1+...+dC`n0l';
    .sort 
Drop d1,...,d`n0l',dC1,...,dC`n0l';

Mul replace_(a6,a5,b6,b5,b3,b2,a3,a2,a2,a3,b2,b3);
id rat(x1?,x2?) = x1*den(x2);
#call RationalFunction

    .sort 
#call color
    .sort 
Skip ampC;

Mul replace_(a`in1',c`in1');
Mul replace_(a`in2',c`in2');
Mul replace_(b`in1',c`in1');
Mul replace_(b`in2',c`in2');

Mul T(`in1')*T(`in2'); 
{chr(10).join(t_defs)}

    .sort 

Mul ampC;
    .sort 

Drop ampC;

#call color

{pol_section}{pol_call}
`mand'
#call PolarizationSums(5)
`mand'
    .sort 
repeat id D = 4 -2 *ep;

    .sort 

#call RationalFunction
#call toden
.sort 
Format mathematica;
    .sort 

#write <{output_rel}> "I[`in1',`in2'] = (%E);\\n" amp
    .sort
Format;
    .sort
#write <{form_output_rel}> "l I`in1'x`in2' = (%E);\\n" amp

    .end
"""


def prepare_ir_file(ctx: RunContext, *, leg_i: int, leg_j: int, gluon_refs: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    if not ctx.run_dir:
        raise RuntimeError("No run attached.")

    meta_path = ctx.run_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    n0l = int(meta.get("n0l") or 0)
    if n0l <= 0:
        raise RuntimeError("n0l is 0: run 'evaluate' first to produce tree amplitudes.")

    form_dir = ctx.prep_form_dir or ctx.run_dir / "form"
    files_dir = form_dir / "Files" / "Amps" / "amp0l"
    if not files_dir.exists():
        raise FileNotFoundError(f"Missing tree amplitudes: {files_dir}. Run 'evaluate' first.")

    max_leg = int(meta.get("n_in") or 0) + int(meta.get("n_out") or 0)
    if not (1 <= leg_i <= max_leg and 1 <= leg_j <= max_leg):
        raise ValueError(f"Leg indices must be between 1 and {max_leg}. Got {leg_i}, {leg_j}.")

    mand_define = meta.get("mand_define")
    if not mand_define:
        raise RuntimeError("mand_define missing in meta.json (run formprep/evaluate first).")

    procs_src = procedures_dir()
    incdir = form_dir / "procedures"
    ensure_symlink_or_copy(procs_src, incdir)

    particles = _particles_from_meta(meta)
    if not particles:
        raise RuntimeError("Particle information missing in meta.json. Regenerate diagrams to populate it.")

    t_defs: List[str] = []
    gluons = 0
    for idx, info in enumerate(particles, 1):
        tok = info.get("token", "").lower()
        side = info.get("side", "out" if idx > int(meta.get("n_in") or 0) else "in")
        if tok == "g":
            gluons += 1
        t_defs.append(_t_definition(idx, tok, side))

    process_str = meta.get("process", "")
    gluon_moms = _collect_gluon_momenta(process_str) if process_str else []
    pol_block = _write_gluon_polarization_section(process_str, gluon_refs or {}) if process_str else ""

    output_dir = ctx.run_dir / "mathematica" / "Files" / "Ioperator"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_rel = f"../mathematica/Files/Ioperator/I{leg_i}x{leg_j}.m"
    form_files_dir = form_dir / "Files" / "Ioperator"
    form_files_dir.mkdir(parents=True, exist_ok=True)
    form_output_rel = f"Files/Ioperator/I{leg_i}x{leg_j}.h"

    driver = form_dir / f"Ioperator_{leg_i}x{leg_j}.frm"
    driver.write_text(
        _build_driver_text(
            incdir=incdir,
            n0l=n0l,
            mand_define=mand_define,
            leg_i=leg_i,
            leg_j=leg_j,
            t_defs=t_defs,
            pol_block=pol_block,
            gluon_count=len(gluon_moms),
            output_rel=output_rel,
            form_output_rel=form_output_rel,
        ),
        encoding="utf-8",
    )

    return {
        "form_dir": form_dir,
        "driver": driver,
        "output_file": output_dir / f"I{leg_i}x{leg_j}.m",
        "form_output_file": form_files_dir / f"I{leg_i}x{leg_j}.h",
        "gluon_count": gluons,
    }


def prepare_ir_full(ctx: RunContext, *, gluon_refs: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    if not ctx.run_dir:
        raise RuntimeError("No run attached.")

    meta_path = ctx.run_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    parts = _particles_from_meta(meta)
    if not parts:
        raise RuntimeError("Particle information missing in meta.json. Regenerate diagrams to populate it.")
    nlegs = len(parts)
    if nlegs < 2:
        raise ValueError("Need at least two legs to build I operators.")

    drivers = []
    for i in range(1, nlegs + 1):
        for j in range(i + 1, nlegs + 1):
            info = prepare_ir_file(ctx, leg_i=i, leg_j=j, gluon_refs=gluon_refs)
            drivers.append((i, j, info))

    return {"drivers": drivers}


def _massless_indices(particles: List[Dict[str, str]]) -> List[int]:
    massless_tokens = {"g", "q", "q~", "qbar"}
    res = []
    for i, p in enumerate(particles, 1):
        if p.get("token", "").lower() in massless_tokens:
            res.append(i)
    return res


def _massive_indices(particles: List[Dict[str, str]]) -> List[int]:
    massless = set(_massless_indices(particles))
    return [i for i in range(1, len(particles) + 1) if i not in massless]


def _gamma_map_lines(particles: List[Dict[str, str]]) -> str:
    lines = []
    for i, p in enumerate(particles, 1):
        tok = p.get("token", "").lower()
        kind = "g" if tok == "g" else ("q" if tok in ("q", "q~", "qbar") else "top")
        lines.append(f"id aGamma?{{aGamma,casimir}}({i}) = aGamma({kind});")
    return "\n".join(lines)


def _build_ioperator_master(
    *,
    incdir: Path,
    np: int,
    n0l: int,
    mand_define: str,
    massless: List[int],
    massive: List[int],
    incoming: List[int],
    outgoing: List[int],
    gamma_lines: str,
) -> str:
    massless_str = ",".join(str(i) for i in massless) or "0"
    massive_str = ",".join(str(i) for i in massive) or "0"
    incoming_str = ",".join(str(i) for i in incoming) or "0"
    outgoing_str = ",".join(str(i) for i in outgoing) or "0"
    return f"""#-
#: IncDir {incdir}
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;
#include declarations.h 


#define np "{np}"
#define n0l "{n0l}"
{mand_define}


#define massless "{massless_str}"
#define massive "{massive_str}"
#define incoming "{incoming_str}"
#define outgoing "{outgoing_str}"
#include Files/TotalLO/TotalLO.h


#do i = 1, `np'
#do j = `i'+ 1 , `np'

#include Files/Ioperator/I`i'x`j'.h

#enddo
#enddo
l const = gs^2/4/Pi/4/Pi * 1/ep ;
l sumcmassless =     
#do i = {{`massless'}}
    +casimir(`i')
#enddo 
;
l sumgam =
#do i = 1,`np'
    +aGamma(`i')
#enddo 
;
l m0m0 =
#do i = {{`massless'}}
#do j = {{`massless'}}
#if (`i' != `j' && `i'<`j')
    +Log(ScaleMu^2*den(SPD(`i',`j')))*I`i'x`j'
#elseif `i' > `j'
    +Log(ScaleMu^2*den(SPD(`i',`j')))*I`j'x`i'
#else
+0
#endif

#enddo 
#enddo 
;

l mm =
#do i = {{`massive'}}
#do j = {{`massive'}}
#if (`i' != `j' && `i'<`j')
    +den(Vel(`i',`j')) *Log(Vel,`i',`j')*I`i'x`j'
#elseif `i' > `j'
    +den(Vel(`i',`j')) *Log(Vel,`i',`j')*I`j'x`i'
#else
+0
#endif

#enddo 
#enddo 
;


    .sort 


l m0m=
#do i = {{`massive'}}
#do j = {{`massless'}}
#if (`i' != `j' && `i'<`j')
    +Log(mass(p`i')*ScaleMu*den(SPD(`i',`j')))*I`i'x`j'
#elseif `i' > `j'
    +Log(mass(p`i')*ScaleMu*den(SPD(`i',`j')))*I`j'x`i'
#else
+0
#endif

#enddo 
#enddo 
;
    .sort 
#do i = {{`incoming'}}
#do j = {{`incoming'}}
argument Log;
argument den;
id SPD(`i',`j') = 2*p`i'.p`j';
id SPD(`j',`i') = 2*p`i'.p`j';
`mand'
endargument;
endargument;
#enddo
#enddo

#do i = {{`incoming'}}
#do j = {{`outgoing'}}
argument Log;
argument den;
id SPD(`i',`j') = -2*p`i'.p`j';
id SPD(`j',`i') = -2*p`i'.p`j';
`mand'
endargument;
`mand'
endargument;
#enddo
#enddo

argument Log;
id den(mt?) = 1/mt;
endargument;

`mand'
    .sort 
#do i = {{`massive'}}
#do j = {{`massive'}}

id Log(Vel,`i',`j') = Log((1- Vel(`i',`j'))*den(1+ Vel(`i',`j')));

#enddo 
#enddo
    .sort 
#do i =  1,`np';
Drop I`i'x1,...,I`i'x`np';
#enddo 
    .sort 
Local Ioperator = const*(
    ((-2/ep)*sumcmassless + sumgam)*TotalLO
    +   2* m0m0

    - mm

    + 4 * m0m

    );
    .sort 
Drop TotalLO, const, sumcmassless,sumgam, m0m0,m0m, mm;
{gamma_lines}

id casimir(q?{{q,top}}) = 4/3;
id casimir(g) = 3;
id aGamma(top) = -2 *4/3;
id aGamma(q)= -3 *4/3;
id aGamma(g) = - 11/3 * 3 + 4/3* 1/2*nl; 


    .sort 
repeat id D = 4-2 *ep;

    .sort 
id ep^pow  = Pole(ep, pow);
id Pole(ep, 0) = 1;
id Pole(ep, -1) = 1/ep;
id Pole(ep, -2) = 1/ep^2;
    .sort 
id Pole(?a) = 0;
    .sort 
#call RationalFunction
#call toden
Format mathematica;
b Log, Vel,ep,Pi,den;
    .sort
#write <../mathematica/Files/Ioperator.m> "Ioperator = (%E);\\n" Ioperator
    .sort
Format;
    .sort

b ep;
Print; 
    .end 
"""


def prepare_ioperator_master(ctx: RunContext, *, gluon_refs: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    if not ctx.run_dir:
        raise RuntimeError("No run attached.")
    meta_path = ctx.run_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    particles = _particles_from_meta(meta)
    if not particles:
        raise RuntimeError("Particle information missing in meta.json.")

    incdir = (ctx.prep_form_dir or ctx.run_dir / "form") / "procedures"
    np = len(particles)
    n0l = int(meta.get("n0l") or 0)
    mand_define = meta.get("mand_define") or ""
    massless = _massless_indices(particles)
    massive = _massive_indices(particles)
    n_in = int(meta.get("n_in") or 0)
    incoming = list(range(1, n_in + 1))
    outgoing = list(range(n_in + 1, np + 1))
    gamma_lines = _gamma_map_lines(particles)

    form_dir = ctx.prep_form_dir or ctx.run_dir / "form"
    (ctx.run_dir / "mathematica" / "Files").mkdir(parents=True, exist_ok=True)
    driver = form_dir / "Ioperator_master.frm"
    driver.write_text(
        _build_ioperator_master(
            incdir=incdir,
            np=np,
            n0l=n0l,
            mand_define=mand_define,
            massless=massless,
            massive=massive,
            incoming=incoming,
            outgoing=outgoing,
            gamma_lines=gamma_lines,
        ),
        encoding="utf-8",
    )
    return {"driver": driver, "form_dir": form_dir}


def prepare_total_lo(ctx: RunContext) -> Dict[str, Any]:
    if not ctx.run_dir:
        raise RuntimeError("No run attached.")

    meta_path = ctx.run_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    n0l = int(meta.get("n0l") or 0)
    if n0l <= 0:
        raise RuntimeError("n0l is 0: no tree amplitudes recorded.")

    form_dir = ctx.prep_form_dir or ctx.run_dir / "form"
    m0m0_dir = form_dir / "Files" / "M0M0"
    if not m0m0_dir.exists():
        raise FileNotFoundError(f"Missing M0M0 folder: {m0m0_dir}")

    procs_src = procedures_dir()
    incdir = form_dir / "procedures"
    ensure_symlink_or_copy(procs_src, incdir)

    math_dir = ctx.run_dir / "mathematica" / "Files" / "M0M0"
    math_dir.mkdir(parents=True, exist_ok=True)
    form_files_dir = form_dir / "Files" / "TotalLO"
    form_files_dir.mkdir(parents=True, exist_ok=True)
    driver = form_dir / "TotalLO.frm"

    text = f"""#-
#: IncDir {incdir}
#: SmallExtension 100M
#: MaxTermSize    10M
#: WorkSpace      1G
Off Statistics;
#define n0l "{n0l}"

#include declarations.h
    .sort
* load all M0M0 pieces
#do i=1,`n0l'
#do j=1,`n0l'
  #include Files/M0M0/d`i'x`j'.h
    .sort
#enddo
#enddo

L TotalLO =
#do i=1,`n0l'
#do j=1,`n0l'
 + d`i'x`j'
#enddo
#enddo
;
.sort
#call RationalFunction
#call toden
.sort
Format mathematica;
    .sort
#write <../mathematica/Files/M0M0/TotalLO.m> "TotalLO = (%E);\\n" TotalLO
    .sort
Format;
    .sort
#write <Files/TotalLO/TotalLO.h> "l TotalLO = (%E);\\n" TotalLO

    .end
"""
    driver.write_text(text, encoding="utf-8")
    return {
        "driver": driver,
        "form_dir": form_dir,
        "output_files": [math_dir / "TotalLO.m", form_files_dir / "TotalLO.h"],
    }

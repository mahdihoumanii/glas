# GLAS — General Loop Amplitude System

GLAS automates the generation and evaluation of loop amplitudes for collider processes, from diagram creation through symbolic reduction. It stitches together QGRAF, FORM, and Mathematica tooling to deliver reproducible, high-precision results. Use it to prototype, validate, and iterate on perturbative computations with minimal manual glue.

A video on how to use GLAS is given here: 
https://drive.google.com/file/d/1xFFeFzAeUpV_n_t7iYSmw0U3TrtDlvrC/view?usp=share_link

## Compatibility
Linus/MacOs

## Features
- Automated pipeline for generating and evaluating loop amplitudes from QGRAF topologies to FORM evaluation.
- Interactive REPL (`glas.py`) orchestrating generation, preparation, evaluation, and tensor/Dirac simplification steps.
- Built-in helpers for Dirac algebra, operator insertion, UV counterterms, and integral extraction.
- Ready-made commands for LO/NLO contractions, counterterm construction, and integral bookkeeping.
- Master integral coefficients are simplified by finding linear relations by employing finite field methods using FiniteFlow.

## Requirements
- Python 3 (with sympy for topology extension)
- FORM
- QGRAF
- wolframscript or Mathematica
- FeynCalc (Mathematica)
- Fermat
- Singular
- FiniteFlow (Mathematica)
- Kira
- blade

**Note**: MultivariateApart is bundled in `mathematica/scripts/` and auto-loaded by GLAS scripts—no separate installation needed.

## Quick start
- `python3 glas.py`
- `glas> generate g g > t t~`
- `glas> formprep`
- `glas> evaluate lo` / `evaluate nlo`
- `glas> DiracSimplify`
- `glas> contract lo` / `contract nlo`
- `glas> uvct`
- `glas> extract topologies` (with interactive parallel execution)
- `glas> ibp`

## Topology extraction & IBP reduction
The `extract topologies` command executes a 4-stage pipeline:

### Stage 1-2: Mathematica preprocessing
1. **Stage 1**: `extract_topologies_stage1.m` → Loads M0×M1 contractions, identifies incomplete topologies → `Files/Topologies.txt`
2. **Stage 2 (extend)**: `extend.py` → Completes propagator sets using SymPy → `Extended.m`
3. **Stage 2b**: `extract_topologies_stage2.m` → Topology mapping:
   - Outputs `Files/integrals.m` (Mathematica integral definitions)
   - Outputs `../form/Files/intrule.h` (FORM-formatted integral substitution rules)
   - Writes `Files/lenTopos.txt` with topology count (`ntop`), which is stored into `meta.json`

### Stage 3: Parallel FORM execution (ToTopos)
- **Interactive prompt**: After Mathematica stages complete, you'll be asked:
  ```
  [extract] Enter number of parallel jobs: 1 = serial, N = maximum parallelism
  [extract] Jobs (1-N):
  ```
- **Parallel chunking**: Generates `ToTopos_J{k}of{N}.frm` drivers that chunk tree-level diagrams across jobs
- **Output**: Produces scalar integrals in both formats:
  - `form/Files/M0M1top/d{i}x{j}.h` (FORM format)
  - `Mathematica/Files/M0M1top/d{i}x{j}.m` (Mathematica format)
- **Validation**: Checks that all `LoopInt`, `SPD`, and `lm1` symbols are eliminated

### IBP reduction
Run `glas> ibp` after topology extraction to perform integral reduction:
1. **mandIBP.m** → Computes Mandelstam variable replacements → `Files/mands.m`
2. **IBP.m** → Blade reduction with Fermat rationalization → `Files/IBP/IBP{i}.m` (Mathematica) and `../form/Files/IBP/IBP{i}.h` (FORM rules)
3. **SymmetryRelations.m** → PaVe conversion and master integral mapping:
   - `Files/SymmetryRelations.m` (Mathematica master integral definitions and PaVe mapping rules)
   - `../form/Files/SymmetryRelations.h` (FORM PaVe substitution rules)
   - `Files/lenMasters.txt` (master integral count, stored into `meta.json` as `nmis`)
   - `../form/Files/MastersToSym.h` (FORM symbolic substitution for master integrals: `mis1`, `mis2`, etc.)

All outputs auto-populate from `meta.json` kinematics. After IBP completion, `nmis` is available in meta.json for the `reduce` stage.

## Commands
- `generate <process>` — Generate diagrams with QGRAF and prepare FORM project
- `evaluate lo|nlo|mct` — Evaluate tree-level (lo), one-loop (nlo), or mass counterterm (mct) amplitudes
- `contract lo|nlo|mct` — Square amplitudes (M0×M0, M0×M1, etc.) with polarization sums
- `reduce [--jobs K]` — Apply IBP + symmetry reductions to M0M1top, producing M0M1Reduced (FORM + Mathematica outputs)
- `dirac [lo|nlo|both]` — Simplify Dirac traces with orthogonality constraints
- `uvct` — Compute UV counterterms (Vas, Vzt, Vg, Vm)
- `extract topologies` — 4-stage topology extraction with interactive parallel FORM execution (records `ntop`)
- `ibp` — Run IBP reduction pipeline (mandIBP → IBP → SymmetryRelations)
- `linrels` — Project and sum master coefficients using FiniteFlow (writes Files/MasterCoefficients.m)
- `ioperator` — Insert operators (experimental)
- `setrefs` — Set gluon polarization reference momenta
- `use <tag>|<run_name>` — Switch active run directory
- `runs [tag]` — List available runs

### Parallel execution
Most FORM commands support `--jobs K` to run K parallel jobs:
- `glas> evaluate nlo --jobs 8`
- `glas> contract lo --jobs 4`
- `glas> dirac both --jobs 4`
- `glas> reduce --jobs 4`

The `extract topologies` command prompts interactively for parallelism after Mathematica stages complete.

## Master coefficient relations (`linrels`)
- Prerequisites: run through `ibp` and `reduce` so that M0M1Reduced and master-integral metadata (`nmis`) exist.
- Command: `glas> linrels`
- What it does: copies and runs `mathematica/scripts/LinearRelations.m` inside the active run; uses FiniteFlow to find linear relations among rational functions, project master coefficients, and sum them across diagrams.
- Outputs: `Mathematica/Files/MasterCoefficients.m` plus per-master logs in `Mathematica/LinearRelations.{stdout,stderr}.log`.
- Dependencies: Mathematica/wolframscript with FiniteFlow available to the kernel.

## Notes
- `uvct` writes outputs into the `UVCT` folder as `Vas.m`, `Vzt.m`, `Vg.m`, and `Vm.m`.
- Parallel FORM jobs chunk diagrams via `chunk_range_1based()` to avoid empty chunks; effective jobs = `min(requested, n_diagrams)`.
- The `M0M1top` directory (generated by `extract topologies` Stage 3) must be preserved for IBP reduction and `reduce` command.
- **Metadata fields auto-populated during pipeline**:
  - `ntop` — Number of topologies (recorded by `extract topologies` from `lenTopos.txt`)
  - `nmis` — Number of master integrals (recorded by `ibp` from `lenMasters.txt`)
  - These are required for `reduce` to run correctly
- Environment variables:
  - `GLAS_FORM_PROCS` — Override FORM procedures directory
  - `GLAS_PYTHON` — Python executable for `extend.py` (must have sympy)
  - `FERMATPATH` — Fermat executable path (file or directory)
  - `SINGULARPATH` — Singular executable path (file or directory)

## Installation
- Automatic QGRAF setup: after `git clone`, run `make` then `make install` (requires `curl`, `tar`, `make`, and a Fortran compiler). This downloads QGRAF into `dependencies/` and copies the binary to `diagrams/qgraf` for GLAS.
- FeynCalc: https://feyncalc.github.io/ (Mathematica `PacletInstall["FeynCalc"];` or copy to `~/Library/Wolfram/Applications/FeynCalc`)
- FORM: https://www.nikhef.nl/~form/ (install; ensure `form` is on `PATH`; optional `GLAS_FORM_PROCS=/abs/path/to/formlib/procedures`)
- Mathematica/wolframscript: https://www.wolfram.com/mathematica/ (provide `wolframscript` or GUI for FeynCalc and post-processing)
- Fermat: https://home.bway.net/lewis/ (install; ensure `fer64`/`fermat` on `PATH`)
- Singular: https://www.singular.uni-kl.de/ (install; `Singular` on `PATH`)
- FeynCalc: https://feyncalc.github.io/ (install to `$UserBaseDirectory/Applications/FeynCalc` via `PacletInstall["FeynCalc"]` or manual copy)
- FiniteFlow: https://finiteflow.hepforge.org/ (install into Mathematica e.g. `$UserBaseDirectory/Applications/FiniteFlow`)
- Kira: https://gitlab.com/kira-pub/kira (build; add `kira` to `PATH`)
- blade: https://gitlab.com/multiloop-integrators/blade (build; add `blade` to `PATH`)
- QGRAF (manual alternative): https://qgraf.tecnico.ulisboa.pt/ (build yourself and place the binary in `diagrams/qgraf` if you prefer manual setup). The Makefile honors `QGRAF_URL` and `QGRAF_VERSION` if you need a different tarball.

## Path setup checklist
- Ensure `form`, `qgraf`, `fermat`/`fer64`, `Singular`, `kira`, and `blade` are on `PATH`.
- Set `FERMATPATH` to the Fermat executable or directory (or ensure `fer64` is on `PATH`).
- Set `SINGULARPATH` to the Singular executable or directory (or ensure `Singular` is on `PATH`).
- Install FeynCalc and FiniteFlow inside Mathematica (e.g., `$UserBaseDirectory/Applications`), and make sure `wolframscript` sees them.
- If using custom FORM procedures, set `GLAS_FORM_PROCS` to the absolute path of `formlib/procedures` (or keep the bundled default).
- For `extend.py` (topology extension), ensure Python has `sympy` installed; set `GLAS_PYTHON` if using a virtualenv.


## Future developments

- Removing extend.py and reduce mathematica dependence to the minimal.
- Adding FormFactor projection methods and full reconstruction via Finite Field methods.
- Solving the master integrals via differential equations in Epsilon factorised basis and systematic expansion. 

**Note**: MultivariateApart and FermatTools are already bundled in `mathematica/scripts/` and loaded automatically by GLAS Mathematica scripts—no separate installation required.

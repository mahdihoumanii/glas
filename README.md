# GLAS — General Loop Amplitude System

GLAS automates the generation and evaluation of loop amplitudes for collider processes, from diagram creation through symbolic reduction. It stitches together QGRAF, FORM, and Mathematica tooling to deliver reproducible, high-precision results. Use it to prototype, validate, and iterate on perturbative computations with minimal manual glue.

## Compatibility
Linus/MacOs

## Features
- Automated pipeline for generating and evaluating loop amplitudes from QGRAF topologies to FORM evaluation.
- Interactive REPL (`glas.py`) orchestrating generation, preparation, evaluation, and tensor/Dirac simplification steps.
- Built-in helpers for Dirac algebra, operator insertion, UV counterterms, and integral extraction.
- Ready-made commands for LO/NLO contractions, counterterm construction, and integral bookkeeping.

## Requirements
- Python 3
- FORM
- QGRAF
- wolframscript or Mathematica
- FeynCalc (Mathematica)
- Fermat
- Singular
- MultivariateApart
- FiniteFlow
- Kira
- blade

## Quick start
- `python3 glas.py`
- `glas> generate g g > t t~`
- `glas> formprep`
- `glas> evaluate`
- `glas> DiracSimplify`
- `glas> contractLO`, `glas> contractNLO`, `glas> UVCT`
- `glas> extract integrals`

## Commands
hello world 

## Notes
- `UVCT` writes outputs into the `UVCT` folder as `Vas.m`, `Vzt.m`, `Vg.m`, and `Vm.m`.

## Installation
- Automatic QGRAF setup: after `git clone`, run `make` then `make install` (requires `curl`, `tar`, `make`, and a Fortran compiler). This downloads QGRAF into `dependencies/` and copies the binary to `diagrams/qgraf` for GLAS.
- FeynCalc: https://feyncalc.github.io/ (Mathematica `PacletInstall["FeynCalc"];` or copy to `~/Library/Wolfram/Applications/FeynCalc`)
- FORM: https://www.nikhef.nl/~form/ (install; ensure `form` is on `PATH`; optional `GLAS_FORM_PROCS=/abs/path/to/formlib/procedures`)
- Mathematica/wolframscript: https://www.wolfram.com/mathematica/ (provide `wolframscript` or GUI for FeynCalc and post-processing)
- Fermat: https://home.bway.net/lewis/ (install; ensure `fer64`/`fermat` on `PATH`)
- Singular: https://www.singular.uni-kl.de/ (install; `Singular` on `PATH`)
- MultivariateApart: https://github.com/CeyhunEksili/MultivariateApart (install into Mathematica e.g. `$UserBaseDirectory/Applications/MultivariateApart`)
- FiniteFlow: https://finiteflow.hepforge.org/ (install into Mathematica e.g. `$UserBaseDirectory/Applications/MultivariateApart`)
- Kira: https://gitlab.com/kira-pub/kira (build; add `kira` to `PATH`)
- blade: https://gitlab.com/multiloop-integrators/blade (build; add `blade` to `PATH`)
- QGRAF (manual alternative): https://qgraf.tecnico.ulisboa.pt/ (build yourself and place the binary in `diagrams/qgraf` if you prefer manual setup). The Makefile honors `QGRAF_URL` and `QGRAF_VERSION` if you need a different tarball.

## Path setup checklist
- Ensure `form`, `qgraf`, `fermat`/`fer64`, `Singular`, `finiteflow`, `kira`, and `blade` are on `PATH`.
- Set `FERMATPATH` to the directory containing `fer64` (or place `fer64` on `PATH`).
- Install FeynCalc, MultivariateApart inside Mathematica (e.g., `$UserBaseDirectory/Applications`), and make sure `wolframscript` sees them.
- If using custom FORM procedures, set `GLAS_FORM_PROCS` to the absolute path of `formlib/procedures` (or keep the bundled default).

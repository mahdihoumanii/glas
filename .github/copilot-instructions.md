# GLAS — General Loop Amplitude System

GLAS is a specialized HEP (High Energy Physics) workflow orchestrator that automates loop amplitude calculations by stitching together QGRAF (diagram generation), FORM (symbolic manipulation), and Mathematica (topology extraction/IBP reduction).

## Architecture

### Three-Phase Pipeline
1. **Generation** (`generate`) → Creates Feynman diagrams via QGRAF, outputs to `runs/{tag}_{nnnn}/diagrams/{0l,1l}/`
2. **Preparation** (`formprep`) → Copies diagrams to `form/Files/`, writes chunked FORM driver scripts for parallel execution
3. **Evaluation** (`evaluate`, `contract`, `uvct`) → Executes FORM scripts in parallel, outputs symbolic results to `form/Files/Amps/`

### Run-Based Workflow
- All work happens inside **run directories** at `runs/{tag}_{nnnn}/` (e.g., `runs/ggtT_0001/`)
- Each run has `meta.json` storing process definition, diagram counts (`n0l`, `n1l`), kinematics (`mand_define`), and job configuration
- The REPL maintains a `RunContext` tracking the active run directory and preparation state
- Commands like `use {tag}` or `use {run_name}` switch active runs; `runs [tag]` lists available runs

### FORM Integration Pattern
- **Procedures directory**: `resources/formlib/procedures/` (or override with `GLAS_FORM_PROCS` env var)
- All FORM drivers include `#: IncDir procedures` and call procedures like `#call DiracSimplify`, `#call FeynmanRules`
- Procedures are symlinked/copied into `form/procedures` during `formprep`
- **Parallel execution**: Jobs split diagram ranges via `chunk_range_1based(total, jobs, job_index)`, each writes `form_{tag}.stdout.log` and `form_{tag}.stderr.log`
- Driver naming: `{operation}_{mode}_J{k}of{N}.frm` (e.g., `eval_lo_J1of4.frm`, `contractNLO_J2of8.frm`)

### Gluon Polarization References
- External gluons require polarization vectors stored in `GluonRefs` (managed via `setrefs` command)
- Stored in `meta.json` under `gluon_refs` as `{"p1": "reference_momentum", ...}`
- Automatically prompted when missing during `contract` or `ioperator` commands
- Used to generate `#call PolarizationSums` blocks in FORM drivers

## Key Commands

### Standard Workflow
```bash
glas> generate g g > t t~ --jobs 8     # QGRAF generation + formprep
glas> evaluate lo --jobs 8              # Tree-level Feynman rules + kinematics
glas> evaluate nlo --jobs 8 --dirac     # Loop-level + optional Dirac simplification
glas> contract lo --jobs 4              # Square tree amplitudes (M0×M0)
glas> contract nlo --jobs 4             # Tree×loop interference (M0×M1)
glas> uvct                              # UV counterterms (Vas, Vzt, Vg)
glas> extract topologies                # Topology extraction: stages 1-2 (Mathematica) + stage 3 (FORM, parallel)
glas> ibp                               # IBP reduction via Blade/MultivariateApart
```

### Topology Extraction & IBP Pipeline
- **extract topologies** (4 stages total):
  1. Stage 1: `extract_topologies_stage1.m` → Loads M0M1, finds incomplete topologies → `Files/Topologies.txt`
  2. Stage 2: `extend.py` → Completes propagator sets → `Extended.m`
  3. Stage 2b: `extract_topologies_stage2.m` → Topology mapping, outputs:
     - `Files/integrals.m` — integral definitions in Mathematica format (integrals, glis, Topologies, intrule)
     - `../form/Files/intrule.h` — FORM-formatted integral rules via FormString conversion
       - FormString converts GLI notation to FORM syntax: `GLI[top1,{1,0,1,0}]` → `GLI(top1,1,0,1,0)`
       - Each intrule written as FORM `id` statement for substitution in FORM drivers
  4. **Stage 3 (Parallel FORM)**: `ToTopos.frm` drivers (parallel execution)
     - User prompted for number of parallel jobs after stage 2b completion (1 = serial, N = N parallel jobs)
     - Generates `ToTopos_J{k}of{N}.frm` drivers chunking M0×M1 contractions across jobs
     - Each job processes diagrams i0..i1 for all loop integrals j=1..n1l
     - Substitutes `intrule.h` and formats topologies to scalar integrals
     - Output structure:
       - `form/Files/M0M1top/d{i}x{j}.h` — FORM-formatted scalar integrals
       - `Mathematica/Files/M0M1top/d{i}x{j}.m` — Mathematica-formatted scalar integrals
     - Validates: checks that all `LoopInt`, `SPD`, and `lm1` symbols are eliminated
     - **Note**: `M0M1top` directory must be preserved for IBP stage usage

- **ibp** (3 stages):
  1. `mandIBP.m` → Computes Mandelstam replacements → `Files/mands.m`
  2. `IBP.m` → Blade reduction + FORM header generation, outputs:
     - `Files/IBP/IBP{i}.m` — Mathematica IBP reduction results for each topology (BL notation)
     - `../form/Files/IBP/IBP{i}.h` — FORM-formatted IBP rules via FormString conversion
       - FormString converts BL notation to GLI, then to FORM syntax: `BL[top1,{1,0,1,0}]` → `GLI(top1,1,0,1,0)`
       - Each reduction rule written as FORM `id` statement for mass restoration in FORM drivers
     - RestoreMass function applies Fermat/Singular rationalization to restore mass dimensions
  3. `SymmetryRelations.m` → PaVe conversion + topology → PaVe mapping rules, outputs:
     - `Files/SymmetryRelations.m` — Master integrals and PaVe rules in Mathematica format (MastersPaVe, PaVeRules, Masters, pentRep)
     - `../form/Files/SymmetryRelations.h` — FORM-formatted PaVe substitution rules via FormString conversion
       - FormString converts BL notation to GLI, then to FORM syntax: `BL[top1,{1,0,1,0}]` → `GLI(top1,1,0,1,0)`
       - Each PaVe rule written as FORM `id` statement for final amplitude reduction


### Mode Hierarchy
- **lo**: Tree-level (0-loop) diagrams from `Files/{tag}0l`
- **nlo**: One-loop (1-loop) diagrams from `Files/{tag}1l`
- **mct**: Mass counterterm diagrams (special tree-level treatment)

### Job Control
- `--jobs K` overrides job count (clamped to diagram count to avoid empty chunks)
- Jobs stored in `meta.json` as `jobs_requested` and `jobs_effective`
- Effective jobs: `min(jobs_requested, n_diagrams)` to prevent empty chunks
- **extract topologies**: Stage 3 (ToTopos) prompts user for parallel job count interactively

## Project Structure

```
glas.py                     # Entry point → glaslib.cli.main()
glaslib/
  cli.py                    # REPL shell (cmd.Cmd subclass)
  generate_diagrams.py      # QGRAF wrapper + formprep logic
  qgraf.py                  # High-level generate_run() interface
  formprep.py               # prepare_form() → calls generate_diagrams.prepare_form_project()
  contracts/{lo,nlo,mct}.py # Amplitude contraction drivers
  counterterms.py           # Mass counterterm logic (detects gs^N power)
  dirac.py                  # DiracSimplify driver generation with orthogonality constraints
  ioperator.py              # Operator insertion (experimental)
  extTopos.py               # Python topology extension (sympy-based)
  topoformat.py             # Parallel ToTopos driver generation for topology formatting
  core/
    run_manager.py          # RunContext, list_runs(), meta.json handling
    parallel.py             # run_jobs() → ThreadPoolExecutor for FORM tasks
    paths.py                # project_root(), procedures_dir(), runs_dir()
    refs.py                 # GluonRefs management
  commands/                 # REPL command implementations
resources/
  formlib/procedures/       # FORM procedures (.prc, declarations.h)
  diagrams/                 # QGRAF binary, mystyle.sty
mathematica/scripts/        # FeynCalc topology extraction scripts
runs/                       # Active run directories
```

## Development Patterns

### Adding New Commands
1. Implement in `glaslib/commands/{name}.py` with `run(state: AppState, arg: str)` signature
2. Add `do_{name}` method to `GlasShell` in `glaslib/cli.py`
3. Use `state.ensure_run()` to validate active run before proceeding
4. Follow parallel execution pattern: prepare drivers → `run_jobs()` → report success

### Metadata Conventions
- Always read/write `meta.json` for state persistence (process, n0l, n1l, jobs, gluon_refs)
- Use `json.loads(path.read_text())` for loading, update via dict merge
- Critical fields: `process`, `tag`, `n0l`, `n1l`, `mand_define`, `particles`, `gluon_refs`

### Path Resolution
- Use `project_root()` or `runs_dir()` from `glaslib.core.paths` for base paths
- Run-relative paths: `ctx.run_dir / "form" / "Files" / "Amps" / ...`
- Never hardcode absolute paths—use `Path.resolve()` only for debugging

## External Dependencies

### Required on PATH
- `form` — FORM executable (https://www.nikhef.nl/~form/)
- `qgraf` — Automatically installed via `make install` to `resources/diagrams/qgraf`
- `wolframscript` — For FeynCalc topology extraction (Mathematica backend)
- `fer64`/`fermat` — Fermat algebra system (set `FERMATPATH` if not on PATH)
- `Singular` — Computer algebra system for Groebner basis (set `SINGULARPATH` if not on PATH)
- `kira`, `blade` — For IBP reduction (post-FORM steps)

### Mathematica Packages
- FeynCalc (Paclet or manual install to `~/Library/Wolfram/Applications/FeynCalc`)
- MultivariateApart, FiniteFlow (bundled; see `mathematica/scripts/MultivariateApart.wl`)
- Blade (for IBP reduction, install to `$UserBaseDirectory/Applications`)
- FermatTools (bundled; see `mathematica/scripts/FermatTools.wl`)
- Both FermatTools.wl and MultivariateApart.wl support environment-aware tool resolution

### Fermat Configuration
- Set Fermat path via environment: `export FERMATPATH="/path/to/fer64"` (file or directory)
- Or in Mathematica: `FermatTools`SetFermatPath["/path/to/fer64"]`
- Falls back to `fer64` on PATH if neither is set
- IBP.m automatically loads FermatTools.wl for rationalization

### Singular Configuration
- Set Singular path via environment: `export SINGULARPATH="/opt/homebrew/bin/Singular"` (file or directory)
- Or in Mathematica: `MultivariateApart`SetSingularPath["/path/to/Singular"]`
- Falls back to `Singular` on PATH if neither is set
- MultivariateApart.wl provides partial fraction decomposition with environment-aware path resolution
- Used by IBP.m for rational function simplification via `MultivariatePassToSingular[]`

### Environment Variables
- `GLAS_FORM_PROCS` — Override procedures directory (default: `resources/formlib/procedures`)
- `GLAS_PYTHON` — Python executable for `extend.py` (must have sympy)
- `FERMATPATH` — Fermat executable path (file or directory; falls back to PATH)
- `SINGULARPATH` — Singular executable path (file or directory; falls back to PATH)

## Critical Conventions

### Diagram Numbering
- FORM diagrams: 1-indexed (`d1, d2, ..., d{n0l}` for tree; `d1, ..., d{n1l}` for loop)
- Chunks: Job `k` of `N` handles range `[i0, i1]` computed via `chunk_range_1based(total, N, k)`

### Mandelstam Variables
- Process-dependent `mand_define` stored in `meta.json` (e.g., `#call mandelstam2x3(p1,p2,p3,p4,p5,...)`)
- Auto-generated from process tokens by `_build_mand_define()` in `generate_diagrams.py`

### Mass Conventions
- Symbolic masses: `mt` (top quark), others inferred from particle tokens (`t` → `mt`, else `0`)
- Defined in FORM via `S mt;` in `declarations.h`

### Process Tag Generation
- Process `g g > t t~` → tag `ggtT` (concatenate particle symbols, capitalize antiparticles)
- Run directories: `{tag}_{nnnn}` with zero-padded counter (e.g., `ggtT_0001`)

## Testing & Debugging

### Smoke Test
```bash
cd resources/tools
python smoke_test.py --process "g g > t t~" [--dirac] [--keep]
```
Runs full pipeline (generate → formprep → evaluate → optional DiracSimplify) in temp run, cleans up unless `--keep`.

### Log Inspection
- FORM logs: `{run_dir}/form/form_{tag}.{stdout|stderr}.log`
- Check `.log` files when `run_jobs()` reports failures

### Mathematica Patterns
- **Directory setting for batch execution**: Use `If[$FrontEnd === Null, $InputFileName, NotebookFileName[]] // DirectoryName // SetDirectory;`
  - Handles both interactive sessions and `wolframscript` execution
  - Ensures relative paths work correctly regardless of execution context
- **FormString conversion** (GLI↔FORM notation): Converts Mathematica GLI to FORM-compatible syntax
  ```mathematica
  FormString[expr_]:= StringReplace[ToString[expr/. GLI[a_,b_]:> GLI[ToExpression[a],Sequence@@b], InputForm],
    {"["-> "(","]"-> ")",WhitespaceCharacter-> ""}]
  ```
  - Used in `extract_topologies_stage2.m` to write `../form/Files/intrule.h`
  - Converts `GLI[top1,{1,0,1,0}]` → `GLI(top1,1,0,1,0)` for FORM `id` statements
  - Each integral rule written as: `id GLI(topN,i1,i2,...) = expr;`
- **FormString conversion** (BL↔FORM notation): Converts Blade integral notation to FORM-compatible syntax
  ```mathematica
  FormString[expr_]:= StringReplace[ToString[expr/. BL[a_, b_]:> GLI[a, Sequence@@b], InputForm],
    {"["-> "(","]"-> ")",WhitespaceCharacter-> ""}]
  ```
  - Used in `IBP.m` to write `../form/Files/IBP/IBP{i}.h`
  - Converts `BL[top1,{1,0,1,0}]` → `GLI(top1,1,0,1,0)` for FORM `id` statements
  - Each IBP reduction rule written as: `id BL(topN,i1,i2,...) = expr;`

### Common Issues
- **Missing procedures**: Ensure `resources/formlib/procedures/` exists or set `GLAS_FORM_PROCS`
- **Empty chunks**: Indicates `jobs_effective` miscalculation—check `chunk_range_1based()` logic
- **Gluon ref prompts**: Run `setrefs` to populate `gluon_refs` in `meta.json` before `contract`

## Anti-Patterns

❌ Don't hardcode run directory names—always use `ctx.run_dir`  
❌ Don't call FORM directly with `subprocess.run()`—use `run_jobs()` for logging/parallelism  
❌ Don't skip `formprep`—it copies diagrams and writes driver scripts  
❌ Don't modify `meta.json` manually—use `update_meta()` or merge dicts in code  
❌ Don't assume `jobs_requested == jobs_effective`—always clamp to diagram count

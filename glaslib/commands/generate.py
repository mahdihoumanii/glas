from __future__ import annotations

from glaslib.commands.common import AppState, clamp_jobs, parse_generate_args, update_meta
from glaslib.core.paths import diagrams_dir, project_root, qgraf_exe, runs_dir, style_file
from glaslib.formprep import prepare_form
from glaslib.qgraf import generate_run


def run(state: AppState, arg: str) -> None:
    try:
        process_str, jobs, run_name, resume = parse_generate_args(arg)
    except Exception as exc:
        print(f"Error: {exc}")
        print("Usage: generate q q~ > t t~ --jobs 8 [--run NAME] [--resume]")
        return

    if not process_str:
        print("Usage: generate q q~ > t t~ --jobs 8 [--run NAME] [--resume]")
        return

    jobs_req = max(1, int(jobs or 1))
    if resume and not run_name:
        print("Error: --resume requires --run NAME.")
        return

    try:
        if run_name:
            run_dir = runs_dir() / run_name
            if run_dir.exists():
                if not resume:
                    print(f"Error: run '{run_name}' already exists. Use --resume to attach.")
                    return
                state.ctx.attach(run_dir)
                state.refs().load_from_meta()
            else:
                if resume:
                    print(f"Error: run '{run_name}' does not exist to resume.")
                    return
                out = generate_run(
                    process_str,
                    root=project_root(),
                    tools_dir=diagrams_dir(),
                    qgraf_exe=qgraf_exe(),
                    style_file=style_file(),
                    model=state.model,
                    keep_temp=state.keep_temp,
                    out_name=run_name,
                )
                state.ctx.attach(out["output_dir"])
                state.refs().load_from_meta()
        else:
            out = generate_run(
                process_str,
                root=project_root(),
                tools_dir=diagrams_dir(),
                qgraf_exe=qgraf_exe(),
                style_file=style_file(),
                model=state.model,
                keep_temp=state.keep_temp,
            )
            state.ctx.attach(out["output_dir"])
            state.refs().load_from_meta()

        if not state.ctx.run_dir:
            print("Error: no run directory attached.")
            return

        prepare_form(state.ctx, jobs=jobs_req)

        n_diagrams = max(1, max(int(state.ctx.meta.get("n0l") or 0), int(state.ctx.meta.get("n1l") or 0)))
        jobs_req, jobs_eff = clamp_jobs(jobs_req, n_diagrams)
        meta = update_meta(state.ctx.run_dir, {"jobs_requested": jobs_req, "jobs_effective": jobs_eff})
        state.ctx.meta = meta

        print("[generate] OK")
        print(f"  process    : {process_str}")
        print(f"  output_dir : {state.ctx.run_dir}")
        print(f"  jobs req   : {jobs_req}")
        print(f"  jobs eff   : {jobs_eff}")
    except Exception as exc:
        print(f"Error: {exc}")

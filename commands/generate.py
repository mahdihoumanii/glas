from __future__ import annotations

from glas.commands.common import AppState, clamp_jobs, parse_generate_args, update_meta
from glaslib.formprep import prepare_form
from glaslib.qgraf import generate_run


def run(state: AppState, arg: str) -> None:
    try:
        process_str, jobs = parse_generate_args(arg)
    except Exception as exc:
        print(f"Error: {exc}")
        print("Usage: generate q q~ > t t~ --jobs 8")
        return

    if not process_str:
        print("Usage: generate q q~ > t t~ --jobs 8")
        return

    jobs_req = max(1, int(jobs or 1))

    try:
        out = generate_run(
            process_str,
            root=state.config.root,
            tools_dir=state.config.tools_dir,
            qgraf_exe=state.config.qgraf_exe,
            style_file=state.config.style_file,
            model=state.config.model,
            keep_temp=state.config.keep_temp,
        )
        state.ctx.attach(out["output_dir"])
        state.load_gluon_refs_from_meta()

        prepare_form(state.ctx, jobs=jobs_req)

        n_diagrams = max(1, max(int(out.get("n0l") or 0), int(out.get("n1l") or 0)))
        jobs_req, jobs_eff = clamp_jobs(jobs_req, n_diagrams)
        meta = update_meta(state.ctx.run_dir, {"jobs_requested": jobs_req, "jobs_effective": jobs_eff})  # type: ignore[arg-type]
        state.ctx.meta = meta

        print("[generate] OK")
        print(f"  process    : {process_str}")
        print(f"  output_dir : {out['output_dir']}")
        print(f"  tree file  : {out['tree_main'].name}   (n0l={out['n0l']})")
        print(f"  loop file  : {out['loop_main'].name}   (n1l={out['n1l']})")
        print(f"  jobs req   : {jobs_req}")
        print(f"  jobs eff   : {jobs_eff}")
    except Exception as exc:
        print(f"Error: {exc}")

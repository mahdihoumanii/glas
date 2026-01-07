from __future__ import annotations

from typing import Any, Dict

from glaslib.generate_diagrams import prepare_form_project
from glaslib.core.run_manager import RunContext


def prepare_form(ctx: RunContext, jobs: int) -> Dict[str, Any]:
    if not ctx.run_dir:
        raise RuntimeError("No run attached.")

    out = prepare_form_project(ctx.run_dir, jobs=jobs)

    ctx.prep_jobs_requested = out["jobs_requested"]
    ctx.prep_jobs_effective = out.get("jobs_effective", ctx.prep_jobs_requested)
    ctx.prep_form_dir = out["evaluate"].get("form_dir") or out.get("form_dir")

    return out

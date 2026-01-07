from __future__ import annotations

from typing import Dict

from glaslib.contractLO import prepare_contractLO_project
from glaslib.core.run_manager import RunContext


def prepare_lo(ctx: RunContext, gluon_refs: Dict[str, str], jobs: int):
    if not ctx.run_dir:
        raise RuntimeError("No run attached.")
    return prepare_contractLO_project(ctx.run_dir, gluon_refs=gluon_refs, jobs=jobs)

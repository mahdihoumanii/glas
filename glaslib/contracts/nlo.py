from __future__ import annotations

from typing import Dict

from glaslib.contractNLO import prepare_contractNLO_project
from glaslib.core.run_manager import RunContext


def prepare_nlo(ctx: RunContext, gluon_refs: Dict[str, str], jobs: int):
    if not ctx.run_dir:
        raise RuntimeError("No run attached.")
    return prepare_contractNLO_project(ctx.run_dir, gluon_refs=gluon_refs, jobs=jobs)

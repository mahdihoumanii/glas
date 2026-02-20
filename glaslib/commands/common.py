from __future__ import annotations

import json
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from glaslib.core.refs import GluonRefs
from glaslib.core.run_manager import RunContext
from glaslib.core.models import get_default_model_id, get_model_by_id, get_feynman_rules_prc, get_qgraf_model


MODES = ("lo", "nlo", "mct")


@dataclass
class AppState:
    ctx: RunContext
    form_exe: str = "form"
    model_id: str = field(default_factory=get_default_model_id)
    keep_temp: bool = False
    verbose: bool = False
    gluon_refs: Optional[GluonRefs] = None

    @property
    def model(self) -> str:
        """QGRAF model file name for diagram generation."""
        return get_qgraf_model(self.get_effective_model_id())

    def ensure_run(self) -> bool:
        return self.ctx.require_run()

    def refs(self) -> GluonRefs:
        if self.gluon_refs is None:
            self.gluon_refs = GluonRefs(self.ctx)
        return self.gluon_refs

    def get_effective_model_id(self) -> str:
        """
        Get the effective model_id for the current run.

        Priority:
        1. Run-specific model_id from meta.json
        2. Global model_id from AppState
        """
        if self.ctx.meta:
            run_model = self.ctx.meta.get("model_id")
            if run_model:
                return run_model
        return self.model_id

    def get_feynman_rules_file(self) -> str:
        """Get the Feynman rules procedure filename for the effective model."""
        return get_feynman_rules_prc(self.get_effective_model_id())


def parse_generate_args(arg: str) -> Tuple[str, Optional[int], Optional[str], bool]:
    toks = shlex.split(arg)
    process: List[str] = []
    jobs: Optional[int] = None
    run_name: Optional[str] = None
    resume = False
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == "--jobs":
            if i + 1 >= len(toks):
                raise ValueError("Missing value after --jobs")
            jobs = int(toks[i + 1])
            i += 2
            continue
        if t == "--run":
            if i + 1 >= len(toks):
                raise ValueError("Missing value after --run")
            run_name = toks[i + 1]
            i += 2
            continue
        if t == "--resume":
            resume = True
            i += 1
            continue
        process.append(t)
        i += 1
    return " ".join(process).strip(), jobs, run_name, resume


def parse_mode_and_flags(arg: str, *, allow_dirac: bool = False) -> Tuple[Optional[str], Optional[int], bool, bool]:
    """
    Parse command arguments for mode and flags.

    Returns:
        (mode, jobs, dirac, verbose)
    """
    toks = shlex.split(arg)
    mode: Optional[str] = None
    jobs: Optional[int] = None
    dirac = False
    verbose = False
    quiet = False
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == "--jobs":
            if i + 1 >= len(toks):
                raise ValueError("Missing value after --jobs")
            jobs = int(toks[i + 1])
            i += 2
            continue
        if allow_dirac and t == "--dirac":
            dirac = True
            i += 1
            continue
        if t == "--verbose":
            verbose = True
            i += 1
            continue
        if t == "--quiet":
            quiet = True
            i += 1
            continue
        if not t.startswith("-") and mode is None:
            mode = t.lower()
        i += 1
    # --quiet wins over --verbose
    if quiet:
        verbose = False
    return mode, jobs, dirac, verbose


def parse_simple_flags(arg: str) -> Tuple[str, bool]:
    """
    Parse simple command arguments for --verbose/--quiet flags.

    Returns:
        (remaining_arg, verbose)
    """
    toks = shlex.split(arg)
    verbose = False
    quiet = False
    remaining = []
    for t in toks:
        if t == "--verbose":
            verbose = True
        elif t == "--quiet":
            quiet = True
        else:
            remaining.append(t)
    if quiet:
        verbose = False
    return " ".join(remaining), verbose


def parse_pick_flag(arg: str) -> Tuple[str, bool, bool]:
    """
    Parse arguments with --pick and --verbose flags.

    Returns:
        (remaining_arg, pick, verbose)
    """
    toks = shlex.split(arg)
    pick = False
    verbose = False
    quiet = False
    args = []
    for t in toks:
        if t == "--pick":
            pick = True
        elif t == "--verbose":
            verbose = True
        elif t == "--quiet":
            quiet = True
        elif not t.startswith("--"):
            args.append(t)
    if quiet:
        verbose = False
    return " ".join(args), pick, verbose


def update_meta(run_dir: Path, updates: Dict[str, object]) -> Dict[str, object]:
    meta_path = Path(run_dir) / "meta.json"
    meta: Dict[str, object] = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update(updates)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def clamp_jobs(requested: Optional[int], total: int) -> Tuple[int, int]:
    jobs_req = max(1, int(requested or 1))
    jobs_eff = max(1, min(jobs_req, max(1, total)))
    return jobs_req, jobs_eff

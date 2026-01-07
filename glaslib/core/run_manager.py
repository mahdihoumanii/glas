from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from glaslib.core.paths import runs_dir
from glaslib.generate_diagrams import parse_process, process_to_tag


RUN_RE = re.compile(r"^([A-Za-z0-9]+)_(\d{4,})$")


def extract_suffix(p: Path) -> int:
    m = RUN_RE.match(p.name)
    if not m:
        return -1
    try:
        return int(m.group(2))
    except ValueError:
        return -1


def list_runs(tag: Optional[str] = None) -> List[Path]:
    base = runs_dir()
    runs: List[Path] = []
    for p in base.iterdir():
        if not p.is_dir():
            continue
        m = RUN_RE.match(p.name)
        if not m:
            continue
        if tag and m.group(1) != tag:
            continue
        if (p / "meta.json").exists():
            runs.append(p)
    runs.sort(key=extract_suffix, reverse=True)
    return runs


def resolve_tag_from_process_or_tag(arg: str) -> str:
    try:
        lhs, rhs = parse_process(arg)
        return process_to_tag(lhs, rhs)
    except Exception:
        return arg.strip()


def load_meta(run_dir: Path) -> Dict[str, Any]:
    meta_path = Path(run_dir) / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in {run_dir}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def pick_run_interactive(runs: List[Path]) -> Optional[Path]:
    if not runs:
        return None
    print("[use] Matching runs:")
    for idx, p in enumerate(runs, 1):
        meta = load_meta(p)
        created = meta.get("created_at_utc", "?")
        print(f"{idx}. {p.name} (created_at_utc={created})")
    sel = input("Select run number: ").strip()
    if not sel.isdigit():
        return None
    i = int(sel)
    if not (1 <= i <= len(runs)):
        return None
    return runs[i - 1]


@dataclass
class RunContext:
    run_dir: Optional[Path] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    prep_jobs_requested: int = 1
    prep_jobs_effective: int = 1
    prep_form_dir: Optional[Path] = None

    def reset_prepared(self) -> None:
        self.prep_jobs_requested = 1
        self.prep_jobs_effective = 1
        self.prep_form_dir = None

    @property
    def process(self) -> Optional[str]:
        return self.meta.get("process")

    @property
    def tag(self) -> Optional[str]:
        return self.meta.get("tag")

    @property
    def n0l(self) -> int:
        return int(self.meta.get("n0l") or 0)

    @property
    def n1l(self) -> int:
        return int(self.meta.get("n1l") or 0)

    def attach(self, run_dir: Path) -> None:
        run_dir = Path(run_dir).resolve()
        meta = load_meta(run_dir)
        self.run_dir = run_dir
        self.meta = meta
        self.reset_prepared()
        print(f"[use] Attached to: {run_dir}")

    def require_run(self) -> bool:
        if not self.run_dir:
            print("Error: no run attached. Use 'generate' or 'use' first.")
            return False
        return True

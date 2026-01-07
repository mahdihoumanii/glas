from __future__ import annotations

import json
import shlex
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from glas.config import GlasConfig
from glaslib.runs import RunContext


MODES = ("lo", "nlo", "mct")


@dataclass
class AppState:
    config: GlasConfig
    ctx: RunContext
    gluon_refs: Dict[str, str] = field(default_factory=dict)

    def ensure_run(self) -> bool:
        return self.ctx.require_run()

    def load_gluon_refs_from_meta(self) -> None:
        if not self.ctx.run_dir:
            return
        meta = self.ctx.meta or {}
        stored = meta.get("gluon_refs")
        if isinstance(stored, dict) and stored:
            self.gluon_refs = {str(k): str(v) for k, v in stored.items()}

    def save_gluon_refs_to_meta(self) -> None:
        if not self.ctx.run_dir:
            return
        meta_path = self.ctx.run_dir / "meta.json"
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        meta["gluon_refs"] = self.gluon_refs
        meta["gluon_refs_saved_at_utc"] = datetime.now(timezone.utc).isoformat()
        meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        self.ctx.meta = meta

    def get_or_prompt_gluon_refs(self, process_str: str) -> Dict[str, str]:
        if self.gluon_refs:
            return self.gluon_refs
        meta_refs = self.ctx.meta.get("gluon_refs") if isinstance(self.ctx.meta, dict) else None
        if isinstance(meta_refs, dict) and meta_refs:
            self.gluon_refs = {str(k): str(v) for k, v in meta_refs.items()}
            return self.gluon_refs
        refs = _ask_gluon_refs_if_needed(process_str)
        if refs:
            self.gluon_refs = refs
            self.save_gluon_refs_to_meta()
        return refs

    def force_refresh_gluon_refs(self, process_str: str) -> Dict[str, str]:
        self.gluon_refs = {}
        refs = _ask_gluon_refs_if_needed(process_str)
        self.gluon_refs = refs
        self.save_gluon_refs_to_meta()
        return refs


def parse_generate_args(arg: str) -> Tuple[str, Optional[int]]:
    toks = shlex.split(arg)
    process: List[str] = []
    jobs: Optional[int] = None
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == "--jobs":
            if i + 1 >= len(toks):
                raise ValueError("Missing value after --jobs")
            jobs = int(toks[i + 1])
            i += 2
            continue
        process.append(t)
        i += 1
    return " ".join(process).strip(), jobs


def parse_mode_and_flags(arg: str, *, allow_dirac: bool = False) -> Tuple[Optional[str], Optional[int], bool]:
    toks = shlex.split(arg)
    mode: Optional[str] = None
    jobs: Optional[int] = None
    dirac = False
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
        if not t.startswith("-") and mode is None:
            mode = t.lower()
        i += 1
    return mode, jobs, dirac


def parse_pick_flag(arg: str) -> Tuple[str, bool]:
    toks = shlex.split(arg)
    pick = False
    args = []
    for t in toks:
        if t == "--pick":
            pick = True
            continue
        if t.startswith("--"):
            continue
        args.append(t)
    return " ".join(args), pick


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


def _split_process(process_str: str) -> Tuple[List[str], List[str]]:
    s = process_str.strip()
    if "->" in s:
        lhs, rhs = s.split("->", 1)
    elif ">" in s:
        lhs, rhs = s.split(">", 1)
    else:
        raise ValueError("Process must contain '>' or '->'")
    lhs_tokens = [t.strip() for t in lhs.strip().split() if t.strip()]
    rhs_tokens = [t.strip() for t in rhs.strip().split() if t.strip()]
    return lhs_tokens, rhs_tokens


def _is_massless(tok: str) -> bool:
    t = tok.lower()
    return t in ("q", "q~", "qbar", "g")


def _collect_gluons_and_default_ref(process_str: str) -> Tuple[List[str], str, List[str], List[str]]:
    lhs, rhs = _split_process(process_str)
    tokens = [t.lower() for t in (lhs + rhs)]
    all_momenta = [f"p{i}" for i in range(1, len(tokens) + 1)]

    default_ref = "p1"
    for tok, mom in zip(tokens, all_momenta):
        if _is_massless(tok):
            default_ref = mom
            break

    gluon_momenta = [mom for tok, mom in zip(tokens, all_momenta) if tok == "g"]
    return gluon_momenta, default_ref, all_momenta, tokens


def _normalize_ref_input(s: str) -> str:
    s = s.strip()
    if not s:
        return ""
    if s.isdigit():
        return f"p{s}"
    return s


def _ask_gluon_refs_if_needed(process_str: str) -> Dict[str, str]:
    gluon_moms, default_ref, all_moms, tokens = _collect_gluons_and_default_ref(process_str)

    if len(gluon_moms) <= 1:
        if len(gluon_moms) == 1:
            print("[polarization] Exactly 1 gluon -> using -d_(mu1,mu2) sum (no refs needed).")
        return {}

    print("[polarization] Gluon reference vectors / orthogonality choices")
    print(f"  process     : {process_str}")
    print(f"  gluons @    : {', '.join(gluon_moms)}")
    print(f"  default ref : {default_ref} (first massless momentum)")
    print("  Tip: enter '2' for p2, or 'p2'. Empty -> default.\n")

    gluon_refs: Dict[str, str] = {}
    for gm in gluon_moms:
        while True:
            ans = input(f"Vector orthogonal to gluon {gm} [default {default_ref}]: ")
            ans = _normalize_ref_input(ans)
            ref = ans if ans else default_ref

            if ref not in all_moms:
                print(f"  Invalid: {ref}. Allowed: {', '.join(all_moms)}")
                continue

            ref_tok = tokens[all_moms.index(ref)]
            if not _is_massless(ref_tok):
                print(f"  Warning: {ref} corresponds to '{ref_tok}' (not massless). Using it anyway.")

            gluon_refs[gm] = ref
            break

    return gluon_refs

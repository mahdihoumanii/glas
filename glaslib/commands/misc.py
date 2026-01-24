from __future__ import annotations

import json
import shutil
from pathlib import Path

from glaslib.commands.common import AppState, parse_pick_flag
import shlex

from glaslib.commands import evaluate, generate, uvct
from glaslib.core.paths import qgraf_exe, procedures_dir, runs_dir
from glaslib.core.run_manager import RunContext, list_runs, pick_run_interactive, resolve_tag_from_process_or_tag


def runs(state: AppState, arg: str) -> None:
    target = arg.strip()
    tag = resolve_tag_from_process_or_tag(target) if target else None
    candidates = list_runs(tag=tag)
    if not candidates:
        if tag:
            print(f"[runs] No runs found for tag/process '{tag}'.")
        else:
            print("[runs] No runs found.")
        return
    for p in candidates:
        meta = json.loads((p / "meta.json").read_text(encoding="utf-8"))
        created = meta.get("created_at_utc", "?")
        n0l = meta.get("n0l")
        n1l = meta.get("n1l")
        proc = meta.get("process")
        print(f"{p.name}  n0l={n0l} n1l={n1l}  created_at_utc={created}  process=\"{proc}\"")


def use(state: AppState, arg: str) -> None:
    arg_clean, pick, _ = parse_pick_flag(arg)
    target = arg_clean.strip()
    if not target:
        print("Usage: use <run>")
        return
    direct = Path(target)
    if not direct.is_absolute():
        direct = runs_dir() / target
    if direct.exists() and direct.is_dir():
        try:
            state.ctx.attach(direct)
            state.refs().load_from_meta()
        except Exception as exc:
            print(f"Error: {exc}")
        return
    tag = resolve_tag_from_process_or_tag(target)
    runs_list = list_runs(tag=tag)
    if not runs_list:
        print(f"[use] No runs found for tag '{tag}'.")
        return
    chosen = pick_run_interactive(runs_list) if pick and len(runs_list) > 1 else runs_list[0]
    if not chosen:
        print("Invalid selection.")
        return
    try:
        state.ctx.attach(chosen)
        state.refs().load_from_meta()
    except Exception as exc:
        print(f"Error: {exc}")


def clean(state: AppState, arg: str) -> None:
    deleted = 0
    for p in list_runs():
        try:
            shutil.rmtree(p)
            deleted += 1
        except Exception as exc:
            print(f"[clean] Failed to delete {p}: {exc}")
    state.ctx = RunContext()
    state.gluon_refs = None
    print(f"[clean] Deleted {deleted} output folder(s) in: {runs_dir()}")


def show(state: AppState, arg: str) -> None:
    print(f"runs root       : {runs_dir()}")
    print(f"form_exe        : {state.form_exe}")
    print(f"last_process    : {state.ctx.process}")
    print(f"last_output_dir : {state.ctx.run_dir}")
    print(f"prep jobs req   : {state.ctx.prep_jobs_requested}")
    print(f"prep jobs eff   : {state.ctx.prep_jobs_effective}")


def setrefs(state: AppState, arg: str) -> None:
    if not state.ensure_run():
        return
    process_str = state.ctx.meta.get("process", "") if isinstance(state.ctx.meta, dict) else ""
    refs = state.refs().force_refresh(process_str)
    if refs:
        print(f"[setrefs] Saved gluon refs: {refs}")


def smoke(state: AppState, arg: str) -> None:
    if arg.strip():
        print("Usage: smoke")
        return
    try:
        if not qgraf_exe().exists():
            print(f"[smoke] Missing qgraf: {qgraf_exe()}")
            return
        proc_dir = procedures_dir()
        if not (proc_dir / "declarations.h").exists():
            print(f"[smoke] Missing declarations.h: {proc_dir / 'declarations.h'}")
            return
    except Exception as exc:
        print(f"[smoke] Error: {exc}")
        return

    print("[smoke] qgraf found.")
    print("[smoke] procedures found.")
    generate.run(state, "g g > t t~ --jobs 1")
    if state.ctx.run_dir:
        print(f"[smoke] run dir created: {state.ctx.run_dir}")
        evaluate.run(state, "lo")
        print("[smoke] OK.")


def contract_full(state: AppState, arg: str) -> None:
    if not state.ensure_run():
        return
    jobs = None
    toks = shlex.split(arg)
    if "--jobs" in toks:
        try:
            idx = toks.index("--jobs")
            jobs = int(toks[idx + 1])
        except Exception:
            print("Usage: contract full [--jobs K]")
            return
    for mode in ("lo", "nlo", "mct"):
        cmd = mode if jobs is None else f"{mode} --jobs {jobs}"
        evaluate.run(state, cmd)
    for mode in ("lo", "nlo", "mct"):
        cmd = mode if jobs is None else f"{mode} --jobs {jobs}"
        from glaslib.commands import contract

        contract.run(state, cmd)
    uvct.run(state, "")

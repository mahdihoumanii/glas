from __future__ import annotations

import cmd
import json
import shutil
from pathlib import Path

from glas.commands import contract, evaluate, generate, ioperator, uvct
from glas.commands.common import AppState, MODES, parse_pick_flag
from glas.config import build_config
from glaslib.runs import RunContext, list_runs, pick_run_interactive, resolve_tag_from_process_or_tag


class GlasShell(cmd.Cmd):
    intro = "GLAS unified shell. Type 'help' or '?'.\n"
    prompt = "glas> "

    def __init__(self) -> None:
        super().__init__()
        config = build_config()
        self.state = AppState(config=config, ctx=RunContext(root=config.root))

    # ----------------- Commands -----------------
    def do_generate(self, arg: str) -> None:
        generate.run(self.state, arg)

    def do_evaluate(self, arg: str) -> None:
        evaluate.run(self.state, arg)

    def complete_evaluate(self, text, line, begidx, endidx):
        return [m for m in MODES if not text or m.startswith(text)]

    def do_contract(self, arg: str) -> None:
        contract.run(self.state, arg)

    def complete_contract(self, text, line, begidx, endidx):
        return [m for m in MODES if not text or m.startswith(text)]

    def do_uvct(self, arg: str) -> None:
        uvct.run(self.state, arg)

    def do_ioperator(self, arg: str) -> None:
        ioperator.run(self.state, arg)

    def do_setrefs(self, arg: str) -> None:
        if not self.state.ensure_run():
            return
        process_str = self.state.ctx.meta.get("process", "") if isinstance(self.state.ctx.meta, dict) else ""
        refs = self.state.force_refresh_gluon_refs(process_str)
        if refs:
            print(f"[setrefs] Saved gluon refs: {refs}")

    def do_runs(self, arg: str) -> None:
        target = arg.strip()
        tag = resolve_tag_from_process_or_tag(target) if target else None
        candidates = list_runs(self.state.config.runs_root, tag=tag)
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

    def do_use(self, arg: str) -> None:
        arg_clean, pick = parse_pick_flag(arg)
        target = arg_clean.strip()
        if not target:
            print("Usage: use <run>")
            return
        direct = Path(target)
        if not direct.is_absolute():
            direct = self.state.config.runs_root / target
        if direct.exists() and direct.is_dir():
            try:
                self.state.ctx.attach(direct)
                self.state.load_gluon_refs_from_meta()
            except Exception as exc:
                print(f"Error: {exc}")
            return
        tag = resolve_tag_from_process_or_tag(target)
        runs = list_runs(self.state.config.runs_root, tag=tag)
        if not runs:
            print(f"[use] No runs found for tag '{tag}'.")
            return
        chosen = pick_run_interactive(runs) if pick and len(runs) > 1 else runs[0]
        if not chosen:
            print("Invalid selection.")
            return
        try:
            self.state.ctx.attach(chosen)
            self.state.load_gluon_refs_from_meta()
        except Exception as exc:
            print(f"Error: {exc}")

    def complete_use(self, text, line, begidx, endidx):
        completions = []
        for p in self.state.config.runs_root.iterdir():
            if not p.is_dir():
                continue
            if not (p / "meta.json").exists():
                continue
            name = p.name
            if not text or name.startswith(text):
                completions.append(name)
        completions.sort()
        return completions

    def do_clean(self, arg: str) -> None:
        deleted = 0
        for p in list_runs(self.state.config.runs_root):
            try:
                shutil.rmtree(p)
                deleted += 1
            except Exception as exc:
                print(f"[clean] Failed to delete {p}: {exc}")
        self.state.ctx = RunContext(root=self.state.config.root)
        print(f"[clean] Deleted {deleted} output folder(s) in: {self.state.config.runs_root}")

    def do_show(self, arg: str) -> None:
        print(f"root            : {self.state.config.root}")
        print(f"runs root       : {self.state.config.runs_root}")
        print(f"form_exe        : {self.state.config.form_exe}")
        print(f"last_process    : {self.state.ctx.process}")
        print(f"last_output_dir : {self.state.ctx.run_dir}")
        print(f"prep jobs req   : {self.state.ctx.prep_jobs_requested}")
        print(f"prep jobs eff   : {self.state.ctx.prep_jobs_effective}")

    def do_extract(self, arg: str) -> None:
        print("[extract] Placeholder only (integrals extraction is disabled).")

    def do_exit(self, arg: str) -> bool:
        return True

    def do_quit(self, arg: str) -> bool:
        return True

    def emptyline(self) -> None:
        pass


def main() -> None:
    GlasShell().cmdloop()

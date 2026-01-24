from __future__ import annotations

import cmd

from glaslib.commands import contract, evaluate, extract, generate, ioperator, linrels, micoef, misc, ratcombine, reduce, uvct
from glaslib.commands.common import AppState, MODES
from glaslib.core.run_manager import RunContext
from glaslib.formprep import prepare_form


class GlasShell(cmd.Cmd):
    intro = "GLAS unified shell. Type 'help' or '?'.\n"
    prompt = "glas> "

    def __init__(self) -> None:
        super().__init__()
        self.state = AppState(ctx=RunContext())

    # ----------------- Commands -----------------
    def do_generate(self, arg: str) -> None:
        generate.run(self.state, arg)

    def do_formprep(self, arg: str) -> None:
        if not self.state.ensure_run():
            return
        jobs = 1
        try:
            toks = arg.split()
            if "--jobs" in toks:
                idx = toks.index("--jobs")
                jobs = int(toks[idx + 1])
        except Exception:
            print("Usage: formprep [--jobs K]")
            return
        try:
            prepare_form(self.state.ctx, jobs=jobs)
            print("[formprep] OK")
            print(f"  jobs requested : {self.state.ctx.prep_jobs_requested}")
            print(f"  jobs effective : {self.state.ctx.prep_jobs_effective}")
        except Exception as exc:
            print(f"Error: {exc}")

    def do_evaluate(self, arg: str) -> None:
        evaluate.run(self.state, arg)

    def complete_evaluate(self, text, line, begidx, endidx):
        return [m for m in MODES if not text or m.startswith(text)]

    def do_contract(self, arg: str) -> None:
        if arg.strip().lower().startswith("full"):
            misc.contract_full(self.state, arg)
            return
        contract.run(self.state, arg)

    def complete_contract(self, text, line, begidx, endidx):
        modes = list(MODES) + ["full"]
        return [m for m in modes if not text or m.startswith(text)]

    def do_reduce(self, arg: str) -> None:
        reduce.run(self.state, arg)

    def do_micoef(self, arg: str) -> None:
        micoef.run(self.state, arg)

    def do_uvct(self, arg: str) -> None:
        uvct.run(self.state, arg)

    def do_ioperator(self, arg: str) -> None:
        ioperator.run(self.state, arg)

    def do_extract(self, arg: str) -> None:
        extract.run(self.state, arg)

    def do_ibp(self, arg: str) -> None:
        extract.ibp(self.state, arg)

    def do_linrels(self, arg: str) -> None:
        linrels.run(self.state, arg)

    def do_ratcombine(self, arg: str) -> None:
        ratcombine.run(self.state, arg)

    def do_runs(self, arg: str) -> None:
        misc.runs(self.state, arg)

    def do_use(self, arg: str) -> None:
        misc.use(self.state, arg)

    def complete_use(self, text, line, begidx, endidx):
        from glaslib.core.run_manager import list_runs

        completions = []
        for p in list_runs():
            name = p.name
            if not text or name.startswith(text):
                completions.append(name)
        completions.sort()
        return completions

    def do_clean(self, arg: str) -> None:
        misc.clean(self.state, arg)

    def do_show(self, arg: str) -> None:
        misc.show(self.state, arg)

    def do_setrefs(self, arg: str) -> None:
        misc.setrefs(self.state, arg)

    def do_smoke(self, arg: str) -> None:
        misc.smoke(self.state, arg)

    def do_verbose(self, arg: str) -> None:
        """Toggle or set verbose mode. Usage: verbose [on|off]"""
        t = arg.strip().lower()
        if t in ("on", "1", "true", "yes"):
            self.state.verbose = True
        elif t in ("off", "0", "false", "no"):
            self.state.verbose = False
        elif not t:
            self.state.verbose = not self.state.verbose
        else:
            print("Usage: verbose [on|off]")
            return
        status = "ON" if self.state.verbose else "OFF"
        print(f"[verbose] Verbose mode is now {status}")

    def do_exit(self, arg: str) -> bool:
        return True

    def do_quit(self, arg: str) -> bool:
        return True

    def emptyline(self) -> None:
        pass


def main() -> None:
    GlasShell().cmdloop()

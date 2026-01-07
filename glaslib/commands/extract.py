from __future__ import annotations

from glaslib.commands.common import AppState


def run(state: AppState, arg: str) -> None:
    target = arg.strip().lower()
    if not target:
        print("Usage: extract topologies")
        return
    print("[extract] Disabled for now (Mathematica not wired yet).")

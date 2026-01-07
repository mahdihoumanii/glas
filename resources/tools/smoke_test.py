#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
import time
import traceback
from pathlib import Path


def _ensure_project_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quick GLAS smoke test.")
    parser.add_argument(
        "--process",
        default="g g > t t~",
        help="Process string to generate (default: 'g g > t t~').",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep generated run folder even if the test succeeds.",
    )
    parser.add_argument(
        "--dirac",
        action="store_true",
        help="Also run DiracSimplify 2 if FORM is available.",
    )
    return parser.parse_args()


def _fail(msg: str, exc: BaseException | None = None) -> int:
    print(f"[FAIL] {msg}")
    if exc:
        traceback.print_exc()
    return 1


def _run_dirac(
    *,
    ctx,
    prepare_dirac,
    run_jobs,
    form_exe: str,
    jobs: int,
) -> bool:
    out = prepare_dirac(ctx, mode="2", jobs=jobs, gluon_orth={})
    form_dir = out["form_dir"]
    ok_all = True

    tree = out.get("tree") or {}
    tree_jobs = tree.get("jobs_effective", jobs)
    tree_drivers = tree.get("drivers", {}) or {}
    tasks = [
        (f"DiracSimplify_tree_J{k}of{tree_jobs}", form_dir, drv)
        for k, drv in tree_drivers.items()
    ]
    if tasks:
        ok_all = ok_all and run_jobs(form_exe, tasks, max_workers=tree_jobs)

    loop = out.get("loop") or {}
    loop_jobs = loop.get("jobs_effective", jobs)
    loop_drivers = loop.get("drivers", {}) or {}
    tasks = [
        (f"DiracSimplify_loop_J{k}of{loop_jobs}", form_dir, drv)
        for k, drv in loop_drivers.items()
    ]
    if tasks:
        ok_all = ok_all and run_jobs(form_exe, tasks, max_workers=loop_jobs)

    return ok_all


def main() -> int:
    args = _parse_args()
    root = _ensure_project_root()
    print(f"[info] Project root: {root}")

    try:
        from diagrams.generate_diagrams import parse_process  # noqa: F401
        from glaslib.formprep import prepare_form
        from glaslib.parallel import run_jobs
        from glaslib.qgraf import generate_run
        from glaslib.runs import RunContext
        from glaslib.dirac import prepare_dirac
    except Exception as exc:  # pragma: no cover - import guard
        return _fail("Imports failed", exc)

    tools_dir = root / "diagrams"
    qgraf_exe = tools_dir / "qgraf"
    style_file = tools_dir / "mystyle.sty"

    for required in (tools_dir, qgraf_exe, style_file):
        if not required.exists():
            return _fail(f"Missing required tool: {required}")

    ctx = RunContext(root=root)
    out_name = f"smoke_{int(time.time())}"
    run_dir: Path | None = None

    try:
        res = generate_run(
            args.process,
            root=root,
            tools_dir=tools_dir,
            qgraf_exe=qgraf_exe,
            style_file=style_file,
            model="qcd",
            keep_temp=False,
            out_name=out_name,
        )
        run_dir = Path(res["output_dir"]).resolve()
        ctx.attach(run_dir)
        print(f"[ok] generate -> {run_dir}")
    except Exception as exc:
        return _fail("generate failed", exc)

    try:
        prepare_form(ctx, jobs=1)
        print("[ok] formprep")
    except Exception as exc:
        return _fail("formprep failed", exc)

    form_exe = shutil.which("form")
    if not form_exe:
        print("[skip] evaluate/DiracSimplify: FORM executable not found in PATH.")
    else:
        jobs = ctx.prep_jobs_effective or 1
        form_dir = ctx.prep_form_dir or (next(iter(ctx.eval_drivers.values())).parent if ctx.eval_drivers else None)
        tasks = [
            (f"evaluate_J{j}of{jobs}", form_dir, drv)
            for j, drv in ctx.eval_drivers.items()
        ]
        if tasks:
            ok = run_jobs(form_exe, tasks, max_workers=jobs)
            if not ok:
                return _fail("evaluate failed")
            print("[ok] evaluate")
        else:
            print("[warn] No evaluate drivers found; skipping evaluate.")

        if args.dirac and ctx.dirac_drivers:
            ok_dirac = _run_dirac(
                ctx=ctx,
                prepare_dirac=prepare_dirac,
                run_jobs=run_jobs,
                form_exe=form_exe,
                jobs=jobs,
            )
            if not ok_dirac:
                return _fail("DiracSimplify failed")
            print("[ok] DiracSimplify (mode 2)")

    if run_dir and not args.keep:
        try:
            shutil.rmtree(run_dir)
            print(f"[info] Cleaned up {run_dir}")
        except Exception as exc:
            print(f"[warn] Failed to clean up {run_dir}: {exc}")

    print("[done] Smoke test completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

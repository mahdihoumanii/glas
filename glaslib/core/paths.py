from __future__ import annotations

import os
import shutil
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resources_dir() -> Path:
    return project_root() / "resources"


def runs_dir() -> Path:
    p = project_root() / "runs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def diagrams_dir() -> Path:
    return resources_dir() / "diagrams"


def qgraf_exe() -> Path:
    return diagrams_dir() / "qgraf"


def style_file() -> Path:
    return diagrams_dir() / "mystyle.sty"


def procedures_dir() -> Path:
    env = os.environ.get("GLAS_FORM_PROCS") or os.environ.get("ORYX_FORM_PROCS")
    if env:
        p = Path(env).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"GLAS_FORM_PROCS/ORYX_FORM_PROCS is set but does not exist: {p}")
        return p

    p = resources_dir() / "formlib" / "procedures"
    if not p.exists():
        raise FileNotFoundError(
            f"Procedures folder not found: {p}\n"
            f"Create it or export GLAS_FORM_PROCS=/abs/path/to/procedures"
        )
    return p


def tools_dir() -> Path:
    return resources_dir() / "tools"


def ensure_symlink_or_copy(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    try:
        os.symlink(str(src.resolve()), str(dst.resolve()), target_is_directory=True)
    except Exception:
        shutil.copytree(src, dst)


def setup_run_procedures(run_dir: Path, feynman_rules_prc: str) -> Path:
    """
    Set up a run-specific procedures directory with the correct Feynman rules.

    This function:
    1. Creates a procedures directory in the run's form folder
    2. Symlinks all procedure files from the global procedures dir
    3. Copies the model-specific Feynman rules as FeynmanRules.prc

    Args:
        run_dir: Path to the run directory
        feynman_rules_prc: Filename of the Feynman rules procedure file to use

    Returns:
        Path to the run-specific procedures directory (for use as IncDir)
    """
    run_dir = Path(run_dir).resolve()
    global_procs = procedures_dir()
    run_procs = run_dir / "form" / "procedures"
    run_procs.mkdir(parents=True, exist_ok=True)

    # Copy/link all procedure files from global dir
    for src_file in global_procs.iterdir():
        if not src_file.is_file():
            continue
        dst_file = run_procs / src_file.name
        # Skip FeynmanRules*.prc files - we'll handle those specially
        if src_file.name.startswith("FeynmanRules") and src_file.name.endswith(".prc"):
            continue
        if not dst_file.exists():
            try:
                os.symlink(str(src_file.resolve()), str(dst_file))
            except Exception:
                shutil.copy2(src_file, dst_file)

    # Copy the selected Feynman rules as FeynmanRules.prc
    src_feynman = global_procs / feynman_rules_prc
    dst_feynman = run_procs / "FeynmanRules.prc"
    if not src_feynman.exists():
        raise FileNotFoundError(
            f"Feynman rules procedure file not found: {src_feynman}\n"
            f"Please create {feynman_rules_prc} in {global_procs}"
        )
    # Always copy (not symlink) so we can later inspect which rules were used
    if dst_feynman.exists():
        dst_feynman.unlink()
    shutil.copy2(src_feynman, dst_feynman)

    return run_procs

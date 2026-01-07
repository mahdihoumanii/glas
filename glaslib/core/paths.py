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

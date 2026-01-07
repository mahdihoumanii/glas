from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from glaslib.paths import diagrams_dir, runs_dir


@dataclass
class GlasConfig:
    root: Path
    runs_root: Path
    tools_dir: Path
    qgraf_exe: Path
    style_file: Path
    model: str = "qcd"
    form_exe: str = "form"
    keep_temp: bool = False


def build_config() -> GlasConfig:
    root = Path(__file__).resolve().parents[1]
    tools_dir = diagrams_dir(root)
    return GlasConfig(
        root=root,
        runs_root=runs_dir(root),
        tools_dir=tools_dir,
        qgraf_exe=tools_dir / "qgraf",
        style_file=tools_dir / "mystyle.sty",
    )

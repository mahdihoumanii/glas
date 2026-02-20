from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from glaslib.generate_diagrams import generate_both


def generate_run(
    process_str: str,
    *,
    root: Path,
    tools_dir: Path,
    qgraf_exe: Path,
    style_file: Path,
    model_id: str,
    keep_temp: bool = False,
    out_name: Optional[str] = None,
) -> Dict[str, Any]:
    return generate_both(
        process_str=process_str,
        project_root=root,
        tools_dir=tools_dir,
        qgraf_exe=qgraf_exe,
        style_file=style_file,
        model_id=model_id,
        keep_temp=keep_temp,
        out_name=out_name,
    )

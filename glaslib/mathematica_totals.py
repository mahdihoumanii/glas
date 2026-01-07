from __future__ import annotations

from pathlib import Path
from typing import Optional


def _extract_rhs(text: str) -> Optional[str]:
    if "=" not in text or ";" not in text:
        return None
    rhs = text.split("=", 1)[1]
    rhs = rhs.rsplit(";", 1)[0]
    rhs = rhs.strip()
    return rhs or None


def _sum_to_file(src_dir: Path, symbol: str, target: Path) -> bool:
    src_dir = Path(src_dir)
    files = sorted(p for p in src_dir.glob("*.m") if p.is_file())
    files = [p for p in files if p.resolve() != target.resolve()]
    exprs = []
    for f in files:
        rhs = _extract_rhs(f.read_text(encoding="utf-8"))
        if rhs:
            exprs.append(rhs)
    if not exprs:
        return False
    total = " + ".join(f"({e})" for e in exprs)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"{symbol} = {total};\n", encoding="utf-8")
    return True


def write_total_to_uvct(run_dir: Path, subdir: str, symbol: str) -> bool:
    base = Path(run_dir) / "Mathematica" / "Files"
    src = base / subdir
    if not src.exists():
        return False
    dst = base / "UVCT" / f"{symbol}.m"
    return _sum_to_file(src, symbol, dst)

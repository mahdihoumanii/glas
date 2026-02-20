"""
Centralized logging utilities for GLAS.

All logs are written to runs/{tag}_{nnnn}/logs/ with subdirectories:
- logs/form/       - FORM job logs
- logs/extract/    - Topology extraction logs (Mathematica + Python)
- logs/ibp/        - IBP reduction logs
- logs/linrels/    - Linear relations logs
- logs/uvct/       - UV counterterm logs
- logs/ioperator/  - I-operator logs
- logs/reduce/     - Reduction logs
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Union

from glaslib.core.run_manager import RunContext


def ensure_logs_dir(ctx_or_run_dir: Union[RunContext, Path], subdir: Optional[str] = None) -> Path:
    """
    Ensure the logs directory exists for the given run context.
    
    Args:
        ctx_or_run_dir: RunContext or run directory Path
        subdir: Optional subdirectory under logs/ (e.g., "form", "extract", "ibp")
    
    Returns:
        Path to the logs directory (with subdir if specified)
    """
    if isinstance(ctx_or_run_dir, RunContext):
        if ctx_or_run_dir.run_dir is None:
            raise ValueError("No run directory attached to context")
        run_dir = ctx_or_run_dir.run_dir
    else:
        run_dir = ctx_or_run_dir
    
    logs_dir = run_dir / "logs"
    if subdir:
        logs_dir = logs_dir / subdir
    
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def make_log_path(
    ctx_or_run_dir: Union[RunContext, Path],
    subdir: str,
    prefix: str,
    suffix: str = ".log",
    with_timestamp: bool = False,
) -> Path:
    """
    Create a deterministic log file path.
    
    Args:
        ctx_or_run_dir: RunContext or run directory Path
        subdir: Subdirectory under logs/ (e.g., "form", "extract")
        prefix: Log file prefix (e.g., "eval_lo_J1of4", "stage1")
        suffix: File suffix (default ".log")
        with_timestamp: Whether to include timestamp in filename
    
    Returns:
        Path to the log file
    """
    logs_dir = ensure_logs_dir(ctx_or_run_dir, subdir)
    
    if with_timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}.{ts}{suffix}"
    else:
        filename = f"{prefix}{suffix}"
    
    return logs_dir / filename


def make_log_paths(
    ctx_or_run_dir: Union[RunContext, Path],
    subdir: str,
    prefix: str,
    with_timestamp: bool = False,
) -> Tuple[Path, Path]:
    """
    Create separate stdout and stderr log file paths.
    
    Args:
        ctx_or_run_dir: RunContext or run directory Path
        subdir: Subdirectory under logs/ (e.g., "form", "extract")
        prefix: Log file prefix (e.g., "stage1", "IBP")
        with_timestamp: Whether to include timestamp in filename
    
    Returns:
        Tuple of (stdout_path, stderr_path)
    """
    logs_dir = ensure_logs_dir(ctx_or_run_dir, subdir)
    
    if with_timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        stdout_path = logs_dir / f"{prefix}.{ts}.stdout.log"
        stderr_path = logs_dir / f"{prefix}.{ts}.stderr.log"
    else:
        stdout_path = logs_dir / f"{prefix}.stdout.log"
        stderr_path = logs_dir / f"{prefix}.stderr.log"
    
    return stdout_path, stderr_path


def format_log_reference(log_path: Path, run_dir: Optional[Path] = None) -> str:
    """
    Format a log path for display in error messages.
    
    If run_dir is provided, shows relative path from run_dir.
    Otherwise shows absolute path.
    """
    if run_dir and log_path.is_relative_to(run_dir):
        return str(log_path.relative_to(run_dir))
    return str(log_path)


def format_failure_message(
    stage: str,
    returncode: int,
    log_path: Optional[Path] = None,
    run_dir: Optional[Path] = None,
) -> str:
    """
    Format a consistent failure message with log reference.
    
    Args:
        stage: Name of the failed stage (e.g., "extract stage1", "FORM eval_lo_J1of4")
        returncode: Exit code of the failed process
        log_path: Path to the log file (combined or stdout)
        run_dir: Run directory for relative path display
    
    Returns:
        Formatted error message
    """
    msg = f"[{stage}] Failed (code={returncode})."
    if log_path:
        ref = format_log_reference(log_path, run_dir)
        msg += f" See log: {ref}"
    return msg


# Log subdirectory constants for consistency
LOG_SUBDIR_FORM = "form"
LOG_SUBDIR_EXTRACT = "extract"
LOG_SUBDIR_IBP = "ibp"
LOG_SUBDIR_LINRELS = "linrels"
LOG_SUBDIR_UVCT = "uvct"
LOG_SUBDIR_IOPERATOR = "ioperator"
LOG_SUBDIR_REDUCE = "reduce"
LOG_SUBDIR_EVALUATE = "evaluate"
LOG_SUBDIR_CONTRACT = "contract"
LOG_SUBDIR_DIRAC = "dirac"
LOG_SUBDIR_TOPOFORMAT = "topoformat"
LOG_SUBDIR_RATCOMBINE = "ratcombine"
LOG_SUBDIR_KTEXPAND = "ktexpand"

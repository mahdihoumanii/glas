"""
Streaming subprocess runner with live output and log capture.

Provides unified subprocess execution for FORM, Mathematica, Python helpers,
and IBP tools with optional verbose streaming to terminal.
"""

from __future__ import annotations

import os
import shlex
import sys
import threading
from pathlib import Path
from subprocess import DEVNULL, PIPE, Popen
from typing import Dict, List, Optional, TextIO


def _stream_reader(
    stream: TextIO,
    log_file: Optional[TextIO],
    prefix: str,
    verbose: bool,
    lock: threading.Lock,
) -> None:
    """Read from stream line by line, optionally print with prefix, write to log."""
    try:
        for line in stream:
            # Write to log file if provided
            if log_file is not None:
                log_file.write(line)
                log_file.flush()
            # Print to terminal if verbose
            if verbose:
                with lock:
                    # Prefix each line
                    print(f"[{prefix}] {line}", end="", flush=True)
    except Exception:
        pass  # Stream closed or error


def run_streaming(
    cmd: List[str],
    cwd: Path,
    env: Optional[Dict[str, str]] = None,
    log_path: Optional[Path] = None,
    prefix: str = "cmd",
    verbose: bool = False,
) -> int:
    """
    Run a command with optional live streaming output.

    Args:
        cmd: Command and arguments to run
        cwd: Working directory
        env: Environment variable overrides (merged with os.environ)
        log_path: Path to write combined stdout/stderr log
        prefix: Prefix for verbose output lines (e.g., "form eval lo J1/4")
        verbose: If True, print output live to terminal with prefix

    Returns:
        Exit code of the process
    """
    import subprocess
    
    # Build environment: inherit os.environ, overlay with env overrides
    full_env = os.environ.copy()
    # Set PYTHONUNBUFFERED by default for Python subprocesses
    if "PYTHONUNBUFFERED" not in full_env:
        full_env["PYTHONUNBUFFERED"] = "1"
    if env:
        full_env.update(env)

    # Create log directory if needed
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # For non-verbose mode, use shell execution to completely isolate from Python
    if not verbose:
        # Build shell command with proper escaping
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        log_str = shlex.quote(str(log_path)) if log_path else "/dev/null"
        
        # Use shell to run command with stdin closed and output redirected
        # This completely bypasses Python's file descriptor handling
        shell_cmd = f"cd {shlex.quote(str(cwd))} && {cmd_str} </dev/null >{log_str} 2>&1"
        
        rc = os.system(shell_cmd)
        # os.system returns the exit status in the format returned by wait()
        # Need to extract the actual exit code
        if os.WIFEXITED(rc):
            return os.WEXITSTATUS(rc)
        return 1  # Signal or other abnormal termination

    # Verbose mode: use Popen with streaming threads
    log_file: Optional[TextIO] = None
    if log_path is not None:
        log_file = open(log_path, "w", encoding="utf-8")

    try:
        proc = Popen(
            cmd,
            cwd=str(cwd),
            env=full_env,
            stdin=DEVNULL,  # Prevent subprocess from reading parent's stdin
            stdout=PIPE,
            stderr=PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )

        # Lock for synchronized printing
        print_lock = threading.Lock()

        # Start threads to read stdout and stderr concurrently
        stdout_thread = threading.Thread(
            target=_stream_reader,
            args=(proc.stdout, log_file, prefix, verbose, print_lock),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_stream_reader,
            args=(proc.stderr, log_file, f"{prefix}:err", verbose, print_lock),
            daemon=True,
        )

        stdout_thread.start()
        stderr_thread.start()

        # Wait for process to complete
        proc.wait()

        # Wait for threads to finish reading
        stdout_thread.join(timeout=5.0)
        stderr_thread.join(timeout=5.0)

        return proc.returncode

    finally:
        if log_file is not None:
            log_file.close()


def run_checked_streaming(
    cmd: List[str],
    cwd: Path,
    env: Optional[Dict[str, str]] = None,
    log_path: Optional[Path] = None,
    prefix: str = "cmd",
    verbose: bool = False,
) -> None:
    """
    Run a command with streaming, raise RuntimeError on failure.

    Args:
        Same as run_streaming

    Raises:
        RuntimeError: If process exits with non-zero code
    """
    rc = run_streaming(cmd, cwd, env, log_path, prefix, verbose)
    if rc != 0:
        log_info = f" See {log_path}" if log_path else ""
        raise RuntimeError(f"[{prefix}] failed (rc={rc}).{log_info}")


def get_project_python() -> Path:
    """
    Get the Python interpreter from the project's virtual environment.

    Falls back to sys.executable if venv not found.
    """
    from glaslib.core.paths import project_root

    root = project_root()
    venv_python = root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return venv_python

    # Windows fallback
    venv_python_win = root / ".venv" / "Scripts" / "python.exe"
    if venv_python_win.exists():
        return venv_python_win

    # Fallback to current interpreter
    return Path(sys.executable)

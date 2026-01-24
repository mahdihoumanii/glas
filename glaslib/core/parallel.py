from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Optional, Tuple

from glaslib.core.logging import ensure_logs_dir, LOG_SUBDIR_FORM
from glaslib.core.proc import run_streaming


def chunk_range_1based(total: int, jobs: int, job_index: int) -> Tuple[int, int]:
    if total <= 0:
        return 1, 0
    jobs = max(1, jobs)
    base = total // jobs
    rem = total % jobs
    size = base + 1 if job_index <= rem else base
    start = (job_index - 1) * base + min(job_index - 1, rem) + 1
    end = start + size - 1
    if size <= 0:
        return 1, 0
    return start, min(end, total)


def effective_jobs(total: int, requested: int) -> int:
    if total <= 0:
        return 1
    return max(1, min(max(1, requested), total))


def _run_once(
    form_exe: str,
    form_dir: Path,
    driver: Path,
    tag: str,
    verbose: bool = False,
    log_dir: Optional[Path] = None,
    log_subdir: str = LOG_SUBDIR_FORM,
) -> bool:
    form_dir = Path(form_dir)
    driver = Path(driver)
    
    # Determine log path - use centralized logs/ if log_dir provided
    if log_dir is not None:
        logs_path = ensure_logs_dir(log_dir, log_subdir)
        log_path = logs_path / f"{tag}.log"
    else:
        # Fallback to form_dir for backwards compatibility
        log_path = form_dir / f"form_{tag}.log"

    if not verbose:
        print(f"[start {tag}] {driver.name}")

    rc = run_streaming(
        cmd=[form_exe, driver.name],
        cwd=form_dir,
        log_path=log_path,
        prefix=f"form {tag}",
        verbose=verbose,
    )

    if rc != 0:
        print(f"[fail {tag}] code={rc}")
        print(f"  log: {log_path}")
        return False

    if not verbose:
        print(f"[done {tag}]")
    return True


def run_jobs(
    form_exe: str,
    jobs: Iterable[Tuple[str, Path, Path]],
    max_workers: int,
    verbose: bool = False,
    run_dir: Optional[Path] = None,
    log_subdir: str = LOG_SUBDIR_FORM,
) -> bool:
    """
    Run FORM jobs in parallel with optional verbose streaming.

    Args:
        form_exe: Path to FORM executable
        jobs: Iterable of (tag, form_dir, driver_path) tuples
        max_workers: Maximum parallel workers
        verbose: If True, stream output live to terminal
        run_dir: Run directory for centralized logging (logs written to run_dir/logs/)
        log_subdir: Subdirectory under logs/ (default "form")

    Returns:
        True if all jobs succeeded, False otherwise
    """
    job_list = list(jobs)
    if not job_list:
        print("[run] No jobs to run.")
        return True
    ok_all = True
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = []
        for tag, form_dir, drv in job_list:
            futs.append(ex.submit(_run_once, form_exe, form_dir, drv, tag, verbose, run_dir, log_subdir))
        for fut in as_completed(futs):
            ok_all = ok_all and bool(fut.result())
    
    # Print logs location summary
    if run_dir is not None and not verbose:
        logs_loc = run_dir / "logs" / log_subdir
        if ok_all:
            print(f"  Logs: {logs_loc}/")
    
    return ok_all

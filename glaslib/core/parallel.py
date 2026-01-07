from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Tuple


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


def _run_once(form_exe: str, form_dir: Path, driver: Path, tag: str) -> bool:
    form_dir = Path(form_dir)
    driver = Path(driver)
    log_out = form_dir / f"form_{tag}.stdout.log"
    log_err = form_dir / f"form_{tag}.stderr.log"
    print(f"[start {tag}] {driver}")
    res = subprocess.run(
        [form_exe, driver.name],
        cwd=str(form_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    log_out.write_text(res.stdout or "", encoding="utf-8")
    log_err.write_text(res.stderr or "", encoding="utf-8")
    if res.returncode != 0:
        print(f"[fail {tag}] code={res.returncode} driver={driver}")
        print(f"  stdout: {log_out}")
        print(f"  stderr: {log_err}")
        return False
    print(f"[done {tag}] driver={driver}")
    return True


def run_jobs(form_exe: str, jobs: Iterable[Tuple[str, Path, Path]], max_workers: int) -> bool:
    job_list = list(jobs)
    if not job_list:
        print("[run] No jobs to run.")
        return True
    ok_all = True
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = []
        for tag, form_dir, drv in job_list:
            futs.append(ex.submit(_run_once, form_exe, form_dir, drv, tag))
        for fut in as_completed(futs):
            ok_all = ok_all and bool(fut.result())
    return ok_all

"""Run independent annulus trainings in parallel processes.

Each training is independent: its own seeds, its own model, its own optimizer, one
CPU thread (``optimizer.threads``). Running them side by side changes nothing about
any single run -- the same function receives the same arguments in a fresh process --
so the results equal the sequential ones bit for bit; ``test_annulus_parallel`` checks
that on real trainings. ``workers`` is an EXECUTION parameter like the device: it is
recorded in identity.json and never read from the frozen config, so choosing it cannot
move codeHash.
"""

from __future__ import annotations

import concurrent.futures
import multiprocessing
from typing import Any, Callable, Mapping, Sequence


def _train_one(job: Mapping[str, Any]) -> dict[str, Any]:
    from . import pinn_torch_annulus as pinn

    return pinn.train_run(job["config"], job["pool"], job["dev_points"], job["seeds"],
                          collocation_count=job["collocation_count"], device=job.get("device", "cpu"),
                          perturbation=job.get("perturbation"))


def train_many(jobs: Sequence[Mapping[str, Any]], *, workers: int = 1,
               log: Callable[[str], None] = print) -> list[dict[str, Any]]:
    """Train every job; the returned list is in job order whatever order they finish in."""

    workers = max(1, int(workers))
    if workers == 1 or len(jobs) <= 1:
        return [_train_one(job) for job in jobs]
    if any(str(job.get("device", "cpu")).startswith("cuda") for job in jobs):
        raise ValueError("parallel training is CPU-only: several processes on one GPU would share its queue")
    results: list[dict[str, Any] | None] = [None] * len(jobs)
    # spawn, not fork: every worker starts from a clean interpreter, as a separate run would.
    context = multiprocessing.get_context("spawn")
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(workers, len(jobs)), mp_context=context) as pool:
        futures = {pool.submit(_train_one, job): index for index, job in enumerate(jobs)}
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            results[index] = future.result()
            log(f"  job {index} finished ({sum(r is not None for r in results)}/{len(jobs)})")
    return [result for result in results if result is not None]

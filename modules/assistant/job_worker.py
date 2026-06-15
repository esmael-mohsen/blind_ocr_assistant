"""Background job worker for runtime OCR and translation tasks."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from itertools import count
from threading import Lock
from time import monotonic
from typing import Any

from modules.assistant.runtime_state import RuntimeJob, RuntimeJobStatus, RuntimeJobType


class JobWorker:
    """Run long assistant operations outside the GUI/camera loop."""

    def __init__(self, *, max_workers: int = 1) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="assistant-job",
        )
        self._counter = count(1)
        self._lock = Lock()
        self._active_future: Future[Any] | None = None
        self._active_job: RuntimeJob | None = None

    @property
    def active_job(self) -> RuntimeJob | None:
        with self._lock:
            return self._active_job

    def submit(
        self,
        job_type: RuntimeJobType,
        func: Callable[[], Any],
        *,
        progress_label: str,
        on_complete: Callable[[RuntimeJob, Any | None], None] | None = None,
    ) -> RuntimeJob:
        job = RuntimeJob(
            job_id=f"{job_type.value}-{next(self._counter)}",
            job_type=job_type,
            status=RuntimeJobStatus.QUEUED,
            progress_label=progress_label,
        )
        with self._lock:
            if self._active_future is not None and not self._active_future.done():
                raise RuntimeError("A runtime job is already active")
            self._active_job = job

        def _run() -> Any:
            self._set_job(job.with_updates(status=RuntimeJobStatus.RUNNING))
            return func()

        future = self._executor.submit(_run)
        with self._lock:
            self._active_future = future

        def _done(done: Future[Any]) -> None:
            result: Any | None = None
            try:
                result = done.result()
                finished = job.with_updates(
                    status=RuntimeJobStatus.SUCCEEDED,
                    finished_at=monotonic(),
                )
            except Exception as exc:
                finished = job.with_updates(
                    status=RuntimeJobStatus.CANCELLED
                    if done.cancelled()
                    else RuntimeJobStatus.FAILED,
                    finished_at=monotonic(),
                    error=f"{type(exc).__name__}: {exc}",
                )
            self._set_job(finished)
            if on_complete is not None:
                on_complete(finished, result)
            with self._lock:
                if self._active_future is done:
                    self._active_future = None

        future.add_done_callback(_done)
        return job

    def cancel_active(self) -> bool:
        with self._lock:
            future = self._active_future
            job = self._active_job
        if future is None:
            return False
        cancelled = future.cancel()
        if job is not None and cancelled:
            self._set_job(
                job.with_updates(
                    status=RuntimeJobStatus.CANCELLED,
                    finished_at=monotonic(),
                )
            )
        return cancelled

    def shutdown(self) -> None:
        self.cancel_active()
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _set_job(self, job: RuntimeJob) -> None:
        with self._lock:
            self._active_job = job


__all__ = ["JobWorker"]

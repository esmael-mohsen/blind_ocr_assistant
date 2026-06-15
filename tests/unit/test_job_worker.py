"""Tests for assistant background job worker."""

from __future__ import annotations

from threading import Event

from modules.assistant.job_worker import JobWorker
from modules.assistant.runtime_state import RuntimeJobStatus, RuntimeJobType


def test_job_worker_runs_job_and_records_completion():
    worker = JobWorker()
    completed = []
    done = Event()
    try:
        job = worker.submit(
            RuntimeJobType.OCR,
            lambda: "done",
            progress_label="ocr",
            on_complete=lambda finished, result: (
                completed.append((finished, result)),
                done.set(),
            ),
        )
        assert done.wait(2.0)
    finally:
        worker.shutdown()

    assert job.job_type == RuntimeJobType.OCR
    assert completed
    assert completed[0][0].status == RuntimeJobStatus.SUCCEEDED
    assert completed[0][1] == "done"


def test_job_worker_reports_failed_job():
    worker = JobWorker()
    completed = []
    done = Event()

    def _fail():
        raise RuntimeError("boom")

    try:
        worker.submit(
            RuntimeJobType.TRANSLATION,
            _fail,
            progress_label="translation",
            on_complete=lambda finished, result: (
                completed.append((finished, result)),
                done.set(),
            ),
        )
        assert done.wait(2.0)
    finally:
        worker.shutdown()

    assert completed
    assert completed[0][0].status == RuntimeJobStatus.FAILED
    assert "RuntimeError" in completed[0][0].error

"""Deployment readiness model tests."""

from __future__ import annotations

import pytest

from modules.deployment.readiness_models import (
    DependencyCheckResult,
    DeploymentReadinessReport,
    HardwareCheckResult,
    ReadinessStatus,
    most_severe_status,
    sanitize_safe_metadata,
)


def test_status_severity_ordering_blocks_before_manual_degraded_ready() -> None:
    assert most_severe_status([ReadinessStatus.READY]) is ReadinessStatus.READY
    assert (
        most_severe_status([ReadinessStatus.DEGRADED, ReadinessStatus.READY])
        is ReadinessStatus.DEGRADED
    )
    assert (
        most_severe_status(
            [
                ReadinessStatus.READY,
                ReadinessStatus.MANUAL_VERIFICATION_NEEDED,
                ReadinessStatus.DEGRADED,
            ]
        )
        is ReadinessStatus.MANUAL_VERIFICATION_NEEDED
    )
    assert (
        most_severe_status(
            [ReadinessStatus.DEGRADED, ReadinessStatus.BLOCKED]
        )
        is ReadinessStatus.BLOCKED
    )


def test_report_aggregates_overall_status_and_requires_checks() -> None:
    ready = DependencyCheckResult(
        check_id="config.present",
        dependency_area="config",
        status=ReadinessStatus.READY,
        required_for_startup=True,
        message="Configuration is available.",
        remediation="No action needed.",
    )
    blocked = HardwareCheckResult(
        check_id="camera.open",
        hardware_area="camera",
        status=ReadinessStatus.BLOCKED,
        message="Camera could not open.",
        spoken_message="Camera is blocked.",
        remediation="Check camera permissions.",
    )
    report = DeploymentReadinessReport(
        report_id="test",
        target_device="Raspberry Pi 4",
        checks=(ready, blocked),
    )

    assert report.overall_status is ReadinessStatus.BLOCKED
    with pytest.raises(ValueError, match="at least one check"):
        DeploymentReadinessReport(report_id="empty", target_device="pi", checks=())


def test_safe_metadata_removes_private_content_paths_and_secrets() -> None:
    safe = sanitize_safe_metadata(
        {
            "engine": "paddleocr",
            "raw_text": "private document",
            "image_bytes": b"payload",
            "debug_path": "debug_captures/private.png",
            "api_key": "secret",
            "duration_ms": 20,
        }
    )

    assert safe == {"engine": "paddleocr", "duration_ms": 20}

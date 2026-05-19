"""Privacy-safe deployment report writer tests."""

from __future__ import annotations

import json

import pytest

from modules.deployment.readiness_models import (
    DependencyCheckResult,
    DeploymentReadinessReport,
    ReadinessStatus,
)
from modules.deployment.report_writer import (
    report_contains_sensitive_content,
    write_readiness_report,
)


def _report() -> DeploymentReadinessReport:
    return DeploymentReadinessReport(
        report_id="phase11-test",
        target_device="Raspberry Pi 4",
        checks=(
            DependencyCheckResult(
                check_id="network.online_optional",
                dependency_area="network",
                status=ReadinessStatus.DEGRADED,
                required_for_startup=False,
                message="Online services are unavailable; local fallback remains ready.",
                remediation="Connect internet to use online-first services.",
            ),
        ),
    )


def test_write_report_creates_json_and_summary_without_sensitive_fields(tmp_path) -> None:
    out = write_readiness_report(_report(), tmp_path)

    payload = json.loads((out / "readiness_report.json").read_text(encoding="utf-8"))
    summary = (out / "readiness_summary.md").read_text(encoding="utf-8")
    assert payload["overall_status"] == "degraded"
    assert "raw_text" not in json.dumps(payload)
    assert "translated_text" not in summary


def test_writer_rejects_accidental_sensitive_payload(tmp_path) -> None:
    assert report_contains_sensitive_content({"raw_text": "secret"}) is True
    report = _report()
    unsafe = report.to_dict()
    unsafe["raw_text"] = "secret"
    assert report_contains_sensitive_content(unsafe) is True

    with pytest.raises(FileExistsError):
        write_readiness_report(report, tmp_path)
        write_readiness_report(report, tmp_path)


def test_online_outage_reports_remain_privacy_safe(tmp_path) -> None:
    out = write_readiness_report(_report(), tmp_path)

    text = (out / "readiness_report.json").read_text(encoding="utf-8")
    assert "network.online_optional" in text
    assert '"contains_secrets": false' in text
    assert "debug_captures" not in text

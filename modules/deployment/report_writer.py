"""Privacy-safe deployment readiness report writing."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from modules.deployment.readiness_models import DeploymentReadinessReport


def make_report_id(now: datetime | None = None) -> str:
    active = now or datetime.now(timezone.utc)
    return active.strftime("%Y%m%d-%H%M%S-%f-phase11")


def reserve_report_directory(output_root: Path, report_id: str) -> Path:
    report_dir = output_root / report_id
    report_dir.mkdir(parents=True, exist_ok=False)
    return report_dir


def report_contains_sensitive_content(payload: object) -> bool:
    """Best-effort guard for accidental sensitive report fields."""
    forbidden = (
        "raw_text",
        "clean_text",
        "translated_text",
        "recognized_text",
        "image_bytes",
        "image_payload",
        "ocr_text",
        "secret",
        "token",
        "api_key",
        "password",
        "debug_captures",
        "private_debug_paths",
    )
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalized = str(key).lower()
            if normalized.startswith("contains_") and value is False:
                continue
            if any(term in normalized for term in forbidden):
                return True
            if report_contains_sensitive_content(value):
                return True
        return False
    if isinstance(payload, (list, tuple)):
        return any(report_contains_sensitive_content(item) for item in payload)
    if isinstance(payload, str):
        text = payload.lower()
        return any(term in text for term in forbidden if "_" in term)
    try:
        json.dumps(payload)
    except TypeError:
        return True
    return False


def build_summary_markdown(report: DeploymentReadinessReport) -> str:
    lines = [
        f"# Deployment Readiness Summary: {report.report_id}",
        "",
        f"- Overall status: {report.overall_status.value}",
        f"- Target device: {report.target_device}",
        f"- Startup mode: {report.startup_mode}",
        "",
        "## Checks",
    ]
    for check in report.checks:
        lines.append(f"- {check.check_id}: {check.status.value} - {check.message}")
    if report.recommended_actions:
        lines.extend(["", "## Recommended Actions"])
        lines.extend(f"- {action}" for action in report.recommended_actions)
    lines.extend(
        [
            "",
            "## Privacy",
            "- Report excludes user images, OCR text, translations, secrets, and private debug paths.",
            "",
        ]
    )
    return "\n".join(lines)


def write_readiness_report(
    report: DeploymentReadinessReport,
    output_root: Path,
) -> Path:
    payload = report.to_dict()
    if report_contains_sensitive_content(payload):
        raise ValueError("deployment report contains sensitive content")
    report_dir = reserve_report_directory(output_root, report.report_id)
    (report_dir / "readiness_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = build_summary_markdown(report)
    if report_contains_sensitive_content(summary):
        raise ValueError("deployment summary contains sensitive content")
    (report_dir / "readiness_summary.md").write_text(summary, encoding="utf-8")
    return report_dir

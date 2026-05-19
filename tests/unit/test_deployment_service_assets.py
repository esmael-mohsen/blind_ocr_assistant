"""Deployment service asset tests."""

from __future__ import annotations

from pathlib import Path

from modules.deployment.readiness_models import ReadinessStatus
from modules.deployment.service_assets import (
    inspect_service_assets,
    service_enablement_warning,
    validate_manual_run_script,
    validate_service_template,
)


ROOT = Path(__file__).resolve().parents[2]


def test_service_template_is_disabled_by_default_and_has_stop_behavior() -> None:
    result = validate_service_template(
        ROOT / "deploy" / "blind-ocr-assistant.service.template"
    )

    assert result.status is ReadinessStatus.READY
    assert result.required_for_startup is False


def test_inspect_service_assets_keeps_manual_startup_available() -> None:
    option = inspect_service_assets(
        template_path=ROOT / "deploy" / "blind-ocr-assistant.service.template",
        manual_script_path=ROOT / "scripts" / "run_assistant.sh",
    )

    assert option.enabled is False
    assert "manual startup script available" in option.notes


def test_manual_run_script_and_service_enablement_warning() -> None:
    script = validate_manual_run_script(ROOT / "scripts" / "run_assistant.sh")
    disabled = service_enablement_warning(False)
    enabled = service_enablement_warning(True)

    assert script.status is ReadinessStatus.READY
    assert disabled.status is ReadinessStatus.READY
    assert enabled.status is ReadinessStatus.MANUAL_VERIFICATION_NEEDED

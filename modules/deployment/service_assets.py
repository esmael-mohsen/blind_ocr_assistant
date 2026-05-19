"""Validation helpers for manual startup and optional service assets."""

from __future__ import annotations

from pathlib import Path

from modules.deployment.readiness_models import (
    DependencyCheckResult,
    ReadinessStatus,
    ServiceStartupMode,
    ServiceStartupOption,
)


def inspect_service_assets(
    *,
    template_path: Path,
    manual_script_path: Path,
) -> ServiceStartupOption:
    template_exists = template_path.exists()
    manual_exists = manual_script_path.exists()
    notes = []
    if template_exists:
        notes.append("service template available but disabled by default")
    else:
        notes.append("service template missing")
    if manual_exists:
        notes.append("manual startup script available")
    else:
        notes.append("manual startup script missing")
    return ServiceStartupOption(
        mode=ServiceStartupMode.SERVICE_TEMPLATE
        if template_exists
        else ServiceStartupMode.MANUAL_SCRIPT,
        enabled=False,
        template_path=str(template_path) if template_exists else "",
        manual_script_path=str(manual_script_path) if manual_exists else "",
        safe_stop_supported=template_contains_safe_stop(template_path)
        and manual_script_contains_safe_stop(manual_script_path),
        notes=tuple(notes),
    )


def validate_service_template(template_path: Path) -> DependencyCheckResult:
    if not template_path.exists():
        return DependencyCheckResult(
            check_id="service.template",
            dependency_area="service",
            status=ReadinessStatus.MANUAL_VERIFICATION_NEEDED,
            required_for_startup=False,
            message="Optional service template is not present.",
            remediation="Use manual startup or add the disabled service template.",
        )
    text = template_path.read_text(encoding="utf-8")
    forbidden = "systemctl enable" in text or "WantedBy=default.target" in text
    if forbidden:
        status = ReadinessStatus.BLOCKED
        message = "Service template appears to auto-enable startup."
        remediation = "Remove automatic enablement from the template."
    elif "ExecStop" not in text:
        status = ReadinessStatus.DEGRADED
        message = "Service template lacks explicit stop behavior."
        remediation = "Add ExecStop or documented systemd stop handling."
    else:
        status = ReadinessStatus.READY
        message = "Service template is optional and disabled by default."
        remediation = "Enable only after manual validation."
    return DependencyCheckResult(
        check_id="service.template",
        dependency_area="service",
        status=status,
        required_for_startup=False,
        message=message,
        remediation=remediation,
    )


def validate_manual_run_script(script_path: Path) -> DependencyCheckResult:
    if not script_path.exists():
        return DependencyCheckResult(
            check_id="service.manual_run_script",
            dependency_area="service",
            status=ReadinessStatus.BLOCKED,
            required_for_startup=True,
            message="Manual assistant startup script is missing.",
            remediation="Restore scripts/run_assistant.sh.",
        )
    text = script_path.read_text(encoding="utf-8")
    has_python = "python" in text and "main.py" in text
    has_trap = "trap" in text and ("TERM" in text or "INT" in text)
    status = ReadinessStatus.READY if has_python and has_trap else ReadinessStatus.DEGRADED
    return DependencyCheckResult(
        check_id="service.manual_run_script",
        dependency_area="service",
        status=status,
        required_for_startup=True,
        message="Manual run script supports startup and safe stop."
        if status is ReadinessStatus.READY
        else "Manual run script needs safe-stop review.",
        remediation="No action needed."
        if status is ReadinessStatus.READY
        else "Add signal traps and main.py execution to the manual run script.",
    )


def service_enablement_warning(enabled: bool) -> DependencyCheckResult:
    return DependencyCheckResult(
        check_id="service.enablement",
        dependency_area="service",
        status=ReadinessStatus.MANUAL_VERIFICATION_NEEDED
        if enabled
        else ReadinessStatus.READY,
        required_for_startup=False,
        message="Service startup is disabled by default."
        if not enabled
        else "Service startup is enabled and requires deployment validation.",
        remediation="No action needed."
        if not enabled
        else "Confirm full diagnostics and privacy settings before unattended use.",
        safe_metadata={"enabled": enabled},
    )


def template_contains_safe_stop(template_path: Path) -> bool:
    return template_path.exists() and "ExecStop" in template_path.read_text(
        encoding="utf-8"
    )


def manual_script_contains_safe_stop(script_path: Path) -> bool:
    if not script_path.exists():
        return False
    text = script_path.read_text(encoding="utf-8")
    return "trap" in text and ("TERM" in text or "INT" in text)

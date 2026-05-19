"""Deployment readiness orchestration."""

from __future__ import annotations

from pathlib import Path

from config import AppConfig, load_config
from modules.deployment.log_retention import (
    build_log_retention_policy,
    plan_log_retention,
    summarize_log_retention_decisions,
)
from modules.deployment.readiness_checks import (
    NetworkChecker,
    build_lightweight_startup_checks,
    check_camera_resource_release,
    check_camera_rgb_depth_readiness,
    check_emergency_ocr_readiness,
    check_microphone_command_input_readiness,
    check_no_internet_startup,
    check_preferred_offline_ocr_readiness,
    check_privacy_risk_debug_settings,
    check_speaker_output_readiness,
    check_temporary_internet_failure_and_recovery,
    startup_spoken_summary,
)
from modules.deployment.readiness_models import (
    DependencyCheckResult,
    DeploymentReadinessReport,
    ReadinessStatus,
)
from modules.deployment.report_writer import make_report_id, write_readiness_report
from modules.deployment.service_assets import (
    inspect_service_assets,
    service_enablement_warning,
    validate_manual_run_script,
    validate_service_template,
)


def run_lightweight_startup_diagnostics(
    config: AppConfig | None = None,
    *,
    output_dir: Path | None = None,
    offline: bool = False,
    network_checker: NetworkChecker | None = None,
    local_fallback_available: bool | None = None,
) -> DeploymentReadinessReport:
    active = config or load_config()
    checks = build_lightweight_startup_checks(
        active,
        network_checker=network_checker,
        offline=offline,
        local_fallback_available=local_fallback_available,
    )
    report = DeploymentReadinessReport(
        report_id=make_report_id(),
        target_device="Raspberry Pi 4",
        startup_mode="manual",
        checks=checks,
        recommended_actions=_recommended_actions(checks),
    )
    if output_dir is not None:
        write_readiness_report(report, output_dir)
    return report


def run_full_deployment_diagnostics(
    config: AppConfig | None = None,
    *,
    output_dir: Path | None = None,
    offline: bool = False,
    skip_hardware: bool = False,
    network_checker: NetworkChecker | None = None,
    local_fallback_available: bool | None = None,
    camera_source=None,
    speaker_probe=None,
    microphone_probe=None,
    paddle_package_available: bool | None = None,
    paddle_load_probe=None,
    tesseract_executable_available: bool | None = None,
    tesseract_language_data_available: bool | None = None,
    recovery_failure_probe=None,
    recovery_restored_probe=None,
    service_enabled: bool = False,
) -> DeploymentReadinessReport:
    active = config or load_config()
    checks = list(
        build_lightweight_startup_checks(
            active,
            network_checker=network_checker,
            offline=offline,
            local_fallback_available=local_fallback_available,
        )
    )
    camera = check_camera_rgb_depth_readiness(
        camera_source=camera_source,
        skip_hardware=skip_hardware,
    )
    checks.append(camera)
    checks.append(
        check_camera_resource_release(None if skip_hardware else camera_source)
    )
    checks.append(
        check_speaker_output_readiness(
            output_probe=speaker_probe,
            skip_hardware=skip_hardware,
        )
    )
    checks.append(
        check_microphone_command_input_readiness(
            input_probe=microphone_probe,
            skip_hardware=skip_hardware,
        )
    )
    checks.append(
        check_preferred_offline_ocr_readiness(
            package_available=paddle_package_available,
            load_probe=paddle_load_probe,
        )
    )
    checks.append(
        check_emergency_ocr_readiness(
            executable_available=tesseract_executable_available,
            language_data_available=tesseract_language_data_available,
        )
    )
    fallback_ready = local_fallback_available is not False
    if offline:
        checks.append(check_no_internet_startup(local_fallback_ready=fallback_ready))
    if recovery_failure_probe is not None and recovery_restored_probe is not None:
        checks.extend(
            check_temporary_internet_failure_and_recovery(
                failure_probe=recovery_failure_probe,
                recovery_probe=recovery_restored_probe,
            )
        )
    template_path = Path("deploy/blind-ocr-assistant.service.template")
    manual_script_path = Path("scripts/run_assistant.sh")
    checks.append(validate_manual_run_script(manual_script_path))
    checks.append(validate_service_template(template_path))
    checks.append(service_enablement_warning(service_enabled))
    checks.append(check_privacy_risk_debug_settings(active))
    policy = build_log_retention_policy(active.logs_dir)
    decisions = plan_log_retention(active.logs_dir, budget_mb=policy.normal_log_budget_mb)
    checks.append(
        DependencyCheckResult(
            check_id="logs.rotate_prune_plan",
            dependency_area="logs",
            status=ReadinessStatus.READY
            if not decisions
            else ReadinessStatus.DEGRADED,
            required_for_startup=False,
            message="No log rotation or pruning is needed."
            if not decisions
            else "Normal logs need rotation or pruning.",
            remediation="No action needed."
            if not decisions
            else "Prune oldest normal logs to stay within budget.",
            safe_metadata=summarize_log_retention_decisions(decisions),
        )
    )
    service = inspect_service_assets(
        template_path=template_path,
        manual_script_path=manual_script_path,
    )
    report = DeploymentReadinessReport(
        report_id=make_report_id(),
        target_device="Raspberry Pi 4",
        startup_mode="manual",
        checks=tuple(checks),
        recommended_actions=_recommended_actions(checks),
        service_startup=service,
        log_retention=policy,
    )
    if output_dir is not None:
        write_readiness_report(report, output_dir)
    return report


def run_safe_stop_diagnostics(
    *,
    start_stop_probe,
    cycles: int = 2,
) -> DependencyCheckResult:
    results = [bool(start_stop_probe()) for _ in range(cycles)]
    ok = all(results)
    return DependencyCheckResult(
        check_id="service.safe_stop_cycles",
        dependency_area="service",
        status=ReadinessStatus.READY if ok else ReadinessStatus.BLOCKED,
        required_for_startup=False,
        message="Repeated start/stop cycles released resources."
        if ok
        else "Repeated start/stop cycles did not release resources.",
        remediation="No action needed."
        if ok
        else "Fix shutdown cleanup before service-style deployment.",
        safe_metadata={"cycles": cycles, "successful_cycles": sum(results)},
    )


def format_report_for_cli(report: DeploymentReadinessReport) -> str:
    lines = [
        f"Overall status: {report.overall_status.value}",
        startup_spoken_summary(report.overall_status),
        "Checks:",
    ]
    for check in report.checks:
        lines.append(f"- {check.check_id}: {check.status.value} - {check.message}")
    if report.recommended_actions:
        lines.append("Recommended actions:")
        lines.extend(f"- {action}" for action in report.recommended_actions)
    return "\n".join(lines)


def _recommended_actions(checks) -> tuple[str, ...]:
    actions = []
    for check in checks:
        if check.status.value != "ready" and check.remediation not in actions:
            actions.append(check.remediation)
    return tuple(actions)

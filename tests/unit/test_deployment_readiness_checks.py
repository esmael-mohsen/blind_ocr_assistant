"""Deployment readiness check tests."""

from __future__ import annotations

from pathlib import Path

from config import AppConfig
from modules.deployment.readiness_checks import (
    build_lightweight_startup_checks,
    check_camera_resource_release,
    check_camera_rgb_depth_readiness,
    check_emergency_ocr_readiness,
    check_microphone_command_input_readiness,
    check_network_availability,
    check_no_internet_startup,
    check_preferred_offline_ocr_readiness,
    check_privacy_risk_debug_settings,
    check_speaker_output_readiness,
    check_temporary_internet_failure_and_recovery,
    offline_recovery_spoken_summary,
    startup_spoken_summary,
)
from modules.deployment.readiness_models import ReadinessStatus, most_severe_status


def _config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        logs_dir=tmp_path / "logs",
        debug_captures_dir=tmp_path / "debug",
        benchmark_results_dir=tmp_path / "benchmark",
        config_dir=tmp_path / "config",
    )


def test_lightweight_startup_ready_when_required_local_checks_pass(tmp_path) -> None:
    checks = build_lightweight_startup_checks(
        _config(tmp_path),
        network_checker=lambda: True,
        local_fallback_available=True,
    )

    assert most_severe_status([check.status for check in checks]) is ReadinessStatus.READY


def test_lightweight_startup_degraded_offline_when_local_fallback_ready(tmp_path) -> None:
    checks = build_lightweight_startup_checks(
        _config(tmp_path),
        offline=True,
        local_fallback_available=True,
    )

    assert most_severe_status([check.status for check in checks]) is ReadinessStatus.DEGRADED
    assert any(check.check_id == "network.online_optional" for check in checks)


def test_lightweight_startup_blocked_when_local_fallback_missing(tmp_path) -> None:
    checks = build_lightweight_startup_checks(
        _config(tmp_path),
        network_checker=lambda: True,
        local_fallback_available=False,
    )

    assert most_severe_status([check.status for check in checks]) is ReadinessStatus.BLOCKED


def test_manual_verification_summary_is_non_visual() -> None:
    assert "manual verification" in startup_spoken_summary(
        ReadinessStatus.MANUAL_VERIFICATION_NEEDED
    )


def test_network_checker_reports_optional_degraded_offline() -> None:
    result = check_network_availability(offline=True)

    assert result.status is ReadinessStatus.DEGRADED
    assert result.required_for_startup is False


def test_no_internet_startup_uses_local_fallback_when_ready() -> None:
    result = check_no_internet_startup(local_fallback_ready=True)

    assert result.status is ReadinessStatus.DEGRADED
    assert result.required_for_startup is False
    assert "local fallback" in result.message


class FakeCamera:
    supports_depth = False

    def __init__(self) -> None:
        self.released = False

    def open(self) -> bool:
        return True

    def capture_frame(self):
        return object()

    def release(self) -> None:
        self.released = True


def test_camera_rgb_only_is_degraded_and_resource_release_confirmed() -> None:
    camera = FakeCamera()

    result = check_camera_rgb_depth_readiness(camera_source=camera)
    release = check_camera_resource_release(camera)

    assert result.status is ReadinessStatus.DEGRADED
    assert result.safe_metadata["depth_ready"] is False
    assert release.status is ReadinessStatus.READY


def test_audio_output_and_command_input_can_need_manual_verification() -> None:
    speaker = check_speaker_output_readiness(output_probe=lambda: False)
    microphone = check_microphone_command_input_readiness(input_probe=lambda: False)

    assert speaker.status is ReadinessStatus.MANUAL_VERIFICATION_NEEDED
    assert microphone.status is ReadinessStatus.MANUAL_VERIFICATION_NEEDED


def test_offline_ocr_readiness_avoids_heavy_load_without_probe() -> None:
    result = check_preferred_offline_ocr_readiness(package_available=True)

    assert result.status is ReadinessStatus.MANUAL_VERIFICATION_NEEDED
    assert result.safe_metadata["package_present"] is True


def test_emergency_ocr_requires_executable_and_language_data() -> None:
    blocked = check_emergency_ocr_readiness(
        executable_available=True,
        language_data_available=False,
    )
    ready = check_emergency_ocr_readiness(
        executable_available=True,
        language_data_available=True,
    )

    assert blocked.status is ReadinessStatus.BLOCKED
    assert ready.status is ReadinessStatus.READY


def test_temporary_internet_failure_and_restored_connectivity() -> None:
    failure, recovery = check_temporary_internet_failure_and_recovery(
        failure_probe=lambda: False,
        recovery_probe=lambda: True,
    )

    assert failure.status is ReadinessStatus.DEGRADED
    assert recovery.status is ReadinessStatus.READY
    assert "local reading fallback" in offline_recovery_spoken_summary(
        ReadinessStatus.DEGRADED
    )


def test_privacy_risk_debug_settings_are_reported(tmp_path) -> None:
    config = AppConfig(
        logs_dir=tmp_path / "logs",
        debug_captures_dir=tmp_path / "debug",
        benchmark_results_dir=tmp_path / "benchmark",
        config_dir=tmp_path / "config",
        debug_save_images=True,
    )

    result = check_privacy_risk_debug_settings(config)

    assert result.status is ReadinessStatus.DEGRADED
    assert result.safe_metadata["debug_save_images"] is True

"""Deployment diagnostics integration tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from config import AppConfig
from modules.deployment.diagnostics import (
    run_safe_stop_diagnostics,
    run_full_deployment_diagnostics,
    run_lightweight_startup_diagnostics,
)
from modules.deployment.readiness_models import ReadinessStatus


def _config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        logs_dir=tmp_path / "logs",
        debug_captures_dir=tmp_path / "debug",
        benchmark_results_dir=tmp_path / "benchmark",
        config_dir=tmp_path / "config",
    )


def test_lightweight_diagnostics_writes_privacy_safe_report(tmp_path) -> None:
    report = run_lightweight_startup_diagnostics(
        _config(tmp_path),
        output_dir=tmp_path / "deployment_diagnostics",
        network_checker=lambda: False,
        local_fallback_available=True,
    )

    assert report.overall_status is ReadinessStatus.DEGRADED
    report_files = list((tmp_path / "deployment_diagnostics").glob("*/readiness_report.json"))
    assert report_files
    assert "raw_text" not in report_files[0].read_text(encoding="utf-8")


def test_cli_lightweight_mode_smoke_writes_report(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/pi_deployment_check.py",
            "--offline",
            "--output-dir",
            str(tmp_path / "out"),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert "Overall status:" in result.stdout
    assert "Mode: lightweight startup checks" in result.stdout
    assert (tmp_path / "out").exists()


class FakeCamera:
    supports_depth = True

    def __init__(self) -> None:
        self.released = False

    def open(self) -> bool:
        return True

    def capture_frame(self):
        return object()

    def release(self) -> None:
        self.released = True


def test_full_diagnostics_with_mocked_hardware_and_ocr(tmp_path) -> None:
    report = run_full_deployment_diagnostics(
        _config(tmp_path),
        output_dir=tmp_path / "full",
        network_checker=lambda: True,
        local_fallback_available=True,
        camera_source=FakeCamera(),
        speaker_probe=lambda: True,
        microphone_probe=lambda: True,
        paddle_package_available=True,
        paddle_load_probe=lambda: True,
        tesseract_executable_available=True,
        tesseract_language_data_available=True,
    )

    assert report.overall_status is ReadinessStatus.READY
    assert any(check.check_id == "camera.rgb_depth" for check in report.checks)


def test_full_diagnostics_skip_hardware_records_manual_verification(tmp_path) -> None:
    report = run_full_deployment_diagnostics(
        _config(tmp_path),
        skip_hardware=True,
        network_checker=lambda: True,
        local_fallback_available=True,
        paddle_package_available=True,
        paddle_load_probe=lambda: True,
        tesseract_executable_available=True,
        tesseract_language_data_available=True,
    )

    assert report.overall_status is ReadinessStatus.MANUAL_VERIFICATION_NEEDED
    assert any(
        check.status is ReadinessStatus.MANUAL_VERIFICATION_NEEDED
        for check in report.checks
    )


def test_full_diagnostics_records_offline_and_recovery_behavior(tmp_path) -> None:
    report = run_full_deployment_diagnostics(
        _config(tmp_path),
        network_checker=lambda: False,
        local_fallback_available=True,
        skip_hardware=True,
        offline=True,
        paddle_package_available=True,
        paddle_load_probe=lambda: True,
        tesseract_executable_available=True,
        tesseract_language_data_available=True,
        recovery_failure_probe=lambda: False,
        recovery_restored_probe=lambda: True,
    )

    check_ids = {check.check_id for check in report.checks}
    assert "network.no_internet_startup" in check_ids
    assert "network.temporary_failure" in check_ids
    assert "network.restored_connectivity" in check_ids


def test_safe_stop_and_resource_release_integration() -> None:
    result = run_safe_stop_diagnostics(start_stop_probe=lambda: True, cycles=3)

    assert result.status is ReadinessStatus.READY
    assert result.safe_metadata["successful_cycles"] == 3

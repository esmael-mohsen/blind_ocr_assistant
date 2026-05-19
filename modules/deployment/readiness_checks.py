"""Deployment readiness checks with lightweight startup defaults."""

from __future__ import annotations

from collections.abc import Callable
import importlib
import importlib.util
import shutil
import socket
import time
from typing import Any

from config import AppConfig, load_config
from modules.deployment.log_retention import build_log_retention_policy
from modules.deployment.readiness_models import (
    DependencyCheckResult,
    HardwareCheckResult,
    ReadinessStatus,
)


NetworkChecker = Callable[[], bool]
Probe = Callable[[], bool]


def check_configuration(config: AppConfig | None = None) -> DependencyCheckResult:
    active = config or load_config()
    missing_languages = not active.languages
    return DependencyCheckResult(
        check_id="config.load",
        dependency_area="config",
        status=ReadinessStatus.BLOCKED
        if missing_languages
        else ReadinessStatus.READY,
        required_for_startup=True,
        message="Configuration loaded with deployment-safe defaults."
        if not missing_languages
        else "Configuration has no supported languages.",
        remediation="No action needed."
        if not missing_languages
        else "Restore Arabic and English language configuration.",
        spoken_message="Configuration is ready."
        if not missing_languages
        else "Configuration is blocked.",
        safe_metadata={"language_count": len(active.languages)},
    )


def check_runtime_folders(
    config: AppConfig | None = None,
    *,
    create: bool = True,
) -> DependencyCheckResult:
    active = config or load_config()
    missing: list[str] = []
    for folder in active.runtime_dirs:
        try:
            if create:
                folder.mkdir(parents=True, exist_ok=True)
            if not folder.exists():
                missing.append(folder.name)
        except OSError:
            missing.append(folder.name)
    return DependencyCheckResult(
        check_id="folders.runtime",
        dependency_area="folders",
        status=ReadinessStatus.BLOCKED if missing else ReadinessStatus.READY,
        required_for_startup=True,
        message="Runtime folders are ready."
        if not missing
        else "One or more runtime folders are unavailable.",
        remediation="No action needed."
        if not missing
        else "Create writable runtime folders before starting the assistant.",
        spoken_message="Runtime folders are ready."
        if not missing
        else "Runtime folders are blocked.",
        safe_metadata={"missing_folder_names": missing},
    )


def check_privacy_settings(config: AppConfig | None = None) -> DependencyCheckResult:
    active = config or load_config()
    risky = active.debug_save_images or active.sensitive_text_logging
    return DependencyCheckResult(
        check_id="privacy.defaults",
        dependency_area="privacy",
        status=ReadinessStatus.DEGRADED if risky else ReadinessStatus.READY,
        required_for_startup=False,
        message="Privacy-sensitive debug settings are disabled."
        if not risky
        else "Privacy-sensitive debug settings are enabled.",
        remediation="No action needed."
        if not risky
        else "Disable debug image saving and sensitive text logging for normal use.",
        spoken_message="Privacy settings are ready."
        if not risky
        else "Privacy settings need review.",
        safe_metadata={
            "debug_save_images": active.debug_save_images,
            "sensitive_text_logging": active.sensitive_text_logging,
        },
    )


def check_privacy_risk_debug_settings(
    config: AppConfig | None = None,
) -> DependencyCheckResult:
    return check_privacy_settings(config)


def check_basic_dependencies(
    packages: tuple[str, ...] = ("modules.camera", "modules.ocr", "modules.voice"),
) -> DependencyCheckResult:
    missing: list[str] = []
    for package in packages:
        try:
            importlib.import_module(package)
        except Exception:
            missing.append(package.rsplit(".", 1)[-1])
    return DependencyCheckResult(
        check_id="dependencies.basic_modules",
        dependency_area="config",
        status=ReadinessStatus.BLOCKED if missing else ReadinessStatus.READY,
        required_for_startup=True,
        message="Core assistant module boundaries are importable."
        if not missing
        else "Required assistant module boundaries are missing.",
        remediation="No action needed."
        if not missing
        else "Reinstall the project or restore missing modules.",
        spoken_message="Core modules are ready." if not missing else "Core modules are blocked.",
        safe_metadata={"missing_modules": missing},
    )


def check_network_availability(
    *,
    network_checker: NetworkChecker | None = None,
    offline: bool = False,
) -> DependencyCheckResult:
    online = False if offline else _default_network_check() if network_checker is None else network_checker()
    return DependencyCheckResult(
        check_id="network.online_optional",
        dependency_area="network",
        status=ReadinessStatus.READY if online else ReadinessStatus.DEGRADED,
        required_for_startup=False,
        message="Online services appear reachable."
        if online
        else "Online services are unavailable; local fallback can be used.",
        remediation="No action needed."
        if online
        else "Connect to the internet to use online-first services.",
        spoken_message="Online services are ready."
        if online
        else "Offline mode is available.",
        safe_metadata={"online": online},
    )


def check_no_internet_startup(
    *,
    local_fallback_ready: bool,
) -> DependencyCheckResult:
    return DependencyCheckResult(
        check_id="network.no_internet_startup",
        dependency_area="network",
        status=ReadinessStatus.DEGRADED
        if local_fallback_ready
        else ReadinessStatus.BLOCKED,
        required_for_startup=not local_fallback_ready,
        message="No-internet startup can continue with local fallback."
        if local_fallback_ready
        else "No-internet startup is blocked because local fallback is unavailable.",
        remediation="No action needed for offline use."
        if local_fallback_ready
        else "Install local OCR and speech fallbacks before offline deployment.",
        spoken_message="Offline reading fallback is available."
        if local_fallback_ready
        else "Offline reading fallback is blocked.",
        safe_metadata={"local_fallback_ready": local_fallback_ready},
    )


def check_temporary_internet_failure_and_recovery(
    *,
    failure_probe: NetworkChecker,
    recovery_probe: NetworkChecker,
) -> tuple[DependencyCheckResult, DependencyCheckResult]:
    failed_online = not failure_probe()
    restored = recovery_probe()
    failure = DependencyCheckResult(
        check_id="network.temporary_failure",
        dependency_area="network",
        status=ReadinessStatus.DEGRADED if failed_online else ReadinessStatus.READY,
        required_for_startup=False,
        message="Temporary internet failure triggers local fallback."
        if failed_online
        else "Temporary internet failure was not reproduced.",
        remediation="Use local fallback while online service is unavailable."
        if failed_online
        else "No action needed.",
        spoken_message="Online service failed, using local fallback."
        if failed_online
        else "Online service remains available.",
        safe_metadata={"failure_reproduced": failed_online},
    )
    recovery = DependencyCheckResult(
        check_id="network.restored_connectivity",
        dependency_area="network",
        status=ReadinessStatus.READY
        if restored
        else ReadinessStatus.MANUAL_VERIFICATION_NEEDED,
        required_for_startup=False,
        message="Restored connectivity can be detected without restart."
        if restored
        else "Restored connectivity needs manual verification.",
        remediation="No action needed."
        if restored
        else "Reconnect internet and rerun diagnostics.",
        spoken_message="Online service can be used again."
        if restored
        else "Online recovery needs manual verification.",
        safe_metadata={"restored": restored},
    )
    return failure, recovery


def check_local_fallback_readiness(
    *,
    paddle_available: bool | None = None,
    tesseract_available: bool | None = None,
) -> DependencyCheckResult:
    paddle = _package_available("paddleocr") if paddle_available is None else paddle_available
    tesseract = _tesseract_available() if tesseract_available is None else tesseract_available
    ready = paddle or tesseract
    return DependencyCheckResult(
        check_id="ocr.local_fallback_basic",
        dependency_area="paddleocr" if paddle else "tesseract",
        status=ReadinessStatus.READY if ready else ReadinessStatus.BLOCKED,
        required_for_startup=True,
        message="At least one local OCR fallback appears available."
        if ready
        else "No local OCR fallback appears available.",
        remediation="No action needed."
        if ready
        else "Install PaddleOCR or Tesseract with Arabic and English data.",
        spoken_message="Local reading fallback is ready."
        if ready
        else "Local reading fallback is blocked.",
        safe_metadata={"paddleocr_present": paddle, "tesseract_present": tesseract},
    )


def check_log_retention(config: AppConfig | None = None) -> DependencyCheckResult:
    active = config or load_config()
    policy = build_log_retention_policy(active.logs_dir)
    return DependencyCheckResult(
        check_id="logs.retention_budget",
        dependency_area="logs",
        status=policy.status,
        required_for_startup=False,
        message="Normal logs are within the deployment budget."
        if policy.status is ReadinessStatus.READY
        else "Normal log retention needs maintainer review.",
        remediation="No action needed."
        if policy.status is ReadinessStatus.READY
        else "Rotate or prune normal logs while preserving privacy.",
        spoken_message="Logs are ready."
        if policy.status is ReadinessStatus.READY
        else "Logs need review.",
        safe_metadata={
            "budget_mb": policy.normal_log_budget_mb,
            "current_usage_mb": policy.current_usage_mb,
            "rotation_action": policy.rotation_action,
        },
    )


def build_lightweight_startup_checks(
    config: AppConfig | None = None,
    *,
    network_checker: NetworkChecker | None = None,
    offline: bool = False,
    local_fallback_available: bool | None = None,
) -> tuple[DependencyCheckResult, ...]:
    fallback = check_local_fallback_readiness(
        paddle_available=local_fallback_available,
        tesseract_available=False if local_fallback_available is not None else None,
    )
    return (
        check_configuration(config),
        check_runtime_folders(config),
        check_privacy_settings(config),
        check_basic_dependencies(),
        check_network_availability(network_checker=network_checker, offline=offline),
        fallback,
        check_log_retention(config),
    )


def startup_spoken_summary(status: ReadinessStatus) -> str:
    if status is ReadinessStatus.READY:
        return "Deployment readiness is ready."
    if status is ReadinessStatus.DEGRADED:
        return "Deployment readiness is degraded, but the assistant can continue."
    if status is ReadinessStatus.MANUAL_VERIFICATION_NEEDED:
        return "Deployment readiness needs manual verification."
    return "Deployment readiness is blocked. Fix the reported issue before use."


def offline_recovery_spoken_summary(status: ReadinessStatus) -> str:
    if status is ReadinessStatus.READY:
        return "Online services are available."
    if status is ReadinessStatus.DEGRADED:
        return "Internet is unavailable. I will use local reading fallback."
    if status is ReadinessStatus.MANUAL_VERIFICATION_NEEDED:
        return "Internet recovery needs manual verification."
    return "Offline fallback is blocked. Fix local reading dependencies."


def manual_hardware_result(check_id: str, area: str) -> HardwareCheckResult:
    return HardwareCheckResult(
        check_id=check_id,
        hardware_area=area,
        status=ReadinessStatus.MANUAL_VERIFICATION_NEEDED,
        message=f"{area.title()} requires manual verification on Raspberry Pi hardware.",
        spoken_message=f"{area.title()} needs manual verification.",
        remediation="Run full diagnostics on the target Raspberry Pi.",
    )


def check_camera_rgb_depth_readiness(
    *,
    camera_source: Any | None = None,
    skip_hardware: bool = False,
) -> HardwareCheckResult:
    if skip_hardware or camera_source is None:
        return manual_hardware_result("camera.rgb_depth", "camera")
    started = time.monotonic()
    opened = False
    try:
        opened = bool(camera_source.open())
        if not opened:
            return HardwareCheckResult(
                check_id="camera.rgb_depth",
                hardware_area="camera",
                status=ReadinessStatus.BLOCKED,
                message="Camera could not be opened.",
                spoken_message="Camera is blocked.",
                remediation="Check camera connection and permissions.",
                duration_ms=timed_result(started),
            )
        camera_source.capture_frame()
        supports_depth = bool(getattr(camera_source, "supports_depth", False))
        return HardwareCheckResult(
            check_id="camera.rgb_depth",
            hardware_area="camera",
            status=ReadinessStatus.READY
            if supports_depth
            else ReadinessStatus.DEGRADED,
            message="Camera RGB and depth are ready."
            if supports_depth
            else "Camera RGB is ready; depth is unavailable.",
            spoken_message="Camera is ready."
            if supports_depth
            else "Camera is available in RGB-only mode.",
            remediation="No action needed."
            if supports_depth
            else "Use RGB-only mode or reconnect a depth-capable camera.",
            duration_ms=timed_result(started),
            safe_metadata={"rgb_ready": True, "depth_ready": supports_depth},
        )
    except Exception:
        return HardwareCheckResult(
            check_id="camera.rgb_depth",
            hardware_area="camera",
            status=ReadinessStatus.BLOCKED,
            message="Camera capture failed during diagnostics.",
            spoken_message="Camera diagnostics failed.",
            remediation="Reconnect the camera and retry diagnostics.",
            duration_ms=timed_result(started),
        )
    finally:
        if opened and hasattr(camera_source, "release"):
            camera_source.release()


def check_camera_resource_release(camera_source: Any | None) -> HardwareCheckResult:
    if camera_source is None:
        return manual_hardware_result("camera.resource_release", "resources")
    released = bool(getattr(camera_source, "released", False))
    return HardwareCheckResult(
        check_id="camera.resource_release",
        hardware_area="resources",
        status=ReadinessStatus.READY if released else ReadinessStatus.BLOCKED,
        message="Camera resource release was confirmed."
        if released
        else "Camera resource release could not be confirmed.",
        spoken_message="Camera resources were released."
        if released
        else "Camera resources need review.",
        remediation="No action needed."
        if released
        else "Stop the assistant and verify camera release behavior.",
        safe_metadata={"released": released},
    )


def check_speaker_output_readiness(
    *,
    output_probe: Probe | None = None,
    skip_hardware: bool = False,
) -> HardwareCheckResult:
    if skip_hardware or output_probe is None:
        return manual_hardware_result("audio.speaker_output", "speaker")
    ok = output_probe()
    return HardwareCheckResult(
        check_id="audio.speaker_output",
        hardware_area="speaker",
        status=ReadinessStatus.READY
        if ok
        else ReadinessStatus.MANUAL_VERIFICATION_NEEDED,
        message="Speaker output probe completed."
        if ok
        else "Speaker output needs manual verification.",
        spoken_message="Speaker output is ready."
        if ok
        else "Speaker output needs manual verification.",
        remediation="No action needed."
        if ok
        else "Play the TTS smoke test and confirm it is audible.",
    )


def check_microphone_command_input_readiness(
    *,
    input_probe: Probe | None = None,
    skip_hardware: bool = False,
) -> HardwareCheckResult:
    if skip_hardware or input_probe is None:
        return manual_hardware_result("audio.microphone_input", "microphone")
    ok = input_probe()
    return HardwareCheckResult(
        check_id="audio.microphone_input",
        hardware_area="microphone",
        status=ReadinessStatus.READY
        if ok
        else ReadinessStatus.MANUAL_VERIFICATION_NEEDED,
        message="Microphone command-input probe completed."
        if ok
        else "Microphone input needs manual verification.",
        spoken_message="Microphone input is ready."
        if ok
        else "Microphone input needs manual verification.",
        remediation="No action needed."
        if ok
        else "Run command recognition on the target Raspberry Pi.",
    )


def check_preferred_offline_ocr_readiness(
    *,
    package_available: bool | None = None,
    load_probe: Probe | None = None,
) -> DependencyCheckResult:
    available = _package_available("paddleocr") if package_available is None else package_available
    if not available:
        status = ReadinessStatus.DEGRADED
        message = "Preferred offline OCR package is not installed."
        remediation = "Install PaddleOCR for local accuracy fallback."
    elif load_probe is None:
        status = ReadinessStatus.MANUAL_VERIFICATION_NEEDED
        message = "Preferred offline OCR package is present but not loaded in lightweight checks."
        remediation = "Run full diagnostics on Raspberry Pi to verify model loading."
    elif load_probe():
        status = ReadinessStatus.READY
        message = "Preferred offline OCR readiness was verified."
        remediation = "No action needed."
    else:
        status = ReadinessStatus.BLOCKED
        message = "Preferred offline OCR failed the load probe."
        remediation = "Repair PaddleOCR installation or use emergency OCR fallback."
    return DependencyCheckResult(
        check_id="ocr.paddleocr_full",
        dependency_area="paddleocr",
        status=status,
        required_for_startup=False,
        message=message,
        remediation=remediation,
        safe_metadata={"package_present": available},
    )


def check_emergency_ocr_readiness(
    *,
    executable_available: bool | None = None,
    language_data_available: bool | None = None,
) -> DependencyCheckResult:
    executable = _tesseract_available() if executable_available is None else executable_available
    language_data = (
        _tesseract_language_data_available()
        if language_data_available is None
        else language_data_available
    )
    ready = executable and language_data
    return DependencyCheckResult(
        check_id="ocr.tesseract_full",
        dependency_area="tesseract",
        status=ReadinessStatus.READY if ready else ReadinessStatus.BLOCKED,
        required_for_startup=False,
        message="Emergency OCR fallback is ready."
        if ready
        else "Emergency OCR fallback is missing executable or language data.",
        remediation="No action needed."
        if ready
        else "Install Tesseract with Arabic and English language data.",
        safe_metadata={
            "executable_present": executable,
            "language_data_present": language_data,
        },
    )


def timed_result(started: float) -> int:
    return max(0, int((time.monotonic() - started) * 1000))


def _default_network_check() -> bool:
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=1.0):
            return True
    except OSError:
        return False


def _package_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def _tesseract_language_data_available() -> bool:
    if shutil.which("tesseract") is None:
        return False
    try:
        import subprocess

        completed = subprocess.run(
            ["tesseract", "--list-langs"],
            check=False,
            text=True,
            capture_output=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    langs = set(completed.stdout.split())
    return {"ara", "eng"}.issubset(langs)

"""Readiness result models for Raspberry Pi deployment diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class ReadinessStatus(str, Enum):
    """Canonical deployment readiness states."""

    READY = "ready"
    DEGRADED = "degraded"
    MANUAL_VERIFICATION_NEEDED = "manual_verification_needed"
    BLOCKED = "blocked"


_STATUS_SEVERITY = {
    ReadinessStatus.READY: 0,
    ReadinessStatus.DEGRADED: 1,
    ReadinessStatus.MANUAL_VERIFICATION_NEEDED: 2,
    ReadinessStatus.BLOCKED: 3,
}


class ServiceStartupMode(str, Enum):
    MANUAL_SCRIPT = "manual_script"
    SERVICE_TEMPLATE = "service_template"
    SERVICE_ENABLED = "service_enabled"


def most_severe_status(statuses: list[ReadinessStatus]) -> ReadinessStatus:
    """Return the most severe status using the Phase 11 ordering."""
    if not statuses:
        return ReadinessStatus.MANUAL_VERIFICATION_NEEDED
    return max(statuses, key=lambda status: _STATUS_SEVERITY[status])


def status_is_blocking(status: ReadinessStatus) -> bool:
    return status is ReadinessStatus.BLOCKED


def sanitize_safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Remove sensitive or path-like metadata from report-safe dictionaries."""
    if not metadata:
        return {}
    forbidden_fragments = (
        "raw_text",
        "clean_text",
        "translated_text",
        "recognized_text",
        "speech_text",
        "image",
        "frame",
        "audio_sample",
        "secret",
        "token",
        "password",
        "api_key",
        "debug_path",
        "private_path",
        "path",
        "payload",
        "bytes",
    )
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        normalized = key.lower()
        if normalized in {"debug_save_images", "sensitive_text_logging"}:
            safe[key] = bool(value)
            continue
        if any(fragment in normalized for fragment in forbidden_fragments):
            continue
        if isinstance(value, Path):
            continue
        if isinstance(value, bytes):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        elif isinstance(value, (list, tuple)):
            safe[key] = [
                item
                for item in value
                if isinstance(item, (str, int, float, bool)) or item is None
            ]
        elif isinstance(value, dict):
            nested = sanitize_safe_metadata(value)
            if nested:
                safe[key] = nested
    return safe


@dataclass(frozen=True)
class HardwareCheckResult:
    check_id: str
    hardware_area: str
    status: ReadinessStatus
    message: str
    spoken_message: str
    remediation: str
    duration_ms: int = 0
    safe_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_safe_metadata(self.safe_metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "hardware_area": self.hardware_area,
            "status": self.status.value,
            "message": self.message,
            "spoken_message": self.spoken_message,
            "remediation": self.remediation,
            "duration_ms": self.duration_ms,
            "safe_metadata": self.safe_metadata,
        }


@dataclass(frozen=True)
class DependencyCheckResult:
    check_id: str
    dependency_area: str
    status: ReadinessStatus
    required_for_startup: bool
    message: str
    remediation: str
    spoken_message: str = ""
    safe_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "safe_metadata",
            sanitize_safe_metadata(self.safe_metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "check_id": self.check_id,
            "dependency_area": self.dependency_area,
            "status": self.status.value,
            "required_for_startup": self.required_for_startup,
            "message": self.message,
            "remediation": self.remediation,
            "safe_metadata": self.safe_metadata,
        }
        if self.spoken_message:
            payload["spoken_message"] = self.spoken_message
        return payload


@dataclass(frozen=True)
class ServiceStartupOption:
    mode: ServiceStartupMode
    enabled: bool
    template_path: str = ""
    manual_script_path: str = ""
    safe_stop_supported: bool = True
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "enabled": self.enabled,
            "template_path": self.template_path,
            "manual_script_path": self.manual_script_path,
            "safe_stop_supported": self.safe_stop_supported,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class LogRetentionPolicy:
    log_root: str
    normal_log_budget_mb: int = 50
    current_usage_mb: float = 0.0
    status: ReadinessStatus = ReadinessStatus.READY
    rotation_action: str = "none"
    privacy_safe: bool = True

    def __post_init__(self) -> None:
        if self.normal_log_budget_mb <= 0:
            raise ValueError("normal_log_budget_mb must be positive")
        if self.current_usage_mb < 0:
            raise ValueError("current_usage_mb must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "log_root": self.log_root,
            "normal_log_budget_mb": self.normal_log_budget_mb,
            "current_usage_mb": round(self.current_usage_mb, 3),
            "status": self.status.value,
            "rotation_action": self.rotation_action,
            "privacy_safe": self.privacy_safe,
        }


@dataclass(frozen=True)
class TroubleshootingEntry:
    entry_id: str
    symptom: str
    likely_cause: str
    diagnosis_step: str
    recovery_action: str
    related_status: ReadinessStatus
    privacy_notes: str = ""


CheckResult = HardwareCheckResult | DependencyCheckResult


@dataclass(frozen=True)
class DeploymentReadinessReport:
    report_id: str
    target_device: str
    checks: tuple[CheckResult, ...]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    startup_mode: str = "manual"
    privacy_summary: dict[str, bool] = field(
        default_factory=lambda: {
            "contains_user_images": False,
            "contains_ocr_text": False,
            "contains_translations": False,
            "contains_secrets": False,
            "contains_private_debug_paths": False,
        }
    )
    recommended_actions: tuple[str, ...] = ()
    service_startup: ServiceStartupOption | None = None
    log_retention: LogRetentionPolicy | None = None

    def __post_init__(self) -> None:
        if not self.checks:
            raise ValueError("DeploymentReadinessReport requires at least one check")
        if any(self.privacy_summary.values()):
            raise ValueError("deployment report privacy summary must remain false")

    @property
    def overall_status(self) -> ReadinessStatus:
        return most_severe_status([check.status for check in self.checks])

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "report_id": self.report_id,
            "created_at": self.created_at.isoformat(),
            "target_device": self.target_device,
            "overall_status": self.overall_status.value,
            "startup_mode": self.startup_mode,
            "checks": [check.to_dict() for check in self.checks],
            "privacy_summary": self.privacy_summary,
            "recommended_actions": list(self.recommended_actions),
        }
        if self.service_startup is not None:
            payload["service_startup"] = self.service_startup.to_dict()
        if self.log_retention is not None:
            payload["log_retention"] = self.log_retention.to_dict()
        return payload

"""Normal-log retention helpers for Raspberry Pi deployment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.deployment.readiness_models import LogRetentionPolicy, ReadinessStatus


DEFAULT_NORMAL_LOG_BUDGET_MB = 50


@dataclass(frozen=True)
class LogFileDecision:
    path: Path
    size_mb: float
    action: str


def calculate_log_usage_mb(log_root: Path) -> float:
    if not log_root.exists():
        return 0.0
    total_bytes = sum(
        path.stat().st_size
        for path in log_root.rglob("*")
        if path.is_file() and _is_normal_log(path)
    )
    return total_bytes / (1024 * 1024)


def build_log_retention_policy(
    log_root: Path,
    *,
    budget_mb: int = DEFAULT_NORMAL_LOG_BUDGET_MB,
) -> LogRetentionPolicy:
    if not log_root.exists():
        return LogRetentionPolicy(
            log_root=str(log_root),
            normal_log_budget_mb=budget_mb,
            status=ReadinessStatus.DEGRADED,
            rotation_action="manual_verification_needed",
            privacy_safe=True,
        )
    usage = calculate_log_usage_mb(log_root)
    action = retention_action_for_usage(usage, budget_mb)
    status = ReadinessStatus.READY if action == "none" else ReadinessStatus.DEGRADED
    return LogRetentionPolicy(
        log_root=str(log_root),
        normal_log_budget_mb=budget_mb,
        current_usage_mb=usage,
        status=status,
        rotation_action=action,
        privacy_safe=True,
    )


def retention_action_for_usage(usage_mb: float, budget_mb: int) -> str:
    if usage_mb <= budget_mb:
        return "none"
    if usage_mb <= budget_mb * 1.5:
        return "rotate"
    return "prune"


def plan_log_retention(
    log_root: Path,
    *,
    budget_mb: int = DEFAULT_NORMAL_LOG_BUDGET_MB,
) -> list[LogFileDecision]:
    if not log_root.exists():
        return []
    files = sorted(
        (path for path in log_root.rglob("*") if path.is_file() and _is_normal_log(path)),
        key=lambda path: path.stat().st_mtime,
    )
    usage_mb = calculate_log_usage_mb(log_root)
    decisions: list[LogFileDecision] = []
    for path in files:
        if usage_mb <= budget_mb:
            break
        size_mb = path.stat().st_size / (1024 * 1024)
        decisions.append(LogFileDecision(path=path, size_mb=size_mb, action="prune"))
        usage_mb -= size_mb
    return decisions


def summarize_log_retention_decisions(
    decisions: list[LogFileDecision],
) -> dict[str, float | int]:
    return {
        "decision_count": len(decisions),
        "planned_prune_mb": round(sum(decision.size_mb for decision in decisions), 3),
    }


def _is_normal_log(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".log") or ".log." in name

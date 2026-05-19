"""Deployment log retention policy tests."""

from __future__ import annotations

from modules.deployment.log_retention import (
    DEFAULT_NORMAL_LOG_BUDGET_MB,
    build_log_retention_policy,
    calculate_log_usage_mb,
    plan_log_retention,
    retention_action_for_usage,
    summarize_log_retention_decisions,
)
from modules.deployment.readiness_models import ReadinessStatus


def test_default_log_budget_is_50_mb() -> None:
    assert DEFAULT_NORMAL_LOG_BUDGET_MB == 50
    assert retention_action_for_usage(49.9, 50) == "none"
    assert retention_action_for_usage(60, 50) == "rotate"
    assert retention_action_for_usage(80, 50) == "prune"


def test_log_usage_and_policy_use_normal_logs_only(tmp_path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "assistant.log").write_bytes(b"a" * 1024)
    (logs / "not-a-log.bin").write_bytes(b"a" * 1024)

    assert calculate_log_usage_mb(logs) > 0
    assert calculate_log_usage_mb(logs) < 0.01
    policy = build_log_retention_policy(logs)
    assert policy.status is ReadinessStatus.READY
    assert policy.normal_log_budget_mb == 50


def test_log_retention_plan_prunes_oldest_normal_logs(tmp_path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    first = logs / "assistant.log.1"
    second = logs / "assistant.log.2"
    first.write_bytes(b"a" * 1024 * 1024)
    second.write_bytes(b"b" * 1024 * 1024)

    decisions = plan_log_retention(logs, budget_mb=1)
    assert decisions
    assert decisions[0].action == "prune"
    assert summarize_log_retention_decisions(decisions)["decision_count"] >= 1

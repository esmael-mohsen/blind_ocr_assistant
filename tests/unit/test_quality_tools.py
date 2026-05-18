"""Optional quality-tool self-check tests."""

from __future__ import annotations

from config import AppConfig
from modules.common.bootstrap import detect_optional_quality_tools, run_self_check


def test_detect_optional_quality_tools_is_non_blocking(monkeypatch) -> None:
    monkeypatch.setattr(
        "modules.common.bootstrap.importlib.util.find_spec",
        lambda _name: None,
    )

    statuses = detect_optional_quality_tools()

    assert statuses
    assert all(status.installed is False for status in statuses)


def test_self_check_passes_when_quality_tools_are_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "modules.common.bootstrap.importlib.util.find_spec",
        lambda _name: None,
    )
    config = AppConfig(
        logs_dir=tmp_path / "logs",
        debug_captures_dir=tmp_path / "debug_captures",
        benchmark_results_dir=tmp_path / "benchmark_results",
        config_dir=tmp_path / "config",
    )

    result = run_self_check(config)

    assert result.success is True
    assert result.value is not None
    assert "optional quality tools not installed" in " ".join(result.value.messages)


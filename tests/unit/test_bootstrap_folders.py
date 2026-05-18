"""Runtime folder creation tests."""

from __future__ import annotations

from config import AppConfig
from modules.common.bootstrap import create_runtime_dirs


def test_create_runtime_dirs_creates_safe_local_folders(tmp_path) -> None:
    config = AppConfig(
        logs_dir=tmp_path / "logs",
        debug_captures_dir=tmp_path / "debug_captures",
        benchmark_results_dir=tmp_path / "benchmark_results",
        config_dir=tmp_path / "config",
    )

    created = create_runtime_dirs(config)

    assert set(created) == set(config.runtime_dirs)
    for directory in config.runtime_dirs:
        assert directory.exists()
        assert directory.is_dir()


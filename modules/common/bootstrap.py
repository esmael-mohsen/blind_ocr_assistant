"""Phase 0 bootstrap checks and local setup helpers."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.util
from pathlib import Path
from typing import Iterable

from config import AppConfig, load_config
from modules.common.logging import log_event, setup_logging
from modules.common.result import Result


CORE_PACKAGES = (
    "modules",
    "modules.assistant",
    "modules.camera",
    "modules.common",
    "modules.image_processing",
    "modules.ocr",
    "modules.text",
    "modules.translation",
    "modules.voice",
)

OPTIONAL_QUALITY_TOOLS = ("ruff", "black", "mypy")


@dataclass(frozen=True)
class QualityToolStatus:
    name: str
    installed: bool


@dataclass(frozen=True)
class SelfCheckReport:
    success: bool
    created_dirs: tuple[Path, ...]
    import_results: tuple[str, ...]
    quality_tools: tuple[QualityToolStatus, ...]
    messages: tuple[str, ...]


def create_runtime_dirs(config: AppConfig) -> tuple[Path, ...]:
    """Create safe local runtime directories if they are missing."""
    created: list[Path] = []
    for directory in config.runtime_dirs:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(directory)
        else:
            directory.mkdir(parents=True, exist_ok=True)
    return tuple(created)


def verify_imports(packages: Iterable[str] = CORE_PACKAGES) -> Result[tuple[str, ...]]:
    """Verify Phase 0 package placeholders are importable."""
    imported: list[str] = []
    for package in packages:
        try:
            importlib.import_module(package)
        except Exception as exc:  # pragma: no cover - defensive report path
            return Result.fail("IMPORT_FAILED", f"{package}: {exc}")
        imported.append(package)
    return Result.ok(tuple(imported), "imports ok")


def detect_optional_quality_tools() -> tuple[QualityToolStatus, ...]:
    """Detect optional quality tools without making them required."""
    return tuple(
        QualityToolStatus(name=tool, installed=importlib.util.find_spec(tool) is not None)
        for tool in OPTIONAL_QUALITY_TOOLS
    )


def run_self_check(config: AppConfig | None = None) -> Result[SelfCheckReport]:
    """Run Phase 0 readiness checks without hardware, network, or engines."""
    active_config = config or load_config()
    created_dirs = create_runtime_dirs(active_config)
    logger = setup_logging(active_config.logs_dir, active_config.log_level)
    log_event(logger, "BOOTSTRAP_SELF_CHECK", "started")

    imports = verify_imports()
    if not imports.success:
        log_event(logger, "BOOTSTRAP_SELF_CHECK", imports.message, level="ERROR")
        return Result.fail(imports.error_code or "BOOTSTRAP_FAILED", imports.message)

    result_probe = Result.ok(message="result helper ok")
    failure_probe = Result.fail("EXPECTED_FAILURE", "failure helper ok")
    if not result_probe.success or failure_probe.success:
        return Result.fail("RESULT_HELPER_FAILED", "Result helpers are inconsistent")

    quality_tools = detect_optional_quality_tools()
    messages = ["core bootstrap checks passed"]
    missing_tools = [tool.name for tool in quality_tools if not tool.installed]
    if missing_tools:
        messages.append(
            "optional quality tools not installed: " + ", ".join(missing_tools)
        )

    report = SelfCheckReport(
        success=True,
        created_dirs=created_dirs,
        import_results=imports.value or (),
        quality_tools=quality_tools,
        messages=tuple(messages),
    )
    log_event(logger, "BOOTSTRAP_SELF_CHECK", "completed")
    return Result.ok(report, "self-check passed")


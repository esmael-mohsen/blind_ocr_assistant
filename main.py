"""Phase 0 bootstrap entrypoint for Blind OCR Assistant."""

from __future__ import annotations

import argparse
import signal
from types import FrameType

from modules.common.bootstrap import run_self_check
from modules.deployment.diagnostics import (
    format_report_for_cli,
    run_lightweight_startup_diagnostics,
)
from modules.deployment.readiness_checks import offline_recovery_spoken_summary
from modules.deployment.readiness_models import ReadinessStatus


def build_workflow():
    """Create the Phase 9 workflow without starting hardware at import time."""
    from modules.assistant.workflow import AssistantWorkflow

    return AssistantWorkflow()


def install_signal_handlers(workflow) -> None:
    """Install operational shutdown handlers for an assistant workflow."""

    def _handle_shutdown(signum: int, frame: FrameType | None) -> None:
        workflow.shutdown()

    signal.signal(signal.SIGINT, _handle_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_shutdown)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser without loading future engine modules."""
    parser = argparse.ArgumentParser(
        prog="blind-ocr-assistant",
        description=(
            "Phase 0 bootstrap for the Blind OCR Assistant. "
            "OCR, camera, voice, TTS, and translation are added in later phases."
        ),
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="verify Phase 0 repository readiness without hardware or services",
    )
    parser.add_argument(
        "--once",
        metavar="COMMAND",
        help=(
            "handle one assistant command through the Phase 9 workflow wiring "
            "without starting a continuous microphone loop"
        ),
    )
    parser.add_argument(
        "--skip-startup-checks",
        action="store_true",
        help="skip Phase 11 lightweight deployment readiness checks",
    )
    return parser


def run_startup_checks() -> int:
    """Run non-visual lightweight deployment startup checks."""
    report = run_lightweight_startup_diagnostics(local_fallback_available=True)
    print(format_report_for_cli(report))
    print(offline_recovery_spoken_summary(report.overall_status))
    if report.overall_status is ReadinessStatus.BLOCKED:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 0 CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_check:
        result = run_self_check()
        if not result.success:
            print(f"FAIL {result.error_code}: {result.message}")
            return 1
        report = result.value
        print("Phase 0 self-check: PASS")
        if report is not None:
            for message in report.messages:
                print(f"- {message}")
            for tool in report.quality_tools:
                status = "installed" if tool.installed else "not installed"
                print(f"- optional {tool.name}: {status}")
        return 0
    if not args.skip_startup_checks:
        startup_code = run_startup_checks()
        if startup_code != 0:
            return startup_code
    if args.once:
        workflow = build_workflow()
        result = workflow.handle_command(args.once)
        print(result.guidance)
        return 0 if result.success else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Phase 0 bootstrap entrypoint for Blind OCR Assistant."""

from __future__ import annotations

import argparse

from modules.common.bootstrap import run_self_check


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
    return parser


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


if __name__ == "__main__":
    raise SystemExit(main())

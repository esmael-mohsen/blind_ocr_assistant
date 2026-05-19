"""Raspberry Pi deployment diagnostics CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.deployment.diagnostics import (  # noqa: E402
    format_report_for_cli,
    run_full_deployment_diagnostics,
    run_lightweight_startup_diagnostics,
)
from modules.deployment.readiness_models import ReadinessStatus  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run privacy-safe Raspberry Pi deployment readiness checks.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="run maintainer hardware, fallback, service, and log diagnostics",
    )
    parser.add_argument(
        "--skip-hardware",
        action="store_true",
        help="record hardware checks as manual verification needed",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="validate no-internet startup and local fallback readiness",
    )
    parser.add_argument(
        "--output-dir",
        default="deployment_diagnostics",
        help="local directory for privacy-safe deployment reports",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir)
    if args.full:
        report = run_full_deployment_diagnostics(
            output_dir=output_dir,
            offline=args.offline,
            skip_hardware=args.skip_hardware,
            local_fallback_available=True if args.skip_hardware else None,
            paddle_load_probe=_paddle_load_probe,
        )
    else:
        report = run_lightweight_startup_diagnostics(
            output_dir=output_dir,
            offline=args.offline,
            local_fallback_available=True if args.skip_hardware else None,
        )
    print(format_report_for_cli(report))
    if not args.full:
        print("Mode: lightweight startup checks")
    if args.full:
        print("Mode: full deployment diagnostics")
        print(
            "Service: manual startup available; service template remains disabled by default."
        )
        print("Logs: normal log retention budget is checked at 50 MB by default.")
    if args.skip_hardware:
        print("Hardware: skipped; manual verification remains required.")
    if args.offline:
        print("Offline: online services disabled for this diagnostic run.")
    return 1 if report.overall_status is ReadinessStatus.BLOCKED else 0


def _paddle_load_probe() -> bool:
    try:
        import os
        import subprocess
        import sys

        env = dict(os.environ)
        env.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        env.setdefault("GLOG_minloglevel", "3")
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from modules.ocr.paddle_ocr_engine import PaddleOCREngine; "
                    "PaddleOCREngine()._load_model()"
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
    except Exception:
        return False
    return completed.returncode == 0


if __name__ == "__main__":
    raise SystemExit(main())

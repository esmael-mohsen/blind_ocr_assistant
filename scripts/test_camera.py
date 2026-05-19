"""Developer camera validation script for Phase 3."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def main(argv: Sequence[str] | None = None) -> int:
    from modules.camera.camera_models import CaptureRequest
    from modules.camera.orbbec_camera import (
        capture_burst_from_sources,
        default_camera_sources,
    )

    parser = argparse.ArgumentParser(
        description=(
            "Validate Phase 3 camera capture. For Phase 11 deployment "
            "diagnostics, also run scripts/pi_deployment_check.py --full."
        )
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="attempt real camera capture; omitted by default for safe local runs",
    )
    parser.add_argument("--count", type=int, default=None, help="requested burst count")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.live:
        print("Live camera validation skipped. Use --live on hardware to run capture.")
        return 0

    request = CaptureRequest(requested_count=args.count)
    result = capture_burst_from_sources(default_camera_sources(), request)
    print(f"camera_available={result.success}")
    print(f"source_type={result.source_type.value}")
    print(f"candidate_count={len(result.candidates)}")
    print(f"partial_timeout={result.partial_timeout}")
    print(f"cleanup_status={result.cleanup_status.value}")
    if result.selection_result and result.selection_result.selected_frame:
        print(f"selected_frame_id={result.selection_result.selected_frame.frame_id}")
    if result.error is not None:
        print(f"error_code={result.error.error_code.value}")
        print(f"message={result.error.message}")
    return 0 if result.success else 2


if __name__ == "__main__":
    raise SystemExit(main())

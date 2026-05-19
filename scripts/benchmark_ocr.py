"""Command-line entry point for Phase 10 OCR benchmarking."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.benchmark.dataset_loader import load_benchmark_dataset  # noqa: E402
from modules.benchmark.runner import BenchmarkRunner, resolve_requested_paths  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    """Build the benchmark CLI parser."""

    parser = argparse.ArgumentParser(description="Run the local Phase 10 OCR benchmark.")
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to the local benchmark manifest JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default="benchmark_results",
        help="Directory where timestamped benchmark outputs are written.",
    )
    parser.add_argument(
        "--paths",
        default="cascade",
        help="OCR paths to benchmark: cascade, ocr_space, paddleocr, tesseract, or compare.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip online OCR paths and record them as disabled when requested.",
    )
    parser.add_argument(
        "--debug-text",
        action="store_true",
        help="Reserved for explicit safe fixture debugging; default outputs remain text-free.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the benchmark CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        dataset = load_benchmark_dataset(args.dataset)
        paths = resolve_requested_paths(args.paths, offline=args.offline)
        runner = BenchmarkRunner(
            dataset=dataset,
            output_dir=Path(args.output_dir),
            paths=paths,
            offline=args.offline,
            debug_text=args.debug_text,
        )
        run, summary = runner.run()
    except Exception as exc:
        print(f"Benchmark failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"Benchmark run: {run.run_id}")
    print(f"Dataset: {summary['dataset_id']}")
    print(f"Status: {summary['status']}")
    print(f"Results: {summary['result_count']} records")
    print(f"Output: {run.result_directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

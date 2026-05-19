"""Benchmark dataset loader tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules.benchmark.benchmark_models import BenchmarkError, REQUIRED_LABELS
from modules.benchmark.dataset_loader import load_benchmark_dataset


def test_controlled_manifest_covers_required_samples_labels_and_expected_text() -> None:
    dataset = load_benchmark_dataset("tests/benchmark/manifest.json")
    labels = set()
    for sample in dataset.samples:
        labels.update(sample.coverage_labels)

    assert dataset.dataset_id == "phase10-controlled"
    assert len(dataset.samples) >= 12
    assert REQUIRED_LABELS.issubset(labels)
    assert all(sample.expected_text_id for sample in dataset.samples if sample.is_normal_language_sample)
    difficult = [sample for sample in dataset.samples if sample.is_difficult_sample]
    assert len([sample for sample in difficult if sample.expected_text_id]) / len(difficult) >= 0.5


def test_loader_rejects_missing_manifest_invalid_shape_duplicate_ids_and_private_expected(tmp_path: Path) -> None:
    with pytest.raises(BenchmarkError, match="manifest missing"):
        load_benchmark_dataset(tmp_path / "missing.json")

    manifest = tmp_path / "manifest.json"
    manifest.write_text("{", encoding="utf-8")
    with pytest.raises(BenchmarkError, match="invalid JSON"):
        load_benchmark_dataset(manifest)

    project_manifest = Path("tests/benchmark/manifest.json")
    payload = json.loads(project_manifest.read_text(encoding="utf-8"))
    payload["samples"][1]["sample_id"] = payload["samples"][0]["sample_id"]
    bad = tmp_path / "manifest2.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BenchmarkError, match="unique"):
        load_benchmark_dataset(bad)


def test_loader_rejects_unsupported_privacy_classification(tmp_path: Path) -> None:
    payload = json.loads(Path("tests/benchmark/manifest.json").read_text(encoding="utf-8"))
    payload["samples"][0]["privacy_classification"] = "public"
    bad = tmp_path / "manifest.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        load_benchmark_dataset(bad)

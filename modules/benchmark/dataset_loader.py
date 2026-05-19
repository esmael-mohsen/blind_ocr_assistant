"""Manifest loading for Phase 10 benchmark datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.benchmark.benchmark_models import (
    BenchmarkDataset,
    BenchmarkError,
    BenchmarkSample,
    ExpectedTextReference,
    LanguageLabel,
    PrivacyClassification,
)
from modules.benchmark.expected_text import load_expected_text


def load_benchmark_dataset(manifest_path: str | Path) -> BenchmarkDataset:
    """Load and validate a benchmark dataset manifest."""

    path = Path(manifest_path)
    if not path.exists():
        raise BenchmarkError(f"benchmark dataset manifest missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BenchmarkError(f"benchmark dataset manifest is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise BenchmarkError("benchmark manifest must be a JSON object")

    base_dir = path.parent
    expected_texts = _load_expected_texts(payload.get("expected_texts", []), base_dir)
    samples = _load_samples(payload.get("samples", []), base_dir)
    dataset = BenchmarkDataset(
        dataset_id=_required_string(payload, "dataset_id"),
        manifest_path=path,
        samples=tuple(samples),
        expected_texts=expected_texts,
        minimum_sample_count=int(payload.get("minimum_sample_count", 12)),
        created_for_phase=str(payload.get("created_for_phase", "phase10")),
    )
    _validate_local_paths(dataset)
    _validate_expected_files(dataset)
    return dataset


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkError(f"manifest field {key} is required")
    return value


def _load_expected_texts(
    items: Any,
    base_dir: Path,
) -> dict[str, ExpectedTextReference]:
    if not isinstance(items, list):
        raise BenchmarkError("expected_texts must be a list")
    references: dict[str, ExpectedTextReference] = {}
    for item in items:
        if not isinstance(item, dict):
            raise BenchmarkError("expected_texts entries must be objects")
        reference = ExpectedTextReference(
            expected_text_id=_required_string(item, "expected_text_id"),
            text_path=_resolve_manifest_path(base_dir, _required_string(item, "text_path")),
            language_label=LanguageLabel(item.get("language_label", "unknown")),
            normalization_policy=str(item.get("normalization_policy", "preserve_meaning")),
            privacy_classification=PrivacyClassification(
                item.get("privacy_classification", "safe_fixture")
            ),
        )
        if reference.expected_text_id in references:
            raise BenchmarkError(f"duplicate expected text ID: {reference.expected_text_id}")
        references[reference.expected_text_id] = reference
    return references


def _load_samples(items: Any, base_dir: Path) -> list[BenchmarkSample]:
    if not isinstance(items, list):
        raise BenchmarkError("samples must be a list")
    samples: list[BenchmarkSample] = []
    for item in items:
        if not isinstance(item, dict):
            raise BenchmarkError("sample entries must be objects")
        labels = item.get("scenario_labels")
        if not isinstance(labels, list):
            raise BenchmarkError("scenario_labels must be a list")
        samples.append(
            BenchmarkSample(
                sample_id=_required_string(item, "sample_id"),
                image_path=_resolve_manifest_path(base_dir, _required_string(item, "image_path")),
                scenario_labels=tuple(str(label) for label in labels),
                language_label=LanguageLabel(item.get("language_label", "unknown")),
                quality_label=str(item.get("quality_label", "normal")),
                expected_text_id=item.get("expected_text_id"),
                privacy_classification=PrivacyClassification(
                    item.get("privacy_classification", "safe_fixture")
                ),
                notes=item.get("notes"),
            )
        )
    return samples


def _resolve_manifest_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        raise BenchmarkError("benchmark manifest paths must be local project-relative paths")
    if value.startswith(".."):
        raise BenchmarkError("benchmark manifest paths must stay within the project")
    return (base_dir.parent.parent / path).resolve()


def _validate_local_paths(dataset: BenchmarkDataset) -> None:
    project_root = dataset.manifest_path.resolve().parents[2]
    for sample in dataset.samples:
        if project_root not in sample.image_path.resolve().parents and sample.image_path.resolve() != project_root:
            raise BenchmarkError("sample paths must stay within the project")
        if not sample.image_path.exists():
            raise BenchmarkError(f"benchmark sample missing: {sample.sample_id}")
    for reference in dataset.expected_texts.values():
        if project_root not in reference.text_path.resolve().parents and reference.text_path.resolve() != project_root:
            raise BenchmarkError("expected text paths must stay within the project")


def _validate_expected_files(dataset: BenchmarkDataset) -> None:
    for reference in dataset.expected_texts.values():
        load_expected_text(reference)


__all__ = ["load_benchmark_dataset"]

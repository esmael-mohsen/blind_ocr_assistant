"""Scope boundary tests for Phase 10 benchmark code and docs."""

from __future__ import annotations

from pathlib import Path


BENCHMARK_FILES = [
    Path("modules/benchmark/benchmark_models.py"),
    Path("modules/benchmark/dataset_loader.py"),
    Path("modules/benchmark/expected_text.py"),
    Path("modules/benchmark/runner.py"),
    Path("modules/benchmark/result_writer.py"),
    Path("modules/benchmark/tuning.py"),
    Path("scripts/benchmark_ocr.py"),
]


def test_phase10_does_not_import_live_assistant_or_adjacent_engines() -> None:
    forbidden = [
        "modules.assistant",
        "modules.translation",
        "modules.voice",
        "LibreTranslate",
        "Argos",
        "Vosk",
        "tts_engine",
        "openai",
        "stripe",
        "boto3",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in BENCHMARK_FILES)

    assert all(value not in combined for value in forbidden)


def test_phase10_does_not_add_assistant_command_categories() -> None:
    command_models = Path("modules/voice/command_models.py").read_text(encoding="utf-8")

    assert "benchmark" not in command_models.lower()


def test_benchmark_methodology_document_contract() -> None:
    doc = Path("docs/benchmark_methodology.md")
    assert doc.exists()
    text = doc.read_text(encoding="utf-8").lower()
    for phrase in [
        "dataset policy",
        "expected-text policy",
        "normalization policy",
        "result fields",
        "privacy behavior",
        "tuning gates",
        "known failure",
        "best-path",
    ]:
        assert phrase in text


def test_benchmark_docs_examples_exclude_private_content() -> None:
    docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [Path("docs/benchmark_methodology.md"), Path("tests/benchmark/README.md")]
        if path.exists()
    )
    forbidden = ["raw secret text", "clean secret text", "translated secret text", "api_token"]

    assert all(value not in docs for value in forbidden)

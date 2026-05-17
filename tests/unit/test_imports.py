"""Importability checks for the Phase 0 scaffold."""

from __future__ import annotations

import importlib


def test_phase0_packages_are_importable() -> None:
    packages = (
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

    for package in packages:
        assert importlib.import_module(package)


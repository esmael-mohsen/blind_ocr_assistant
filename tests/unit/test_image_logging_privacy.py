"""Image logging privacy tests."""

from __future__ import annotations

import numpy as np

from modules.image_processing.image_models import safe_image_metadata


def test_safe_image_metadata_excludes_images_debug_paths_and_text() -> None:
    metadata = safe_image_metadata(
        source_id="fixture",
        image=np.zeros((10, 12, 3), dtype=np.uint8),
        metadata={
            "image_array": np.zeros((1, 1, 3), dtype=np.uint8),
            "image_bytes": b"private",
            "raw_text": "private OCR text",
            "debug_path": "debug_captures/private.png",
            "quality_score": 0.8,
        },
    )

    assert metadata["source_id"] == "fixture"
    assert metadata["image_width"] == 12
    assert metadata["image_height"] == 10
    assert metadata["quality_score"] == 0.8
    assert "private" not in str(metadata)
    assert "debug_captures" not in str(metadata)

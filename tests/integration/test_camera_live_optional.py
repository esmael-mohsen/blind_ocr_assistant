"""Optional live camera validation tests."""

from __future__ import annotations

import os

import pytest


@pytest.mark.live_camera
def test_live_camera_is_opt_in() -> None:
    if os.getenv("RUN_LIVE_CAMERA_TESTS") != "1":
        pytest.skip("RUN_LIVE_CAMERA_TESTS=1 is required for live camera tests")

    pytest.skip("Live Phase 3 camera validation is implemented with the camera adapter")

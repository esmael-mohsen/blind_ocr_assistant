# Quickstart: Phase 3 Camera Integration and Best Frame Selection

## Prerequisites

- Python 3.10+
- Existing Phase 0-2 project setup
- `numpy`
- `opencv-python` or `opencv-python-headless`
- `pytest`
- Optional target hardware: Raspberry Pi 4 with Orbbec Astra Pro
- Optional target camera SDK or OpenNI2 adapter dependencies for live hardware

Automated validation must not require camera hardware. Live camera validation is
manual or opt-in.

## Install Development Dependencies

```powershell
python -m pip install -r requirements.txt
```

If optional quality tools are installed, they may be run during validation:

```powershell
python -m ruff check .
python -m black --check .
python -m mypy .
```

## Run Automated Phase 3 Tests

```powershell
python -m pytest tests/unit
```

Expected automated coverage:

- capture request count is clamped to 10-20
- target depth camera is preferred before generic RGB fallback
- mocked capture returns structured frame candidates
- resource release is verified after success, failure, timeout, and cancellation
- partial timeouts score valid captured frames
- zero-frame timeouts return structured capture failure
- RGB-only mode succeeds when depth is unavailable
- depth statuses classify too close, acceptable, too far, and unavailable
- frame selection is deterministic
- tie-breaks prefer acceptable quality, then stability, then earliest frame
- default logs contain safe metadata only

## Run Optional Live Camera Validation

Use the live camera script only on machines with camera hardware attached:

```powershell
python scripts/test_camera.py --live
```

Expected script output:

- camera availability
- selected source path, including fallback mode when used
- RGB capture status
- optional depth status
- clamped capture count
- selected frame id and score summary
- timeout or failure code when applicable
- resource cleanup status

Without `--live`, the script should avoid requiring hardware or should report a
safe skipped/unavailable status.

## Manual Acceptance Checklist

- Target depth camera path is attempted first on Raspberry Pi hardware.
- Generic RGB fallback works when target depth capture is unavailable.
- Captured frames are not saved permanently by default.
- Poor bursts return recapture guidance rather than a selected frame.
- Depth too-close and too-far cases produce corrective guidance.
- Camera resources are released after every terminal path.
- No OCR, OCR cascade, text cleanup, TTS, translation, or full assistant
  workflow behavior is introduced in Phase 3.

## Validation Results

Phase 3 implementation validation commands:

```text
python -m pytest tests/unit
python -m ruff check .
optional: python scripts/test_camera.py --live
```

Expected local result after implementation:

- Unit tests pass without physical camera hardware.
- Live camera integration test is skipped unless `RUN_LIVE_CAMERA_TESTS=1` is
  set.
- `scripts/test_camera.py` without `--live` prints a skipped message and does
  not touch camera hardware.
- `scripts/test_camera.py --live` is reserved for a machine with camera
  hardware attached.

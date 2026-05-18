# Phase 3 Camera Fixture Notes

Phase 3 automated tests use generated arrays and mocked camera sources by
default so validation does not require physical camera hardware.

Safe fixture rules:

- Do not store real user document images in this directory.
- Keep captured-frame artifacts out of version control unless they are synthetic
  and non-sensitive.
- Prefer deterministic `numpy` arrays in tests for brightness, blur, depth, and
  stability cases.
- Live camera validation belongs behind explicit opt-in flags or environment
  variables.

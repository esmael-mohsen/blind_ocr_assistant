# Research: Phase 2 Image Processing and Quality Checking

## Decision: Use Deterministic Local Image Analysis Only

**Rationale**: Phase 2 must run without internet, camera hardware, OCR
credentials, audio devices, or paid services. Local deterministic analysis keeps
tests repeatable and supports later Raspberry Pi deployment.

**Alternatives considered**:
- Online image-quality services: rejected because they violate free/offline and
  privacy goals.
- OCR-based quality checks: rejected for Phase 2 because OCR execution is out of
  scope and would couple this layer to Phase 1 engines.

## Decision: Use Named Quality Statuses Instead of Exact Score Assertions

**Rationale**: Threshold values will need tuning during benchmarking, but the
product behavior must remain stable: dark, bright, blurry, low-contrast,
no-text, uncertain, and acceptable categories drive guidance and blocking.

**Alternatives considered**:
- Test exact numeric defaults: rejected because minor algorithm changes would
  make tests brittle.
- Use only a pass/fail result: rejected because users need actionable guidance
  and developers need observability.

## Decision: Conservative Blocking for Poor or Uncertain Images

**Rationale**: Blind users cannot visually verify OCR quality. Blocking
borderline images with recapture guidance better supports accuracy before speed
and reduces the chance of reading incorrect text.

**Alternatives considered**:
- Allow uncertain images into OCR automatically: rejected because it risks
  unreliable output.
- Add an override in Phase 2: deferred because override behavior belongs to a
  later assistant workflow.

## Decision: Provide Arabic and English Guidance Text in Reports

**Rationale**: The assistant targets Arabic and English users. Returning both
guidance strings now lets later TTS and command phases choose the spoken
language without reinterpreting quality statuses.

**Alternatives considered**:
- English-only guidance: rejected because it weakens accessibility for Arabic
  users.
- Generate guidance dynamically later: rejected because Phase 2 needs testable
  user-facing outcomes.

## Decision: Use Safe Local Fixtures and Deterministic Generated Images

**Rationale**: Tests must be reproducible and must not store private user
content. Generated fixtures can exercise dark, blurry, contrast, and text-like
patterns consistently across development machines.

**Alternatives considered**:
- Real captured documents: rejected by default because they can include private
  content and may not be reproducible.
- Hardware camera fixtures: deferred to Phase 3.

## Decision: Produce Three Preprocessing Variants for Accepted Images

**Rationale**: Later OCR paths have different expected inputs: a light online
variant, a natural local accuracy variant, and a stronger emergency variant.
Producing named variants here keeps the future cascade simple while preserving
the original image.

**Alternatives considered**:
- One universal variant: rejected because Tesseract-style emergency OCR often
  benefits from stronger processing than online or local accuracy OCR.
- Preprocess rejected images automatically: rejected because the normal workflow
  must return corrective guidance first.

## Decision: Keep Phase 2 Independent From Camera, OCR, TTS, and Translation

**Rationale**: The specification requires Phase 2 to be testable as an isolated
image-processing layer. This prevents cross-phase coupling and keeps task
generation focused.

**Alternatives considered**:
- Integrate with camera capture now: rejected because Phase 3 owns capture and
  best-frame selection.
- Integrate with OCR cascade now: rejected because Phase 4 owns cascade routing.

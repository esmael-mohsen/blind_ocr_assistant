# Feature Specification: Phase 2 Image Processing and Quality Checking

**Feature Branch**: `003-phase2-image-quality`

**Created**: 2026-05-17

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 2 with best practices"

## Clarifications

### Session 2026-05-17

- Q: How should borderline or uncertain image quality be handled before OCR? -> A: Use conservative blocking with recapture guidance.
- Q: What language coverage should guidance messages provide in Phase 2? -> A: Provide Arabic and English guidance text.
- Q: What source should Phase 2 use for validation images? -> A: Use deterministic generated or safe local fixtures only.
- Q: Should preprocessing run automatically for images rejected by quality checks? -> A: Do not preprocess rejected images in the normal quality workflow.
- Q: How should configurable quality thresholds be validated? -> A: Validate named categories, not exact default numbers.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reject Poor Images With Guidance (Priority: P1)

As a blind user, I need the assistant to recognize when an image is too dark,
too blurry, too low contrast, or unlikely to contain readable text so that I can
adjust the capture before the system tries to read unreliable OCR output.

**Why this priority**: This is the core Phase 2 value. A blind user cannot
visually inspect the image, so the assistant must prevent clearly poor images
from entering the reading path and must provide actionable guidance.

**Independent Test**: Given curated dark, blurry, low-contrast, no-text, and
acceptable image fixtures, the quality check returns an accept/reject decision,
individual quality statuses, an overall score, and a guidance message that tells
the user what to improve.

**Acceptance Scenarios**:

1. **Given** a dark image, **When** the image quality check runs, **Then** the
   result is rejected and the guidance asks the user to improve lighting.
2. **Given** a blurry image, **When** the image quality check runs, **Then** the
   result is rejected and the guidance asks the user to hold the camera steady
   or recapture.
3. **Given** an acceptable image with readable text, **When** the image quality
   check runs, **Then** the result is accepted and the Arabic and English
   guidance indicates the image is ready for OCR.
4. **Given** an image with no likely text area, **When** the image quality check
   runs, **Then** the result is rejected and the guidance asks the user to point
   the camera toward printed text.
5. **Given** a borderline image with uncertain quality, **When** the image
   quality check runs, **Then** the result is blocked from the normal OCR path
   and the guidance asks for a safer recapture.

---

### User Story 2 - Prepare OCR-Ready Image Variants (Priority: P2)

As a developer, I need the assistant to produce distinct image preparation
variants for online OCR, local accuracy OCR, and emergency OCR so that later OCR
phases can choose the most appropriate input without mutating the original
capture.

**Why this priority**: The OCR engines validated in Phase 1 have different
input needs. Preparing variants independently reduces later cascade complexity
and protects the original image for comparison and debugging.

**Independent Test**: Given a valid source image, preprocessing returns named
variants for online-light, local-natural, and emergency-strong use, preserves the
source image unchanged, and reports which variants were produced.

**Acceptance Scenarios**:

1. **Given** a readable accepted source image, **When** preprocessing runs,
   **Then** three named variants are available for the later OCR paths.
2. **Given** a source image with mild lighting or contrast issues, **When**
   preprocessing runs, **Then** at least one variant improves readability
   indicators without destroying text structure.
3. **Given** preprocessing cannot produce a variant, **When** the failure is
   reported, **Then** the result includes a stable failure reason and the source
   image remains available.
4. **Given** a source image rejected by the quality workflow, **When** the normal
   workflow decides next steps, **Then** preprocessing is not run automatically
   and the user receives corrective guidance instead.

---

### User Story 3 - Estimate Text Presence Before OCR (Priority: P3)

As a developer, I need a basic text-region estimate so that later capture and
OCR phases can avoid wasting time on images that probably do not contain
readable text.

**Why this priority**: Text-region estimation improves accuracy and user
guidance, but it is less critical than detecting obvious poor image quality.

**Independent Test**: Given fixtures with prominent text, sparse text, and no
text-like content, the estimate reports a text-presence status and score that
can be included in the overall quality decision.

**Acceptance Scenarios**:

1. **Given** an image with clear printed text, **When** text-region estimation
   runs, **Then** the result reports likely text present.
2. **Given** an image with no text-like area, **When** text-region estimation
   runs, **Then** the result reports unlikely text present.
3. **Given** a borderline image with small or partial text, **When** text-region
   estimation runs, **Then** the result is marked uncertain rather than treated
   as a confident pass.

---

### Edge Cases

- Image input is missing, unreadable, empty, or not a supported image format.
- Image is extremely dark, extremely bright, washed out, or low contrast.
- Image is heavily blurred, motion blurred, or too small to evaluate reliably.
- Image contains decorative patterns that may look text-like but are not text.
- Image contains Arabic only, English only, mixed Arabic/English, or numbers and
  punctuation.
- Image contains small text, angled text, partial text, or text near the edge of
  the frame.
- Multiple quality problems are present at once; guidance must prioritize the
  most actionable issue.
- Borderline or uncertain image quality is treated conservatively so the normal
  OCR path is blocked until the user recaptures or a later explicit override is
  introduced.
- Preprocessing fails for one variant while other variants can still be
  produced.
- Rejected images do not automatically enter preprocessing in the normal quality
  workflow.
- Debug image saving is disabled by default; no permanent image artifact is
  created unless explicitly configured.
- Phase 2 runs on a development machine without camera hardware, internet,
  audio devices, or OCR credentials.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a single image input and return a complete
  image quality report without requiring camera hardware.
- **FR-002**: The quality report MUST include an overall accept/reject decision,
  an overall quality score, brightness status, blur or sharpness status,
  contrast status, text-presence status, and an actionable guidance message.
- **FR-003**: The system MUST detect images that are too dark or too bright for
  reliable reading and classify them separately from acceptable images.
- **FR-004**: The system MUST detect images that are too blurry for reliable
  reading and classify them separately from acceptable images.
- **FR-005**: The system MUST detect low-contrast images that may reduce reading
  accuracy and include that finding in the quality report.
- **FR-006**: The system MUST provide a basic text-presence estimate that can
  distinguish likely text, unlikely text, and uncertain text cases.
- **FR-007**: The system MUST combine individual quality findings into a single
  decision that blocks clearly poor or uncertain images from the normal later
  OCR path.
- **FR-008**: The system MUST produce actionable guidance for each rejected or
  uncertain image, prioritizing lighting, steadiness, distance/framing, or
  pointing toward text as appropriate.
- **FR-009**: Guidance messages MUST include Arabic and English user-facing text,
  be short enough to be spoken later, and not depend on visual-only
  instructions.
- **FR-010**: The system MUST produce named preprocessing variants for the later
  online-light, local-natural, and emergency-strong OCR paths.
- **FR-011**: Preprocessing MUST preserve the original image input unchanged for
  later comparison, fallback decisions, and debug workflows.
- **FR-012**: The system MUST return structured failures for missing input,
  unreadable input, unsupported image format, and preprocessing failure without
  crashing.
- **FR-013**: The system MUST expose configurable quality thresholds for
  brightness, blur, contrast, text presence, and overall acceptance.
- **FR-014**: Phase 2 MUST include deterministic generated images or safe local
  fixtures for dark, blurry, low-contrast, no-text, acceptable, Arabic, English,
  and mixed text scenarios.
- **FR-015**: Phase 2 MUST NOT implement camera capture, depth analysis,
  best-frame selection, OCR cascade routing, OCR engine execution, text cleanup,
  voice command recognition, TTS playback, or translation.
- **FR-016**: Default logs MUST include quality metadata such as status, scores,
  guidance category, and failure reason, but MUST NOT store image contents or
  extracted text.
- **FR-017**: Any debug image saving MUST be disabled by default and MUST be
  explicitly configurable when introduced.
- **FR-018**: The normal quality workflow MUST NOT automatically preprocess
  images rejected by the quality decision; it MUST return corrective guidance
  instead.
- **FR-019**: Tests and acceptance checks MUST validate named quality categories
  and decisions rather than depending on exact default threshold numbers.

### Constitution Requirements

- **CR-001**: Phase 2 MUST support accessibility-first behavior by producing
  guidance messages that can be spoken to a blind user without requiring visual
  confirmation.
- **CR-002**: Phase 2 MUST enforce accuracy-before-speed by rejecting clearly
  poor images before OCR rather than allowing unreliable text extraction.
- **CR-003**: Phase 2 MUST preserve free-only and offline-capable operation by
  requiring no paid service, online service, camera hardware, or OCR credential.
- **CR-004**: Phase 2 MUST define privacy behavior for image inputs, logs, and
  debug artifacts, with no permanent storage by default.
- **CR-005**: Phase 2 MUST include measurable validation for Arabic, English,
  mixed text, blur, lighting, contrast, and no-text failure modes.
- **CR-006**: Phase 2 MUST remain modular by keeping image quality and
  preprocessing independent from OCR engines, camera capture, command handling,
  speaking, and translation workflows.
- **CR-007**: Phase 2 MUST remain Raspberry Pi aware by keeping evaluation
  bounded to one image at a time and avoiding continuous every-frame OCR or
  unbounded artifact creation.

### Key Entities *(include if feature involves data)*

- **Image Input**: A single still image submitted for quality assessment and
  preprocessing. It may come from a file, image bytes, or a future camera frame.
- **Image Quality Report**: Structured result containing accept/reject decision,
  quality score, individual quality statuses, text-presence status, guidance
  message, and safe metadata.
- **Quality Finding**: A classified assessment of one quality dimension such as
  lighting, sharpness, contrast, or text presence.
- **Guidance Message**: A short user-facing instruction explaining what to
  improve before another capture or OCR attempt, with Arabic and English text
  available for later spoken feedback.
- **Preprocessing Variant Set**: Named image outputs prepared for later OCR
  paths while preserving the original image unchanged.
- **Quality Thresholds**: Configurable acceptance limits used to classify image
  quality consistently across tests and environments. Their exact default
  numbers may change during tuning, but their named categories and decisions
  must remain testable.
- **Image Processing Error**: Stable failure classification for missing input,
  unreadable input, unsupported format, invalid image data, or failed
  preprocessing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of curated dark, blurry, low-contrast, no-text, and
  acceptable fixtures are classified into the expected quality category.
- **SC-002**: 100% of rejected quality reports include one primary Arabic
  guidance message and one primary English guidance message that tell the user
  the next corrective action.
- **SC-003**: 100% of accepted quality reports include an overall score and all
  required individual quality statuses.
- **SC-004**: For every valid test image, preprocessing produces the three named
  OCR-preparation variants or returns a structured per-variant failure without
  crashing.
- **SC-005**: Local Phase 2 tests run without internet, camera hardware, audio
  devices, OCR credentials, or paid services.
- **SC-006**: Default validation creates no permanent debug image artifacts
  unless debug image saving is explicitly enabled.
- **SC-007**: Phase 2 test coverage includes Arabic-only, English-only, mixed
  Arabic/English, no-text, dark, blurry, low-contrast, and acceptable image
  cases.
- **SC-008**: 100% of borderline or uncertain quality fixtures are blocked from
  the normal OCR path unless a later explicit override is introduced.
- **SC-009**: 100% of normal workflow tests confirm rejected images return
  corrective guidance rather than automatically entering preprocessing.

## Assumptions

- Phase 2 consumes still image inputs only; live camera capture and burst
  selection are reserved for Phase 3.
- Phase 2 prepares inputs for later OCR engines but does not run OCR or decide
  cascade fallback behavior.
- Text-presence estimation is intentionally basic and deterministic in this
  phase; benchmark-driven tuning is reserved for later phases.
- Guidance messages are returned as text that later TTS phases can speak; Phase
  2 does not play audio.
- Quality thresholds start with conservative defaults and may be tuned later
  using benchmark results; tests should assert categories and decisions instead
  of exact default numbers.
- Test images are deterministic generated images or safe local fixtures that are
  suitable to store in the repository and do not contain private user content.

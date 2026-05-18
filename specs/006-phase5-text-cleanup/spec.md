# Feature Specification: Phase 5 Text Cleanup, RTL Handling, and Language Detection

**Feature Branch**: `006-phase5-text-cleanup`

**Created**: 2026-05-18

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 5 with best practices"

## Clarifications

### Session 2026-05-18

- Q: How aggressive should OCR garbage cleanup be? -> A: Conservative cleanup only; preserve uncertain content and flag it with warnings instead of deleting it.
- Q: How should line breaks be handled? -> A: Collapse single OCR line breaks inside paragraphs, preserve blank-line paragraph breaks, and keep list-like breaks when detected.
- Q: What language detection decision rule should tests use? -> A: Use deterministic evidence thresholds: dominant language requires at least 60% language-bearing characters and enough text evidence; mixed requires meaningful Arabic and English evidence; otherwise return unknown.
- Q: What output order should Arabic RTL handling preserve? -> A: Preserve logical reading order for Arabic and mixed text, with direction metadata for later reading or display workflows.
- Q: When may raw or clean text appear in logs? -> A: Only when debug mode and explicit sensitive-text logging are both enabled; default logs exclude both raw and clean text.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read Clean OCR Text Aloud (Priority: P1)

As a blind user, I need OCR output to be cleaned before it is read aloud so that broken spacing, awkward line breaks, and OCR garbage do not make the spoken reading confusing.

**Why this priority**: This is the minimum useful outcome for Phase 5. The assistant can already obtain OCR text; the next user value is making that text understandable for reading.

**Independent Test**: Provide noisy OCR text with extra spaces, broken lines, repeated whitespace, and punctuation spacing issues; verify the resulting clean text is easier to read while the original raw text remains available.

**Acceptance Scenarios**:

1. **Given** OCR text with repeated spaces and awkward line breaks, **When** the cleanup step is applied, **Then** the clean text has normalized spacing, readable sentence flow, and preserved paragraph boundaries.
2. **Given** OCR text with punctuation separated by inconsistent spaces, **When** the cleanup step is applied, **Then** punctuation spacing is normalized without changing the intended words.
3. **Given** OCR text containing obvious garbage fragments around otherwise readable text, **When** cleanup is applied, **Then** the clean text removes or reduces the garbage while preserving meaningful content.

---

### User Story 2 - Preserve Arabic and Mixed Text Readability (Priority: P2)

As an Arabic or bilingual Arabic/English user, I need the assistant to preserve Arabic reading order and mixed-language content so that cleanup does not damage the text before reading or translation.

**Why this priority**: Arabic and mixed text are core supported content types. Cleanup that improves English but damages Arabic would make the assistant unusable for a primary audience.

**Independent Test**: Provide Arabic-only, English-only, and mixed Arabic/English OCR samples; verify the cleaned text remains readable, language classification is correct, and mixed content is not destroyed.

**Acceptance Scenarios**:

1. **Given** Arabic OCR text with spacing noise, **When** cleanup and direction handling are applied, **Then** the Arabic text remains readable and suitable for later speech output.
2. **Given** mixed Arabic/English OCR text, **When** cleanup is applied, **Then** both language segments remain present and understandable.
3. **Given** English OCR text, **When** cleanup is applied, **Then** English text remains readable and is not treated as Arabic.

---

### User Story 3 - Identify Text Language for Later Workflows (Priority: P3)

As the assistant workflow, I need a reliable language classification for cleaned OCR text so later reading and translation steps can choose appropriate behavior without asking the user unnecessarily.

**Why this priority**: Language detection improves later TTS and translation routing, but it depends on cleaned text being available first.

**Independent Test**: Provide representative Arabic, English, mixed, empty, and uncertain text samples; verify the language result is stable, explainable, and safe for downstream decisions.

**Acceptance Scenarios**:

1. **Given** Arabic-only text, **When** language detection is applied, **Then** the result identifies Arabic.
2. **Given** English-only text, **When** language detection is applied, **Then** the result identifies English.
3. **Given** meaningful Arabic and English content in the same text, **When** language detection is applied, **Then** the result identifies mixed text.
4. **Given** empty or symbol-heavy text, **When** language detection is applied, **Then** the result is unknown or low-confidence rather than misleading.

### Edge Cases

- Empty or whitespace-only OCR text must produce empty clean text and an unknown language result without crashing.
- Very short text must be preserved when meaningful but may return unknown language if there is not enough evidence.
- Cleanup must be conservative: uncertain fragments are preserved with warnings rather than removed.
- Single OCR line breaks inside paragraphs should be collapsed, blank-line paragraph breaks should be preserved, and list-like breaks should remain readable.
- Mixed numbers, punctuation, dates, prices, and symbols must not cause meaningful Arabic or English words to be removed.
- Arabic punctuation and common diacritics must not be stripped in a way that changes readability.
- Text containing both right-to-left and left-to-right segments must preserve all meaningful segments in logical reading order.
- Cleanup must be idempotent: applying it more than once should not keep changing the text.
- Raw OCR text and clean text must follow the project's privacy policy and must not be logged by default; logging text requires both debug mode and explicit sensitive-text logging.
- This phase must not start OCR, capture camera frames, translate text, or read text aloud; it prepares text for those later or adjacent workflows.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept raw OCR text and produce a separate clean text value.
- **FR-002**: System MUST preserve the original raw OCR text unchanged for audit, fallback, and comparison.
- **FR-003**: System MUST normalize repeated spaces, tabs, and inconsistent line breaks into readable text flow.
- **FR-004**: System MUST normalize punctuation spacing for Arabic, English, and mixed text without removing meaningful punctuation.
- **FR-005**: System MUST reduce obvious OCR garbage fragments when they are not meaningful content.
- **FR-006**: System MUST preserve Arabic text readability after cleanup.
- **FR-007**: System MUST preserve English text readability after cleanup.
- **FR-008**: System MUST preserve mixed Arabic/English content without deleting either language segment.
- **FR-009**: System MUST classify cleaned text as Arabic, English, mixed, or unknown.
- **FR-010**: System MUST provide a confidence or evidence summary for language classification sufficient for downstream decisions.
- **FR-011**: System MUST return structured results for successful cleanup, empty input, uncertain language, and invalid input.
- **FR-012**: System MUST make cleanup safe to run repeatedly without progressive text damage.
- **FR-013**: System MUST define user-safe guidance for cases where cleaned text is empty, too noisy, or language is unknown.
- **FR-014**: System MUST keep this phase scoped to text cleanup, direction handling, and language detection only.
- **FR-015**: System MUST use conservative cleanup by preserving uncertain content and returning warnings rather than deleting ambiguous text.
- **FR-016**: System MUST collapse single OCR line breaks within paragraphs, preserve paragraph breaks, and keep list-like line breaks readable.
- **FR-017**: System MUST classify a dominant language only when there is enough evidence and at least 60% of language-bearing characters support that language.
- **FR-018**: System MUST classify text as mixed only when both Arabic and English have meaningful evidence; otherwise uncertain samples MUST return unknown.
- **FR-019**: System MUST preserve logical reading order for Arabic and mixed text and expose direction information for later reading or display workflows.
- **FR-020**: System MUST exclude raw text and clean text from default logs and include them only when both debug mode and explicit sensitive-text logging are enabled.

### Constitution Requirements

- **CR-001**: Feature MUST be usable without visual confirmation and MUST define required spoken feedback for empty, noisy, or uncertain text results.
- **CR-002**: Feature MUST document downstream reading and translation readiness but MUST NOT implement TTS, translation, or voice command workflows in this phase.
- **CR-003**: Feature MUST avoid paid-service dependency; cleanup and language detection must be available offline.
- **CR-004**: Feature MUST define privacy behavior for raw OCR text, clean text, logs, and debug artifacts.
- **CR-005**: Feature MUST define measurable acceptance criteria for Arabic, English, mixed text, empty text, noisy text, and repeated cleanup.

### Key Entities *(include if feature involves data)*

- **TextCleanupRequest**: Represents raw OCR text to be prepared for reading and translation, including optional language hints from prior OCR results.
- **TextCleanupResult**: Represents the original raw text, clean text, detected language, cleanup status, warnings, and user-safe guidance.
- **LanguageDetectionResult**: Represents Arabic, English, mixed, or unknown classification with confidence or evidence details and the direction information needed by later workflows.
- **CleanupWarning**: Represents non-fatal cleanup concerns such as empty input, noisy content, uncertain language, or mixed direction text.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of accepted cleanup results preserve the original raw OCR text exactly.
- **SC-002**: At least 95% of representative Arabic, English, and mixed fixture samples remain readable after cleanup in reviewer validation.
- **SC-003**: Cleanup is idempotent for all automated fixture samples: running cleanup twice returns the same clean text as running it once.
- **SC-004**: Arabic-only, English-only, and mixed-language fixture sets are classified correctly in at least 90% of deterministic test cases.
- **SC-005**: Empty or whitespace-only inputs return a structured empty result and user-safe guidance in 100% of tests.
- **SC-006**: Default logs contain no raw OCR text or clean text in 100% of privacy tests.
- **SC-007**: The feature can process typical OCR text samples locally without requiring internet access or paid services.
- **SC-008**: Conservative cleanup preserves ambiguous but potentially meaningful text in 100% of noisy fixture tests while returning a warning.
- **SC-009**: Paragraph and list-like line break behavior matches the clarified policy in 100% of line-break fixture tests.
- **SC-010**: Language detection returns unknown rather than a false dominant language in 100% of insufficient-evidence fixture tests.
- **SC-011**: Arabic and mixed text fixtures preserve logical reading order in 100% of direction-handling tests.

## Assumptions

- Phase 5 receives OCR text from the existing OCR cascade and does not perform OCR itself.
- Text cleanup prepares content for future TTS and translation phases but does not read or translate the text.
- Arabic and English are the only required languages for this phase; mixed means meaningful Arabic and English content together.
- Language detection may use deterministic character and token evidence rather than requiring external services.
- Privacy defaults follow the existing project policy: raw text and clean text are excluded from normal logs, and text logging requires both debug mode and explicit sensitive-text logging.
- User-facing spoken messages will be represented as guidance text in this phase for later TTS integration.

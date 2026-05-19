# Feature Specification: Phase 7 Translation Layer

**Feature Branch**: `008-phase7-translation-layer`

**Created**: 2026-05-18

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 7 with best practices"

## Clarifications

### Session 2026-05-18

- Q: What is the default online/offline routing policy for translation? -> A: Use online translation first when allowed and available; use offline fallback when online is disabled, unavailable, times out, fails, or returns an invalid result.
- Q: How should mixed or unknown source language be handled? -> A: Do not auto-translate mixed or unknown source text unless the caller supplies an explicit source language; otherwise return spoken guidance requesting a clearer direction.
- Q: How should same-language translation requests behave? -> A: Treat same-language requests as successful no-op results, do not call translation providers, preserve the clean text for reading, and return guidance that translation was not needed.
- Q: What counts as a valid translated result? -> A: A translated result must be non-empty, match the requested target language when detectable, and differ from the source except for same-language no-op cases.
- Q: Should successful translations be read aloud automatically? -> A: When a reading layer is available, successful translations should be handed to it for immediate spoken output by default; otherwise the translated result remains available with guidance.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hear Latest Clean Text Translated (Priority: P1)

As a blind user, I need the assistant to translate the latest clean OCR text between Arabic and English and make the translated result available for reading aloud so I can understand content written in the other language.

**Why this priority**: Translation is the primary Phase 7 value after clean OCR text and spoken reading are available.

**Independent Test**: Provide clean Arabic text with a target of English, and clean English text with a target of Arabic; verify each request returns a successful translated result, records the source and target languages, provides user-safe guidance that the translation is ready to read, and hands the translated result to the reading layer when available.

**Acceptance Scenarios**:

1. **Given** clean Arabic text is available and a reading layer is available, **When** translation to English is requested, **Then** the assistant returns an English translation, hands it to reading, and provides guidance that the translated text is being read.
2. **Given** clean English text is available and a reading layer is unavailable, **When** translation to Arabic is requested, **Then** the assistant returns an Arabic translation and guidance that the translated text is ready to read.
3. **Given** no clean text is available, **When** translation is requested, **Then** the assistant does not attempt to translate empty content and returns guidance that no readable text is available.

---

### User Story 2 - Continue When Online Translation Is Unavailable (Priority: P2)

As a blind user, I need translation to continue with a local fallback when online translation is unavailable or fails, so I can still use the assistant with limited or no internet access.

**Why this priority**: The assistant must remain useful in low-cost and intermittent-network settings, and translation failure must not become a silent dead end.

**Independent Test**: Simulate online translation disabled, unavailable, timeout, invalid, or failed; verify the assistant announces fallback use, attempts the local translation path when allowed, and returns either a valid translated result or a final user-safe failure with recovery guidance.

**Acceptance Scenarios**:

1. **Given** online translation is disabled, unavailable, timed out, failed, or returned an invalid result, **When** a valid translation is requested and offline fallback is allowed, **Then** the assistant skips or abandons the online path and attempts local translation.
2. **Given** online translation fails, **When** local translation succeeds, **Then** the assistant returns the local translated result and guidance that fallback translation was used.
3. **Given** every allowed translation option fails, **When** translation is requested, **Then** the assistant returns a structured failure and tells the user what to try next.

---

### User Story 3 - Translate With Clear Language Direction And Privacy (Priority: P3)

As a blind user, I need the assistant to respect the requested translation direction and protect the original and translated text from normal logs, so private documents remain private while translation behavior stays predictable.

**Why this priority**: Receipts, forms, medicine instructions, and personal documents may contain sensitive content. Users also need confidence that Arabic-to-English and English-to-Arabic requests do not get reversed.

**Independent Test**: Provide Arabic, English, mixed, and unknown-language clean text with requested target languages; verify direction handling, unsupported-language guidance, privacy-safe metadata, and no raw or translated text in default logs.

**Acceptance Scenarios**:

1. **Given** the latest clean text has known language metadata, **When** the user requests the opposite target language, **Then** the assistant translates in the requested direction.
2. **Given** clean text is mixed or the source language is uncertain and no explicit source language is supplied, **When** translation is requested, **Then** the assistant uses safe language guidance instead of silently choosing an unsafe direction.
3. **Given** clean text is mixed or the source language is uncertain and an explicit supported source language is supplied, **When** translation is requested, **Then** the assistant translates using the supplied direction.
4. **Given** translation succeeds or fails, **When** default logs are inspected, **Then** raw OCR text, clean text, translated text, and snippets are absent.

### Edge Cases

- Empty, whitespace-only, or cleanup-failed text must not be translated.
- Source and target language being the same must return guidance without unnecessary translation.
- Unsupported source or target language must return clear guidance.
- Same-language requests must be successful no-op results that preserve the clean text for reading and do not call translation providers.
- Mixed Arabic/English text and unknown-language text must not be translated unless an explicit supported source language is supplied.
- Online translation disabled, unavailable, timeout, invalid response, weak response, or service error must not crash the assistant.
- Invalid translation results, including empty output or detectable wrong-language output, must trigger fallback when fallback is allowed.
- Local translation unavailable or failed must return a structured final failure.
- Translation must preserve the latest clean OCR text as the source; it must not use raw OCR text.
- Translation output must be handed to the existing reading layer for immediate spoken output when the reading layer is available.
- Default logs must not include raw OCR text, clean text, translated text, or snippets.
- This phase must not capture camera frames, run OCR, clean text, parse voice commands, or orchestrate the full assistant workflow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept the latest clean OCR text and translate it between Arabic and English on request.
- **FR-002**: System MUST support Arabic-to-English and English-to-Arabic translation requests.
- **FR-003**: System MUST return structured success or failure results for translation operations.
- **FR-004**: System MUST avoid translating empty or whitespace-only text and MUST return guidance when no readable text is available.
- **FR-005**: System MUST preserve the source clean text separately from translated text.
- **FR-006**: System MUST record source language, target language, selected translation path, fallback use, duration when available, and user-safe guidance.
- **FR-007**: System MUST use a free online translation path when allowed and available.
- **FR-008**: System MUST use a local offline fallback when online translation is disabled, unavailable, fails, times out, is disallowed, or returns an invalid result.
- **FR-009**: System MUST return final guidance when all allowed translation paths fail.
- **FR-010**: System MUST detect or accept source language metadata for Arabic, English, mixed, and unknown clean text.
- **FR-011**: System MUST return guidance instead of silently translating when source language is mixed, unknown, or unsupported unless an explicit supported source language is supplied.
- **FR-012**: System MUST treat same-language requests as successful no-op results, preserve the clean text for reading, and avoid calling translation providers.
- **FR-013**: System MUST hand successful translated text to the existing reading layer for immediate spoken output when the reading layer is available, and MUST return the translated result with guidance when reading is unavailable.
- **FR-014**: System MUST provide user-safe spoken guidance for translation start, fallback use, success, same-language requests, unsupported-language requests, no-text requests, and translation failure.
- **FR-015**: System MUST exclude raw OCR text, clean text, translated text, and snippets from default logs.
- **FR-016**: System MUST expose translation behavior behind a stable boundary so translation providers can be replaced without changing assistant workflow logic.
- **FR-017**: System MUST keep this phase scoped to translation, translation fallback, translated-result state, reading handoff, and translation guidance only.
- **FR-018**: System MUST treat a translated result as valid only when it is non-empty, compatible with the requested target language when detectable, and different from the source except for same-language no-op cases.
- **FR-019**: System MUST keep only the latest source and translated text in normal in-memory translation state and MUST replace it on each new translation request.

### Constitution Requirements

- **CR-001**: Feature MUST be usable without visual confirmation and MUST define spoken feedback for translation start, fallback use, success, unsupported language, no text, same-language request, and failure.
- **CR-002**: Feature MUST document translation fallback behavior because it touches translation workflow.
- **CR-003**: Feature MUST avoid paid-service dependency; online translation must be free, optional, and replaceable, with a local offline fallback.
- **CR-004**: Feature MUST define privacy behavior for raw OCR text, clean text, translated text, logs, and debug artifacts.
- **CR-005**: Feature MUST define measurable acceptance criteria for Arabic-to-English, English-to-Arabic, mixed or unknown language handling, fallback behavior, reading handoff, and failure modes.

### Key Entities *(include if feature involves data)*

- **TranslationRequest**: Represents clean source text, source language, target language, online permission, offline permission, and operation context.
- **TranslationResult**: Represents translated text, source language, target language, selected translation path, fallback use, duration if available, validity status, reading-handoff status, success or failure, and user-safe guidance.
- **TranslationEngine**: Represents a replaceable translation boundary that can translate or return a structured failure.
- **TranslationError**: Represents stable translation failure categories and user-safe guidance.
- **TranslationState**: Represents the latest source clean text identity, latest translated text, source and target languages, selected path, fallback use, reading-handoff status, and last operation; normal state keeps only the latest translation and replaces it on each new request.
- **TranslationControlRequest**: Represents a user or later command request to translate to Arabic or translate to English.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of Arabic-to-English translation tests return the expected English translated result or a structured fallback/failure result.
- **SC-002**: 100% of English-to-Arabic translation tests return the expected Arabic translated result or a structured fallback/failure result.
- **SC-003**: 100% of empty or whitespace-only translation requests return guidance and do not call translation providers.
- **SC-004**: 100% of simulated online-unavailable or online-failure cases attempt the local fallback when offline translation is allowed.
- **SC-005**: 100% of all-provider-failure cases return structured failure and user-safe recovery guidance without uncaught exceptions.
- **SC-006**: 100% of same-language requests return successful no-op results and do not call translation providers.
- **SC-007**: 100% of unsupported-language, mixed-language without explicit source, or unknown-language without explicit source cases return clear guidance and avoid silent unsafe direction choices.
- **SC-008**: Default logs contain no raw OCR text, clean text, translated text, or snippets in 100% of privacy tests.
- **SC-009**: 100% of scope-boundary tests confirm this phase does not capture camera frames, run OCR, clean text, parse voice commands, or orchestrate the full assistant workflow.
- **SC-010**: 100% of successful translation results are handed to the existing reading layer when it is available, without changing the translated text.
- **SC-011**: 100% of invalid translated results trigger fallback when fallback is allowed or return a structured final failure when no fallback remains.
- **SC-012**: 100% of translation-state tests show only the latest source and translated text are retained in normal in-memory state.

## Assumptions

- Phase 7 receives clean text and language metadata from Phase 5 or equivalent tests; it does not perform OCR or cleanup itself.
- Phase 7 may use the existing Phase 6 reading layer to read translated output, but it does not implement new speech behavior.
- The initial online translation option is free, optional, and replaceable; the local offline fallback remains available for no-internet or service-failure cases.
- Translation requests are limited to Arabic and English in this phase.
- Mixed or unknown source language requires safe guidance unless the caller supplies an explicit supported source language.
- Same-language translation requests are treated as successful no-op results that can still be read aloud.
- A successful translation should be read aloud immediately when the existing reading layer is available.
- Normal translation state stores only the latest source and translated result in memory; this phase does not add persistent translation history.
- User-facing spoken feedback is represented as guidance text in this phase and can be routed to spoken reading by the translation controller.
- Privacy defaults follow the existing project policy: text content is excluded from normal logs and sensitive text logging requires explicit opt-in outside normal operation.

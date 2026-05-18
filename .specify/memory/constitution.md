<!--
Sync Impact Report
Version change: unratified template -> 1.0.0
Modified principles:
- Placeholder Principle 1 -> Accessibility First
- Placeholder Principle 2 -> Accuracy Before Speed
- Placeholder Principle 3 -> Free Online-First, Offline-Fallback Design
- Placeholder Principle 4 -> Graceful Degradation and Human-Understandable Failures
- Placeholder Principle 5 -> Privacy, Modularity, Testability, and Raspberry Pi Resource Awareness
Added sections:
- Assistive System Constraints
- Development Workflow and Quality Gates
Removed sections:
- Placeholder-only template guidance
Templates requiring updates:
- updated .specify/templates/plan-template.md
- updated .specify/templates/spec-template.md
- updated .specify/templates/tasks-template.md
- not applicable .specify/templates/commands/*.md because the commands directory is absent
Follow-up TODOs: None
-->

# Blind OCR Assistant Constitution

## Core Principles

### I. Accessibility First
Every user-facing workflow MUST be usable by a blind or visually impaired user
without visual confirmation. The assistant MUST provide spoken feedback for
command recognition, capture readiness, capture problems, OCR progress, fallback
use, successful reading, translation, pauses, repeats, and failures. No essential
action MAY require reading a screen, inspecting an image preview, or interpreting
visual-only status.

Rationale: This project is an assistive reading system, not a visual OCR utility.
Accessibility is the primary product requirement and must govern all tradeoffs.

### II. Accuracy Before Speed
The system MUST prefer reliable reading over fast but weak OCR. It MUST assess
image quality before OCR, capture multiple frames when practical, select the best
frame, preprocess images, and reject clearly poor input with spoken guidance
instead of silently producing low-quality text. High Accuracy Mode MUST be
available and MAY spend additional time comparing OCR results.

Rationale: Blind users cannot visually verify OCR output. Wrong or partial text
can be more harmful than a slower workflow that clearly asks for recapture.

### III. Free Online-First, Offline-Fallback Design
The initial system MUST NOT depend on paid APIs or billing-required services.
Online OCR, speech, or translation services MAY be used only when they are free,
optional, and replaceable. OCR.space Free API is the online OCR primary;
PaddleOCR is the main offline accuracy fallback; Tesseract with Arabic and
English data is the emergency OCR fallback. LibreTranslate may be used as a free
or self-hosted translation primary, and Argos Translate MUST remain available as
the offline translation fallback. Vosk MUST remain available for offline fixed
voice commands.

Rationale: The assistant must remain usable in low-cost and intermittent-network
settings on Raspberry Pi hardware.

### IV. Graceful Degradation and Human-Understandable Failures
Failure in one layer MUST trigger the next viable fallback unless all alternatives
have failed. The assistant MUST explain fallback transitions and final failures in
short spoken language. If no text is found, OCR confidence is weak, the image is
blurred, lighting is poor, translation fails, or internet access is unavailable,
the user MUST hear what happened and what to try next.

Rationale: Silent failure is inaccessible. Clear degradation preserves user trust
and keeps the workflow recoverable.

### V. Privacy, Modularity, Testability, and Raspberry Pi Resource Awareness
The system MUST minimize storage and transmission of user content. Images MUST
only be uploaded to the selected online provider when online OCR is intentionally
used, and permanent image saving MUST require explicit debug configuration. Logs
MUST be local by default and MUST avoid sensitive text unless explicitly enabled.

OCR, translation, STT, and TTS engines MUST be implemented behind stable
interfaces so engines can be swapped without changing orchestration logic.
Engine-specific code MUST stay isolated from command handling, capture, cleanup,
and speaking workflows.

Each feature MUST include measurable validation appropriate to its risk:
automated tests for pure logic and interfaces, integration or manual acceptance
tests for assistive workflows, and benchmark coverage for Arabic, English, mixed
text, blur, lighting, angle, distance, and small fonts when OCR behavior changes.
OCR attempts MUST record selected engine, duration, quality score, fallback use,
and failure reason.

Runtime design MUST respect Raspberry Pi 4 Model B with 4GB RAM. Heavy engines
MUST be lazy-loaded, cascade execution MUST be the default, OCR engines MUST NOT
all run in parallel by default, camera resources MUST be released, queues and
timeouts MUST be bounded, and continuous OCR on every frame MUST NOT be part of
the initial system.

Rationale: The assistant handles sensitive real-world text on constrained
hardware. Clean boundaries, privacy controls, logs, benchmarks, and resource
limits are required for safe iteration.

## Assistive System Constraints

The project targets Python 3.10+ on Linux for Raspberry Pi 4 Model B with an
Orbbec Astra Pro camera. Core implementation MUST prioritize OpenCV-based image
quality checks, best-frame selection, OCR preprocessing, Arabic and English text
cleanup, right-to-left handling, language detection, full-text TTS, and
Arabic-English translation on demand.

The initial version MUST exclude paid OCR, STT, TTS, or translation services;
cloud storage of user images or text by default; user accounts; model training;
custom OCR fine-tuning; continuous every-frame OCR; and open-ended natural
language conversation beyond fixed assistant commands.

Configuration MUST make online providers, offline fallbacks, debug image saving,
sensitive-text logging, frame counts, timeouts, and quality thresholds explicit.
Defaults MUST be privacy-preserving, resource-aware, and functional without paid
services.

## Development Workflow and Quality Gates

Plans MUST pass a Constitution Check before research and again after design. The
check MUST document how the feature satisfies accessibility, accuracy,
free-service constraints, offline fallback, graceful degradation, privacy,
engine modularity, testability, observability, and Raspberry Pi resource limits.

Specifications MUST include independently testable user journeys, spoken feedback
expectations, failure and fallback behavior, privacy expectations, and measurable
success criteria. Ambiguous requirements MUST be marked clearly before
implementation planning.

Tasks MUST be organized by independently valuable user stories and MUST include
quality gates for capture guidance, OCR quality decisions, fallback paths,
translation fallback, local logging, privacy configuration, resource limits, and
assistive acceptance tests whenever the feature touches those areas.

Implementation reviews MUST reject changes that introduce paid-service
dependency, visual-only essential workflows, silent failure, unnecessary upload or
storage, unbounded heavy model usage, or engine-specific coupling in the cascade
controller.

## Governance

This constitution supersedes conflicting project plans, templates, task lists,
and implementation preferences. Changes to product behavior, architecture, or
workflow MUST be checked against the Core Principles before acceptance.

Amendments require an explicit rationale, an updated Sync Impact Report, review
of affected Spec Kit templates, and a semantic version change:

- MAJOR: Removes or redefines a core principle or permits behavior previously
  forbidden by this constitution.
- MINOR: Adds a principle, required section, quality gate, or materially expands
  governance.
- PATCH: Clarifies language without changing project obligations.

Compliance MUST be reviewed during planning, task generation, implementation
review, and release readiness. Any approved exception MUST be documented in the
feature plan with the affected principle, reason, rejected simpler alternative,
and mitigation.

**Version**: 1.0.0 | **Ratified**: 2026-05-17 | **Last Amended**: 2026-05-17

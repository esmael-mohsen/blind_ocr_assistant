# Implementation Plan: Phase 11 Raspberry Pi Deployment Hardening

**Branch**: `012-phase11-pi-deployment` | **Date**: 2026-05-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/012-phase11-pi-deployment/spec.md`

## Summary

Phase 11 hardens the completed Blind OCR Assistant for real Raspberry Pi use.
The implementation will add deployment readiness models, lightweight startup
checks, explicit full hardware diagnostics, privacy-safe local readiness
reports, bounded log retention, manual and optional service startup assets,
Raspberry Pi dependency setup guidance, and troubleshooting documentation.
This phase verifies existing assistant, camera, OCR fallback, audio, internet
recovery, and shutdown behavior; it does not add new engines, paid services,
cloud storage, user accounts, visual UI, or new user-facing workflow categories.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0-10 modules; standard library
dataclasses, enums, JSON file handling, path handling, subprocess checks,
platform/resource inspection, signal handling, and logging; existing camera,
OCR, voice, assistant, configuration, and common logging boundaries. No new
mandatory paid or cloud dependency is required.

**Storage**: Local filesystem only. Readiness reports are written as
privacy-safe summaries under a local diagnostics/deployment artifact location.
Normal logs stay within a 50 MB default budget. Debug images, raw OCR text,
clean text, translations, secrets, and private debug paths are excluded from
normal logs and deployment validation artifacts.

**Testing**: Unit tests for readiness states, dependency checks, privacy-safe
report serialization, log retention decisions, service template safety, startup
check classification, and scope boundaries. Integration tests use mocked camera,
audio, OCR fallback, internet, and assistant shutdown boundaries. Manual
hardware acceptance remains required for real Raspberry Pi camera, microphone,
speaker, service startup, and repeated start/stop behavior.

**Target Platform**: Primary deployment target is Raspberry Pi OS or
Ubuntu-based Linux on Raspberry Pi 4 Model B with Orbbec Astra Pro. Development
validation may run on Windows/Linux with mocked hardware and local filesystem
checks.

**Project Type**: Single local Python assistive application with deployment
diagnostic helpers, shell scripts, optional service template, and documentation.

**Performance Goals**: Lightweight startup checks must complete quickly enough
to run before every assistant start and must not eagerly load heavy OCR models.
Full diagnostics may take longer because they validate camera, audio, local OCR
fallback, no-internet behavior, internet recovery, and safe shutdown. Long
running operation must avoid sustained memory pressure on the Raspberry Pi 4GB
target and must keep normal logs within the 50 MB default local budget.

**Constraints**: No paid services; no mandatory cloud dependency; no visual-only
setup requirement; no user accounts; no new OCR, translation, STT, or TTS
engines; no continuous every-frame OCR; no full parallel OCR execution by
default; service startup remains optional and disabled until a maintainer
enables it; validation artifacts remain privacy-safe local summaries.

**Scale/Scope**: One Raspberry Pi device running one assistant process at a
time. Scope covers startup readiness, explicit diagnostics, dependency setup,
camera/audio/OCR fallback checks, no-internet startup, internet recovery, safe
shutdown, optional service startup, troubleshooting, and log retention.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. Startup, degraded, blocked, manual verification,
  and failure states require spoken or non-visual actionable feedback.
- Accuracy Before Speed: PASS. This phase validates existing OCR fallback and
  camera readiness instead of bypassing quality gates for deployment speed.
- Free Online-First, Offline-Fallback: PASS. Online services remain optional;
  no-internet startup and local OCR fallback readiness are explicit acceptance
  criteria.
- Graceful Degradation: PASS. Readiness states distinguish Ready, Degraded,
  Blocked, and Manual Verification Needed, and failures must produce actionable
  diagnostics.
- Privacy by Default: PASS. Reports and logs exclude images, OCR text,
  translations, secrets, and private debug paths by default.
- Modular Engines: PASS. Deployment checks use existing boundaries and do not
  introduce provider-specific coupling into assistant orchestration.
- Testability and Observability: PASS. Automated tests cover pure readiness,
  serialization, log retention, service assets, and mocked integration paths;
  real hardware checks are documented as manual acceptance.
- Raspberry Pi Resource Awareness: PASS. Startup checks are lightweight, heavy
  models stay lazy, logs are bounded, service startup is optional, and shutdown
  must release camera/audio resources.

Post-design re-check: PASS. The research decisions, data model, contract, and
quickstart preserve accessibility, free-service constraints, offline fallback,
privacy-safe artifacts, modular boundaries, explicit tests, and Raspberry Pi
resource limits. No complexity exceptions are required.

## Project Structure

### Documentation (this feature)

```text
specs/012-phase11-pi-deployment/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- deployment-readiness-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
modules/
|-- deployment/
|   |-- __init__.py
|   |-- readiness_models.py
|   |-- readiness_checks.py
|   |-- diagnostics.py
|   |-- report_writer.py
|   |-- log_retention.py
|   `-- service_assets.py
|-- assistant/
|-- camera/
|-- common/
|-- ocr/
`-- voice/

scripts/
|-- install_pi_dependencies.sh
|-- run_assistant.sh
`-- pi_deployment_check.py

deploy/
`-- blind-ocr-assistant.service.template

tests/
|-- unit/
|   |-- test_deployment_readiness_models.py
|   |-- test_deployment_readiness_checks.py
|   |-- test_deployment_report_writer.py
|   |-- test_deployment_log_retention.py
|   |-- test_deployment_service_assets.py
|   `-- test_deployment_scope_boundaries.py
`-- integration/
    `-- test_deployment_diagnostics.py

docs/
|-- troubleshooting.md
`-- architecture.md
```

**Structure Decision**: Add a focused `modules.deployment` package for
readiness models, checks, diagnostics orchestration, privacy-safe reporting, log
retention, and service asset validation. Keep executable entry points in
`scripts/` and the optional service template in `deploy/` so deployment assets
do not mix with OCR, voice, or assistant workflow modules.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 11.

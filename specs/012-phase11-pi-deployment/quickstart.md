# Phase 11 Quickstart: Raspberry Pi Deployment Hardening

## Purpose

Phase 11 verifies that the Blind OCR Assistant can run reliably on Raspberry Pi
hardware with accessible startup feedback, local fallback readiness, privacy-safe
diagnostics, bounded logs, safe stop behavior, and optional service startup.

## Expected Files

```text
modules/deployment/__init__.py
modules/deployment/readiness_models.py
modules/deployment/readiness_checks.py
modules/deployment/diagnostics.py
modules/deployment/report_writer.py
modules/deployment/log_retention.py
modules/deployment/service_assets.py
scripts/pi_deployment_check.py
scripts/install_pi_dependencies.sh
scripts/run_assistant.sh
deploy/blind-ocr-assistant.service.template
tests/unit/test_deployment_readiness_models.py
tests/unit/test_deployment_readiness_checks.py
tests/unit/test_deployment_report_writer.py
tests/unit/test_deployment_log_retention.py
tests/unit/test_deployment_service_assets.py
tests/unit/test_deployment_scope_boundaries.py
tests/integration/test_deployment_diagnostics.py
docs/troubleshooting.md
docs/architecture.md
```

## Automated Validation

Run focused Phase 11 tests:

```powershell
python -m pytest tests/unit/test_deployment_readiness_models.py
python -m pytest tests/unit/test_deployment_readiness_checks.py
python -m pytest tests/unit/test_deployment_report_writer.py
python -m pytest tests/unit/test_deployment_log_retention.py
python -m pytest tests/unit/test_deployment_service_assets.py
python -m pytest tests/unit/test_deployment_scope_boundaries.py
python -m pytest tests/integration/test_deployment_diagnostics.py
```

Or run them together:

```powershell
python -m pytest tests/unit/test_deployment_readiness_models.py tests/unit/test_deployment_readiness_checks.py tests/unit/test_deployment_report_writer.py tests/unit/test_deployment_log_retention.py tests/unit/test_deployment_service_assets.py tests/unit/test_deployment_scope_boundaries.py tests/integration/test_deployment_diagnostics.py
```

Run full unit regression:

```powershell
python -m pytest tests/unit
```

Run available quality checks:

```powershell
python -m ruff check .
python -m black --check .
python -m mypy .
```

If optional tools are not installed, record that they could not be run and keep
pytest plus ruff as the required validation baseline.

## Deployment Diagnostics Smoke Runs

Development-machine diagnostics without real hardware:

```powershell
python scripts/pi_deployment_check.py --full --skip-hardware
```

Offline readiness diagnostics:

```powershell
python scripts/pi_deployment_check.py --full --offline --skip-hardware
```

Expected behavior:

- Writes a privacy-safe local readiness report.
- Uses Ready, Degraded, Blocked, and Manual Verification Needed statuses.
- Does not store user images, OCR text, translations, secrets, or private debug
  paths.
- Does not load heavy OCR engines during lightweight startup checks.
- Records hardware areas as Manual Verification Needed when real hardware is
  skipped or unavailable.
- Returns non-zero only for Blocked status or safe report-write failure.

Example lightweight output:

```text
Overall status: degraded
Deployment readiness is degraded, but the assistant can continue.
Checks:
- config.load: ready - Configuration loaded with deployment-safe defaults.
- network.online_optional: degraded - Online services are unavailable; local fallback can be used.
Mode: lightweight startup checks
```

Example full skipped-hardware output:

```text
Overall status: manual_verification_needed
Deployment readiness needs manual verification.
Mode: full deployment diagnostics
Hardware: skipped; manual verification remains required.
Service: manual startup available; service template remains disabled by default.
Logs: normal log retention budget is checked at 50 MB by default.
```

## Raspberry Pi Manual Acceptance

On target Raspberry Pi hardware:

1. Run the dependency install script and confirm it completes without paid
   service setup.
2. Run the manual assistant startup script and confirm spoken startup status.
3. Run full deployment diagnostics with camera, speaker, and microphone
   connected.
4. Confirm RGB capture readiness and depth or RGB-only degraded status.
5. Confirm speaker output can be heard.
6. Confirm command input is usable or documented as Manual Verification Needed.
7. Start without internet and confirm degraded offline readiness.
8. Trigger a reading workflow without internet and confirm local OCR fallback is
   attempted.
9. Restore internet and confirm a later workflow can detect online availability.
10. Run repeated start/stop cycles and confirm camera/audio resources are
    released.
11. Confirm normal logs remain within the 50 MB default local budget.
12. Confirm normal logs and reports contain no user images, OCR text,
    translations, secrets, or private debug paths.

## Optional Service Startup

Service startup must remain disabled by default.

Manual acceptance before enabling service mode:

1. Confirm manual startup works.
2. Confirm full diagnostics are Ready or explicitly accepted as Degraded.
3. Review privacy settings and debug flags.
4. Install the service template intentionally.
5. Enable the service intentionally.
6. Reboot the Raspberry Pi.
7. Confirm the assistant starts or a clear local service failure is recorded.
8. Confirm service stop releases camera/audio resources.

## Acceptance Checklist

- Lightweight startup checks run before declaring readiness.
- Full diagnostics are available as a maintainer action.
- Readiness states are Ready, Degraded, Blocked, and Manual Verification Needed.
- No-internet startup preserves local reading readiness when local dependencies
  are available.
- Preferred offline OCR and emergency OCR fallback readiness are validated.
- Camera diagnostics report ready, degraded RGB-only, blocked, or manual
  verification needed.
- Audio diagnostics report spoken-output and command-input readiness or manual
  verification needed.
- Manual startup script remains available.
- Optional service template is disabled by default.
- Safe stop behavior releases camera/audio resources.
- Normal logs stay within a 50 MB default local budget.
- Deployment reports are privacy-safe local summaries only.
- Troubleshooting documentation covers startup, dependency, camera, audio,
  offline mode, OCR fallback, service failures, log rotation, and privacy.

## Phase 11 Validation Results

Recorded on 2026-05-19:

```powershell
python -m pytest tests/unit/test_deployment_readiness_models.py tests/unit/test_deployment_readiness_checks.py tests/unit/test_deployment_report_writer.py tests/unit/test_deployment_log_retention.py tests/unit/test_deployment_service_assets.py tests/unit/test_deployment_scope_boundaries.py tests/integration/test_deployment_diagnostics.py
# 32 passed

python -m pytest tests/unit
# 382 passed

python -m ruff check .
# All checks passed

python scripts/pi_deployment_check.py --full --skip-hardware --output-dir deployment_diagnostics/smoke
# wrote a report and returned 1 because this development machine is missing full local OCR dependencies

python scripts/pi_deployment_check.py --full --offline --skip-hardware --output-dir deployment_diagnostics/smoke-offline
# wrote a report and returned 1 because this development machine is missing full local OCR dependencies

python -m black --check .
# unavailable: No module named black

python -m mypy .
# unavailable: No module named mypy
```

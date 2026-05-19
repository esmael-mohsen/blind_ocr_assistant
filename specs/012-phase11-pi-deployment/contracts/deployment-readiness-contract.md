# Contract: Phase 11 Deployment Readiness Workflow

## Purpose

Define the maintainer-facing deployment readiness contract for Phase 11. The
contract describes startup checks, full diagnostics, report outputs, privacy
guarantees, service startup behavior, log retention, and failure handling for
Raspberry Pi deployment hardening.

## Command Contract

### Lightweight Startup Check

The assistant startup path must run lightweight readiness checks before
declaring normal readiness.

Expected behavior:

- Check configuration, local folders, log readiness, privacy settings, basic
  dependency availability, and optional online/offline mode status.
- Do not eagerly load heavy OCR models.
- Do not capture images or audio samples.
- Do not require internet access to declare degraded local readiness.
- Announce Ready, Degraded, Blocked, or Manual Verification Needed status in a
  non-visual form.

### Full Deployment Diagnostics

```powershell
python scripts/pi_deployment_check.py --full
```

Required flags:

- `--full`: run maintainer diagnostics for hardware and fallback readiness.
- `--output-dir PATH`: optional local diagnostics output root.
- `--offline`: simulate or enforce no-online-service validation where possible.
- `--skip-hardware`: allow development-machine diagnostics that produce Manual
  Verification Needed for real hardware areas.

Supported statuses:

- `ready`
- `degraded`
- `blocked`
- `manual_verification_needed`

Report fields:

- `report_id`
- `created_at`
- `target_device`
- `overall_status`
- `startup_mode`
- `checks`
- `privacy_summary`
- `recommended_actions`
- optional `service_startup`
- optional `log_retention`

The command must return a non-zero exit status only when the overall readiness
status is Blocked or the report cannot be written safely.

## Readiness Status Contract

All checks must use these statuses:

- `ready`: usable for deployment.
- `degraded`: usable with reduced capability, such as no internet or RGB-only
  camera operation.
- `blocked`: cannot declare deployment readiness until fixed.
- `manual_verification_needed`: automated validation cannot prove the result.

Overall status is the most severe check status, ordered as:

```text
blocked > manual_verification_needed > degraded > ready
```

## Report Output Contract

Each full diagnostics run writes a privacy-safe local report:

```text
deployment_diagnostics/<run-id>/
|-- readiness_report.json
`-- readiness_summary.md
```

Example `readiness_report.json`:

```json
{
  "report_id": "20260519-raspi-readiness",
  "overall_status": "degraded",
  "startup_mode": "manual",
  "checks": [
    {
      "check_id": "network.online_optional",
      "status": "degraded",
      "message": "Online services are unavailable; local fallback remains ready.",
      "spoken_message": "Offline mode is available.",
      "remediation": "Connect to the internet to use online-first services."
    }
  ],
  "privacy_summary": {
    "contains_user_images": false,
    "contains_ocr_text": false,
    "contains_translations": false,
    "contains_secrets": false,
    "contains_private_debug_paths": false
  }
}
```

## Privacy Contract

Deployment checks, summaries, reports, and normal logs must not include:

- raw user images
- image payloads
- raw OCR text
- clean OCR text
- translated text
- recognized speech text
- provider secrets
- endpoint credentials
- private debug artifact paths

Safe outputs may include status, check identifiers, durations, safe categories,
redacted configuration presence, and actionable remediation text.

## Hardware Diagnostics Contract

Full diagnostics must attempt or document:

- Camera RGB capture readiness and resource release.
- Depth availability or RGB-only degraded mode.
- Speaker output readiness or manual verification requirement.
- Microphone command-input readiness or manual verification requirement.
- Preferred offline OCR readiness.
- Emergency OCR fallback readiness.
- No-internet startup readiness.
- Temporary internet failure and recovery behavior when testable.
- Safe manual stop and service stop behavior when applicable.

When hardware is unavailable on the current machine, diagnostics must record
Manual Verification Needed rather than pretending success.

## Service Startup Contract

Deployment assets must provide:

- A manual run script.
- An optional service template.
- Disabled-by-default service behavior.
- Clear enable, disable, status, and stop instructions.
- Local log access guidance.

The install/setup flow must not automatically enable unattended startup.

## Log Retention Contract

Normal logs must stay within a 50 MB default local budget.

Log retention checks must:

- Measure local normal-log usage when possible.
- Report Ready when within budget.
- Report Degraded or Blocked when logs cannot be measured or written safely,
  depending on impact.
- Rotate or prune only normal logs, not private debug captures, unless
  explicitly configured.
- Preserve privacy-safe summaries.

## Failure Contract

Deployment readiness must return structured outcomes for:

- missing dependency
- missing optional online configuration
- no internet at startup
- internet failure during use
- camera unavailable
- RGB-only degraded camera operation
- audio output unavailable
- microphone unavailable
- local OCR fallback unavailable
- emergency OCR fallback unavailable
- heavy model load failure during full diagnostics
- log directory missing or read-only
- log budget exceeded
- privacy-risky debug setting enabled
- service template missing
- service enabled without validation
- report write failure
- manual verification needed

Failures must include a safe remediation message and must not expose private
content.

Failure categories are represented by stable check IDs, including:

- `dependencies.basic_modules`
- `network.online_optional`
- `network.no_internet_startup`
- `network.temporary_failure`
- `network.restored_connectivity`
- `camera.rgb_depth`
- `camera.resource_release`
- `audio.speaker_output`
- `audio.microphone_input`
- `ocr.paddleocr_full`
- `ocr.tesseract_full`
- `logs.retention_budget`
- `logs.rotate_prune_plan`
- `privacy.defaults`
- `service.manual_run_script`
- `service.template`
- `service.enablement`

## Scope Boundary Contract

Phase 11 deployment code must not:

- add OCR engines
- add translation engines
- add STT or TTS engines
- add assistant command categories
- add visual UI requirements
- require cloud storage
- create user accounts
- require paid services
- enable service startup automatically
- store user images, OCR text, translations, secrets, or private debug paths in
  normal deployment reports

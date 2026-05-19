# Data Model: Phase 11 Raspberry Pi Deployment Hardening

## DeploymentReadinessReport

Represents one privacy-safe local deployment validation summary.

**Fields**

- `report_id`: Unique local identifier for the report.
- `created_at`: Timestamp for the validation run.
- `target_device`: Safe device label, such as Raspberry Pi 4.
- `overall_status`: `ready`, `degraded`, `blocked`, or
  `manual_verification_needed`.
- `startup_mode`: `manual`, `service_template`, or `service_enabled`.
- `checks`: Ordered list of readiness check results.
- `privacy_summary`: Flags proving sensitive content is excluded.
- `recommended_actions`: Safe actionable next steps.

**Validation Rules**

- Must not contain raw images, OCR text, clean text, translations, secrets, or
  private debug paths.
- Must include at least one check result.
- Overall status must be the most severe status from the included checks.
- Reports are local artifacts only.

**Relationships**

- Has many `HardwareCheckResult` and `DependencyCheckResult` entries.
- References one `LogRetentionPolicy` summary when log checks run.
- May reference one `ServiceStartupOption`.

## ReadinessStatus

Canonical status used by all deployment checks.

**Values**

- `ready`: The area is usable for deployment.
- `degraded`: The assistant can continue with reduced capability.
- `blocked`: Normal use must not be declared ready until fixed.
- `manual_verification_needed`: Automated validation cannot prove the area.

**Validation Rules**

- User-facing summaries must describe each status without relying on color or
  visual-only cues.
- Startup must not announce full readiness when any check is `blocked`.

## HardwareCheckResult

Represents a camera, audio output, audio input, or resource release check.

**Fields**

- `check_id`: Stable check identifier.
- `hardware_area`: `camera`, `depth`, `speaker`, `microphone`, `resources`, or
  `unknown`.
- `status`: One `ReadinessStatus`.
- `message`: Safe human-readable summary.
- `spoken_message`: Short message suitable for voice feedback.
- `remediation`: Safe next step for maintainers.
- `duration_ms`: Non-negative duration when measured.
- `safe_metadata`: Optional safe facts such as RGB-only mode.

**Validation Rules**

- Must not include private image paths, captured frames, audio samples, or
  recognized speech text.
- Must classify RGB-only camera operation as degraded when depth is unavailable
  but capture can proceed.
- Must confirm resource release for camera/audio checks when possible.

**Relationships**

- Belongs to one `DeploymentReadinessReport`.

## DependencyCheckResult

Represents a local dependency, configuration, model/data, folder, or optional
online setting check.

**Fields**

- `check_id`: Stable check identifier.
- `dependency_area`: `config`, `folders`, `ocr_space`, `paddleocr`,
  `tesseract`, `vosk`, `espeak`, `network`, `logs`, or `privacy`.
- `status`: One `ReadinessStatus`.
- `required_for_startup`: Boolean.
- `message`: Safe diagnostic summary.
- `remediation`: Safe next step.
- `safe_metadata`: Optional safe metadata with no secrets.

**Validation Rules**

- Secrets, endpoint credentials, and private paths must be redacted or omitted.
- Missing optional online settings must be degraded when local fallback is
  ready, not blocked.
- Missing required local fallback dependencies may be blocked.

**Relationships**

- Belongs to one `DeploymentReadinessReport`.

## ServiceStartupOption

Represents the deployment startup mode and optional service asset.

**Fields**

- `mode`: `manual_script`, `service_template`, or `service_enabled`.
- `enabled`: Boolean.
- `template_path`: Local service template path when present.
- `manual_script_path`: Local manual startup script path.
- `safe_stop_supported`: Boolean.
- `notes`: Safe maintainer notes.

**Validation Rules**

- Service template must remain disabled by default.
- Manual startup must remain available even when service mode is not enabled.
- Service instructions must include safe stop behavior and local log access.

**Relationships**

- May be referenced by `DeploymentReadinessReport`.

## LogRetentionPolicy

Represents local normal-log retention behavior.

**Fields**

- `log_root`: Local log directory.
- `normal_log_budget_mb`: Default `50`.
- `current_usage_mb`: Current measured usage when available.
- `status`: One `ReadinessStatus`.
- `rotation_action`: `none`, `rotate`, `prune`, or `manual_verification_needed`.
- `privacy_safe`: Boolean.

**Validation Rules**

- Normal logs must stay within 50 MB by default.
- Rotation must not include raw images, OCR text, translations, secrets, or
  private debug paths in summaries.
- Missing or read-only log directories must produce actionable diagnostics.

**Relationships**

- May be summarized by `DeploymentReadinessReport`.

## TroubleshootingEntry

Represents one documented deployment problem and recovery path.

**Fields**

- `entry_id`: Stable identifier.
- `symptom`: What the maintainer or user observes.
- `likely_cause`: Safe cause summary.
- `diagnosis_step`: Accessible check to run.
- `recovery_action`: Recommended fix.
- `related_status`: One `ReadinessStatus`.
- `privacy_notes`: Content-safety warning when relevant.

**Validation Rules**

- Must cover startup, dependency, camera, audio, offline mode, OCR fallback,
  service failure, log retention, and privacy-risky debug settings.
- Must be usable without requiring visual-only evidence.

## State Transitions

### DeploymentReadinessReport

```text
created -> running -> ready
created -> running -> degraded
created -> running -> blocked
created -> running -> manual_verification_needed
created -> failed_to_write
```

### ServiceStartupOption

```text
manual_script_available -> service_template_available -> service_enabled
service_enabled -> service_disabled
```

- `service_enabled` requires explicit maintainer action.
- `service_disabled` must leave manual startup available.

### LogRetentionPolicy

```text
within_budget -> near_budget -> rotation_needed -> rotation_applied
within_budget -> blocked
```

- `blocked` is used when logs cannot be written, measured, rotated, or pruned
  safely.

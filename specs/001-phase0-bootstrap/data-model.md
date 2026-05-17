# Data Model: Phase 0 Repository Bootstrap

## Project Configuration

Represents centralized defaults used by bootstrap and later phases.

**Fields**
- `languages`: list of supported language codes. Initial value: `["ar", "en"]`.
- `online_first`: boolean. Default: `true`.
- `offline_fallback`: boolean. Default: `true`.
- `debug_save_images`: boolean. Default: `false`.
- `log_level`: string. Default: `INFO`.
- `sensitive_text_logging`: boolean. Default: `false`.
- `frame_capture_count`: integer. Default: `15`.
- `logs_dir`: local path. Default: `logs/`.
- `debug_captures_dir`: local path. Default: `debug_captures/`.
- `benchmark_results_dir`: local path. Default: `benchmark_results/`.
- `config_dir`: local path. Default: `config/`.

**Validation Rules**
- `languages` must include Arabic and English.
- `frame_capture_count` must be positive and bounded; recommended range is
  1-20 for Phase 0 defaults.
- Debug image saving and sensitive text logging default to disabled.
- Directories must resolve to local project paths by default.

## Environment Template

Represents documented environment variables for local setup.

**Fields**
- `OCR_SPACE_API_KEY`: optional, empty by default.
- `LIBRETRANSLATE_URL`: optional, empty by default.
- `DEBUG_SAVE_IMAGES`: optional boolean, default `false`.
- `LOG_LEVEL`: optional string, default `INFO`.
- `SENSITIVE_TEXT_LOGGING`: optional boolean, default `false`.
- `FRAME_CAPTURE_COUNT`: optional integer, default `15`.

**Validation Rules**
- Missing online-service values must not fail Phase 0 bootstrap.
- No value may imply a paid-service requirement.
- Sensitive logging values must be visibly disabled in the example.

## Operation Result

Shared response shape for bootstrap utilities and future engine/controller code.

**Fields**
- `success`: boolean.
- `value`: optional payload.
- `error_code`: optional stable string for failures.
- `message`: human-readable message.

**Validation Rules**
- Successful results must set `success` to `true`.
- Failed results must set `success` to `false` and include `error_code`.
- Messages must be suitable for logs and later spoken error mapping.

## Log Event

Local observability record emitted by bootstrap and future modules.

**Fields**
- `timestamp`: event time.
- `level`: `INFO`, `WARNING`, `ERROR`, or `DEBUG`.
- `event`: stable event name.
- `message`: human-readable message.
- `context`: optional non-sensitive metadata.

**Validation Rules**
- Default logs must contain operational events only.
- User images, OCR text, translations, and voice recordings must not be logged in
  Phase 0.
- Debug-only sensitive fields must remain disabled by default.

## Bootstrap Entrypoint

Command surface for repository readiness.

**Fields**
- `command`: `help` or `self-check`.
- `exit_status`: zero for successful help/readiness; non-zero only for core
  bootstrap failure.
- `checks`: list of readiness checks for imports, config, folders, logging,
  result pattern, and optional tooling status.

**Validation Rules**
- Help must not require hardware, internet, service keys, or engine packages.
- Self-check must create safe local folders if missing.
- Missing optional quality tools must be reported as non-blocking.

## State Transitions

```text
Fresh checkout
  -> Help requested
  -> Usage shown
  -> Exit success

Fresh checkout
  -> Self-check requested
  -> Local folders created if missing
  -> Core bootstrap checks run
  -> Optional tooling status reported
  -> Exit success if core checks pass
```

# Phase 7 Quickstart: Translation Layer

## Purpose

Phase 7 translates latest clean OCR text between Arabic and English using a free
online-first path and local offline fallback. Successful translations are handed
to the existing reading layer when available, while failures return user-safe
guidance and privacy-safe metadata.

## Expected Files

```text
modules/translation/base.py
modules/translation/translation_models.py
modules/translation/libre_translate_client.py
modules/translation/argos_fallback.py
modules/assistant/translation_controller.py
tests/unit/test_translation_models.py
tests/unit/test_translation_base.py
tests/unit/test_libre_translate_client.py
tests/unit/test_argos_fallback.py
tests/unit/test_translation_controller.py
tests/unit/test_translation_logging_privacy.py
tests/unit/test_translation_scope_boundaries.py
tests/fixtures/text/translation_cases.md
```

## Automated Validation

Run focused Phase 7 tests:

```powershell
python -m pytest tests/unit/test_translation_models.py
python -m pytest tests/unit/test_translation_base.py
python -m pytest tests/unit/test_libre_translate_client.py
python -m pytest tests/unit/test_argos_fallback.py
python -m pytest tests/unit/test_translation_controller.py
python -m pytest tests/unit/test_translation_logging_privacy.py
python -m pytest tests/unit/test_translation_scope_boundaries.py
```

Or run them together:

```powershell
python -m pytest tests/unit/test_translation_models.py tests/unit/test_translation_base.py tests/unit/test_libre_translate_client.py tests/unit/test_argos_fallback.py tests/unit/test_translation_controller.py tests/unit/test_translation_logging_privacy.py tests/unit/test_translation_scope_boundaries.py
```

Run the full unit suite after implementation:

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

## Environment Notes

- Live LibreTranslate calls are not required for automated validation; tests use
  a mocked HTTP function.
- Local Argos Translate packages are not required for automated validation;
  tests use a lazy mocked language loader and verify missing-package behavior.
- If `black` or `mypy` is unavailable in the current environment, record that
  result and keep the focused Phase 7 tests, full unit suite, and ruff as the
  required checks.

## Acceptance Checklist

- Arabic-to-English and English-to-Arabic requests return expected translated
  results or structured fallback/failure results.
- Empty text does not call translation providers.
- Online disabled, unavailable, timeout, failure, or invalid output attempts
  offline fallback when allowed.
- All-provider failure returns structured user-safe guidance.
- Same-language requests return successful no-op results without provider calls.
- Mixed or unknown source language requires explicit supported source language.
- Invalid translated results trigger fallback or final structured failure.
- Successful translations are handed to reading when available.
- Normal state keeps only the latest translation.
- Default logs contain no raw OCR text, clean text, translated text, or snippets.
- Phase 7 code does not call camera, OCR, image processing, text cleanup, voice
  command parsing, or full workflow orchestration.

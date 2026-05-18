# Phase 5 Language Detection Fixture Notes

Use these notes to build deterministic tests for language and direction behavior.

- Arabic-only samples should classify as Arabic and RTL.
- English-only samples should classify as English and LTR.
- Mixed Arabic/English samples should classify as mixed and mixed direction.
- Empty, very short, symbol-heavy, or insufficient-evidence samples should
  classify as unknown.
- Dominant language requires at least 60 percent of language-bearing characters.
- Direction metadata must preserve logical reading order for later workflows.


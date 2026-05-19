# Phase 10 Benchmark Fixtures

These fixtures are sanitized local benchmark placeholders for automated Phase
10 validation. They are safe text files that stand in for controlled sample
images during tests and CLI smoke runs.

Fixture policy:

- Use only safe, synthetic, non-private content.
- Label each sample with language and scenario metadata in `manifest.json`.
- Add expected text for every normal Arabic, English, and mixed sample.
- Add expected text for at least half of difficult samples.
- Do not commit private documents, image payloads, secrets, endpoint
  credentials, raw user OCR text, clean user text, translated user text, or
  debug artifact paths.

Manual sample policy:

- Keep private manual samples outside version control.
- Mark private manual samples as `manual_private` or `debug_only` in local
  manifests.
- Share only privacy-safe benchmark summaries.

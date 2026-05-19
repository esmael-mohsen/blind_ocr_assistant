# Phase 7 Translation Fixture Notes

Deterministic tests use mocked providers by default. Fixture samples cover:

- Arabic-to-English translation
- English-to-Arabic translation
- mixed Arabic/English text
- unknown or numeric-only text
- unsupported source and target language guidance
- same-language no-op behavior
- invalid provider result fallback
- all-provider failure guidance

## Representative Samples

- Arabic: `خذ قرصا واحدا يوميا.`
- English: `Take one tablet daily.`
- Mixed: `دواء price`
- Unknown: `12345`
- Unsupported source example: `fr`
- Same-language request: English source to English target preserves the clean text.
- Invalid result example: provider returns empty text, wrong-language text, or unchanged non-no-op text.
- Fallback example: online fails or returns invalid output, then offline returns a valid Arabic or English result.

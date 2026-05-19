# Phase 8 Command Phrase Fixture Notes

Deterministic tests use text-level phrases and mocked recognizers by default.
Fixture samples cover:

- Arabic and English read commands
- Arabic and English stop and continue commands
- Arabic and English repeat sentence and repeat paragraph commands
- Arabic and English translate-to-Arabic and translate-to-English commands
- Arabic and English help commands
- unknown, ambiguous, empty, silence-only, and low-confidence samples
- online unavailable, no-supported-command, and local fallback examples

## Read Commands

- English: `read text`, `read the text`, `start reading`
- Arabic: `اقرأ النص`, `اقرا النص`, `ابدأ القراءة`

## Playback Commands

- Stop: `stop`, `توقف`
- Continue: `continue`, `تابع`
- Repeat sentence: `repeat sentence`, `اعد الجملة`
- Repeat paragraph: `repeat paragraph`, `اعد الفقرة`
- Ambiguous sample: `stop continue`

## Translation And Help Commands

- Translate to Arabic: `translate to Arabic`, `ترجم الى العربية`
- Translate to English: `translate to English`, `ترجم الى الانجليزية`
- Help: `help`, `مساعدة`

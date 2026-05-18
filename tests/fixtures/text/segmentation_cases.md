# Phase 6 Segmentation Fixture Notes

These deterministic samples cover sentence and paragraph splitting for the TTS
reading controller. Tests should assert logical order, stable segment IDs,
blank-line paragraph boundaries, Arabic sentence-ending punctuation, English
sentence-ending punctuation, mixed-language content, and empty-segment removal.

## English

```text
First sentence. Second sentence? Third sentence!

New paragraph starts here. It has another sentence.
```

## Arabic

```text
هذا سطر أول. هذا سؤال؟ هذا تعجب!

هذه فقرة ثانية. تنتهي هنا.
```

## Mixed

```text
Total is 25 EGP. السعر مناسب.

Take one tablet daily. الجرعة بعد الطعام.
```

## Repeat Expectations

- Sentence repeat after full-text start uses the first logical sentence when
  exact speech progress is unknown.
- Paragraph repeat after full-text start uses the first logical paragraph when
  exact speech progress is unknown.
- Repeat requests without prior reading history return guidance and do not speak
  unrelated text.

# Research: Phase 5 Text Cleanup, RTL Handling, and Language Detection

## Decision: Use conservative cleanup by default

**Rationale**: A blind user cannot visually verify removed text. Phase 5 should
normalize obvious OCR noise while preserving ambiguous content and returning
warnings. This aligns with the clarified requirement to avoid destructive
cleanup.

**Alternatives considered**: Aggressive garbage removal was rejected because it
can delete meaningful medicine names, prices, signs, names, or mixed-language
tokens. Leaving all noise untouched was rejected because it makes later reading
harder.

## Decision: Preserve raw OCR text exactly and emit clean text separately

**Rationale**: Raw text is needed for audit, fallback, comparison, and debugging
under explicit privacy controls. Clean text is the user-facing preparation for
later TTS and translation. Keeping both values separate avoids accidental data
loss.

**Alternatives considered**: Mutating raw text in place was rejected because it
breaks traceability. Storing only clean text was rejected because cleanup
mistakes would be impossible to diagnose.

## Decision: Use deterministic whitespace and line-break rules

**Rationale**: Cleanup should be testable and idempotent. Single OCR line breaks
inside paragraphs are collapsed, blank-line paragraph breaks are preserved, and
list-like breaks remain readable.

**Alternatives considered**: Removing all line breaks was rejected because it
destroys paragraph and list structure. Preserving every line break was rejected
because OCR often inserts noisy line breaks inside sentences.

## Decision: Normalize punctuation spacing without changing punctuation meaning

**Rationale**: Arabic, English, and mixed OCR output commonly has spaces before
commas, periods, colons, question marks, and Arabic punctuation. Normalizing
spacing improves later speech flow while preserving punctuation and numbers.

**Alternatives considered**: Removing punctuation was rejected because it harms
reading pauses and meaning. Applying English-only punctuation rules was rejected
because Arabic punctuation must remain readable.

## Decision: Use deterministic language evidence thresholds

**Rationale**: The accepted clarification sets a concrete rule: dominant
language requires enough evidence and at least 60% of language-bearing
characters. Mixed requires meaningful Arabic and English evidence. Otherwise the
result should be unknown.

**Alternatives considered**: External language detection services were rejected
because Phase 5 must work offline and avoid paid services. Always choosing the
largest character class was rejected because very short or symbol-heavy text can
produce false confidence.

## Decision: Preserve logical reading order for Arabic and mixed text

**Rationale**: Later TTS and translation need a stable logical text sequence.
Phase 5 should not reverse strings or create display-only visual ordering.
Direction metadata can tell later workflows that the text contains RTL or mixed
direction content.

**Alternatives considered**: Visual bidi reordering was rejected because it can
damage speech and translation inputs. Ignoring direction metadata was rejected
because later phases need to know whether text is RTL, LTR, mixed, or unknown.

## Decision: Use structured statuses and warnings

**Rationale**: Empty input, noisy text, uncertain language, mixed direction, and
successful cleanup need stable statuses for tests and later spoken guidance.
Warnings keep the workflow recoverable without forcing failure for every
non-fatal issue.

**Alternatives considered**: Returning only a string was rejected because later
workflows need language, warnings, privacy-safe metadata, and guidance. Raising
exceptions for noisy but usable text was rejected because it prevents graceful
degradation.

## Decision: Default logs exclude raw and clean text

**Rationale**: OCR text can contain private documents, medicine labels, payment
information, addresses, or identifiers. Default logs should contain only safe
metadata such as status, detected language, warning codes, text length, and
direction.

**Alternatives considered**: Logging clean text by default was rejected because
clean text is still sensitive. Suppressing all metadata was rejected because
privacy-safe observability is needed for troubleshooting.

## Decision: Keep Phase 5 independent from OCR, TTS, translation, voice, and assistant orchestration

**Rationale**: The implementation plan places Phase 5 after OCR cascade and
before TTS and translation. It should prepare text and expose contracts, not
start upstream or downstream workflows.

**Alternatives considered**: Calling TTS directly after cleanup was rejected
because Phase 6 owns reading control. Calling translation directly was rejected
because Phase 7 owns translation fallback.

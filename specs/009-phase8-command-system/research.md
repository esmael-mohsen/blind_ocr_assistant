# Phase 8 Research: Voice Assistant Command System

## Decision: Use fixed-command recognition rather than open-ended conversation

**Rationale**: The accepted spec and constitution require predictable assistive
behavior. Fixed commands reduce accidental routing, make Arabic and English
coverage testable, and avoid introducing unsupported open-ended dialogue.

**Alternatives considered**: Open-ended natural language conversation was
rejected because it is out of scope for the initial assistant and increases the
risk of unsafe command guesses.

## Decision: Use a curated bilingual phrase catalog with deterministic normalization

**Rationale**: A curated Arabic and English catalog makes command coverage
explicit and testable. Normalization can handle case, whitespace, punctuation,
and simple diacritics without leaking transcript text into logs.

**Alternatives considered**: Broad fuzzy matching was rejected because it can
route ambiguous phrases incorrectly. Exact raw matching only was rejected
because it is too brittle for spoken transcripts.

## Decision: Route only one confidently recognized supported intent

**Rationale**: Blind users need reliable command outcomes. Multi-intent and
low-confidence phrases should return clarification guidance rather than trigger
the wrong action.

**Alternatives considered**: Routing the first matching intent was rejected
because phrase order could cause unsafe behavior. Asking clarification for every
non-exact phrase was rejected because deterministic normalization already
handles harmless transcript variation.

## Decision: Online-first recognition with local fixed-command fallback

**Rationale**: Online recognition can provide useful transcript quality when
available, but the assistant must remain usable without internet. Local fixed
commands preserve core control for reading and translation.

**Alternatives considered**: Online-only recognition was rejected because it
breaks offline use. Local-only recognition was rejected as the only path because
future online STT can improve transcript capture while remaining optional.

## Decision: Lazy-load local Vosk fallback resources

**Rationale**: Vosk models can be large for Raspberry Pi hardware. Lazy loading
keeps import-time memory low and avoids loading models unless fallback is needed
or explicitly requested.

**Alternatives considered**: Eager loading was rejected because it increases
startup time and memory pressure for workflows that use transcript-level tests
or online recognition.

## Decision: Keep command routing in a dialogue manager boundary

**Rationale**: Separating recognition from routing keeps command parsing
replaceable and keeps reading/translation controllers focused on their own
domains. It also makes unavailable-state and privacy tests deterministic.

**Alternatives considered**: Calling reading or translation directly from the
parser was rejected because it would couple phrase matching to assistant
workflow behavior.

## Decision: Discard transcript text after classification

**Rationale**: Spoken command transcripts can contain private content if speech
recognition mishears nearby reading or documents. Retaining only safe metadata
aligns with the project privacy model.

**Alternatives considered**: Keeping a transcript history was rejected because
it is not needed for fixed commands and increases privacy risk.

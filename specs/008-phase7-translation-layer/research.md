# Phase 7 Research: Translation Layer

## Decision: Use online-first translation with local offline fallback

**Rationale**: The project constitution and implementation plan require free
online-first behavior with offline fallback. Online translation gives a useful
default when connectivity is available, while local fallback preserves basic
translation when the network or service is unavailable.

**Alternatives considered**: Online-only translation was rejected because the
assistant must work in intermittent-network settings. Offline-only translation
was rejected as the default because free online translation can provide better
coverage when available. Paid translation was rejected by the cost policy.

## Decision: Keep translation behind a replaceable engine boundary

**Rationale**: A stable `TranslationEngine` boundary lets the controller route
between online and offline providers without coupling workflow logic to provider
details. It also allows deterministic mocked tests for success, timeout,
invalid output, and failure paths.

**Alternatives considered**: Calling a provider directly from the controller was
rejected because it would make fallback behavior harder to test and replace.

## Decision: Lazy-load the offline translation fallback

**Rationale**: Local translation assets can be large relative to the Raspberry
Pi target. Lazy loading keeps import-time memory low and avoids loading offline
models unless fallback is needed or explicitly requested.

**Alternatives considered**: Eager loading was rejected because it increases
startup memory pressure and slows workflows that succeed through online
translation.

## Decision: Validate translated results before acceptance

**Rationale**: Blind users cannot visually verify output. A translated result
must be non-empty, compatible with the target language when detectable, and
different from the source except for same-language no-op cases. Invalid results
trigger fallback when available.

**Alternatives considered**: Accepting any provider success response was
rejected because empty, wrong-language, or unchanged output can mislead users.

## Decision: Mixed or unknown source language requires explicit source metadata

**Rationale**: Mixed or unknown text can be receipts, labels, prices, or product
names where automatic direction guesses are risky. Requiring explicit supported
source language avoids silent unsafe translation choices.

**Alternatives considered**: Auto-selecting the dominant language was rejected
for this phase because Phase 5 already marks uncertain cases, and translation
should not override that uncertainty silently.

## Decision: Same-language requests are successful no-op results

**Rationale**: Same-language requests should not call providers or fail. They
preserve clean text for reading and return guidance that translation was not
needed, which is accessible and easy to test.

**Alternatives considered**: Treating same-language requests as errors was
rejected because it creates unnecessary friction. Calling a provider anyway was
rejected because it wastes resources and may leak content online.

## Decision: Hand successful translations to reading by default when available

**Rationale**: The user goal is assistive understanding without visual
confirmation. Immediate reading of successful translations reduces steps while
keeping translation usable when the reading layer is absent in tests.

**Alternatives considered**: Returning translated text only was rejected as the
default because it would require a separate user action for the primary
assistive flow.

## Decision: Keep only latest translation state in memory

**Rationale**: Phase 7 does not need persistent translation history. Latest-only
state minimizes retention of sensitive content and matches the current assistant
workflow model.

**Alternatives considered**: Maintaining a translation history was rejected
because it increases privacy risk and is not required by the accepted spec.

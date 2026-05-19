# Research: Phase 10 Benchmarking and Accuracy Tuning

## Decision: Use Safe Local Fixture Dataset With Manifest

**Rationale**: A manifest-driven local dataset gives repeatable benchmark runs,
stable labels, and clear privacy classification. It also allows one sample to
cover multiple required labels, which keeps the minimum dataset small enough for
the repository while still satisfying Phase 10 coverage.

**Alternatives considered**:

- Live camera capture only: rejected because automated validation would depend
  on hardware and would not be repeatable.
- Downloaded public OCR datasets: rejected for Phase 10 because licensing,
  size, and privacy review would add scope beyond the project plan.
- Ad hoc filename parsing: rejected because labels, expected text, and privacy
  classification need explicit validation.

## Decision: Minimum Dataset Is 12 Safe Local Samples

**Rationale**: Twelve samples can cover Arabic, English, mixed text, and the
required real-world scenarios while keeping tests lightweight. Overlapping
labels are allowed so one image can represent both a document type and a quality
condition.

**Alternatives considered**:

- Fewer than 12 samples: rejected because it risks under-covering languages and
  difficult capture conditions.
- Large benchmark corpus immediately: rejected because Phase 10 needs a stable
  baseline before expanding fixture size.

## Decision: Expected Text Required For Normal Samples And Half Of Difficult Samples

**Rationale**: Expected-text references enable objective comparison for core
Arabic, English, and mixed reading quality, while allowing some difficult
samples to be measured by metadata-only outcomes when exact transcription is
not practical.

**Alternatives considered**:

- Expected text for every sample: rejected because some low-quality samples are
  intentionally expected to fail image quality or OCR.
- No expected text: rejected because tuning would become subjective and weak.

## Decision: Normalize Expected Text Conservatively

**Rationale**: Ignoring harmless whitespace and line-break differences prevents
false failures caused by OCR layout differences. Preserving language-bearing
characters, numbers, prices, and meaningful punctuation protects Arabic,
English, and mixed-content accuracy.

**Alternatives considered**:

- Exact string comparison only: rejected because OCR often differs in line
  wrapping even when content is correct.
- Aggressive punctuation and number stripping: rejected because receipts,
  medicine packages, prices, codes, and labels depend on those tokens.

## Decision: Timestamped Result Directories

**Rationale**: Separate local result sets make benchmark runs comparable over
time and avoid accidental loss of evidence. This also supports later regression
review without introducing a database.

**Alternatives considered**:

- Overwrite latest results: rejected because it destroys comparison history.
- Database-backed benchmark history: rejected because the project intentionally
  avoids persistent service storage for the initial version.

## Decision: Sequential Engine/Path Comparison By Default

**Rationale**: Sequential measurement matches the Raspberry Pi resource model
and avoids loading or running all OCR engines in parallel. It keeps engine
failures isolated and preserves existing lazy-loading expectations.

**Alternatives considered**:

- Full parallel OCR benchmarking: rejected because it can exceed Raspberry Pi
  memory and conflicts with the constitution's default cascade model.
- Measuring only the normal cascade: rejected because Phase 10 must identify
  best engine/path behavior per scenario.

## Decision: Tuning Recommendations Are Evidence, Not Automatic Changes

**Rationale**: Threshold changes affect what blind users hear. Recommendations
must document evidence, tradeoffs, expected benefit, and regression risk before
any implementation task accepts a change.

**Alternatives considered**:

- Automatically rewrite thresholds from benchmark output: rejected because it
  can silently reduce Arabic, English, or mixed reading quality.
- Manual notes only: rejected because result-driven recommendations should be
  structured and testable.

## Decision: Privacy-Safe Default Results

**Rationale**: Benchmark summaries must be shareable in normal development
without exposing private document content. Result records include lengths,
scores, labels, error codes, and safe paths only when paths are not private
debug artifacts.

**Alternatives considered**:

- Include raw OCR text in every result: rejected because benchmark images may
  contain private real-world content.
- Store image copies by default: rejected because debug image saving must remain
  explicit and bounded.

## Decision: Benchmark Runner Is Separate From Assistant Workflow

**Rationale**: Benchmarking is a maintainer workflow, not a blind user's live
assistant command. Separating it prevents accidental camera, microphone, TTS,
or translation startup during benchmark tests.

**Alternatives considered**:

- Add a voice command for benchmarking: rejected because Phase 10 must not add
  normal assistant command categories.
- Run benchmarks through the full assistant loop: rejected because benchmark
  runs should measure OCR paths without starting live user workflows.

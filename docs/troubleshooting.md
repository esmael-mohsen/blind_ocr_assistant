# Troubleshooting

Phase 0 requires no camera, audio device, internet connection, OCR engine, or
translation service.

## Self-Check Reports Missing Quality Tools

Missing `black` or `mypy` is non-blocking in Phase 0. Install optional quality
tools later if you want to run every local check.

## Runtime Folders Are Missing

Run:

```bash
python main.py --self-check
```

The self-check creates `logs/`, `debug_captures/`, `benchmark_results/`, and
`config/` when they are absent.

## OCR or Camera Is Not Available

That is expected in Phase 0. OCR, camera capture, audio, STT, TTS, translation,
and the full assistive workflow are intentionally deferred.

## Online OCR Credential Is Missing

Phase 1 live online OCR checks are opt-in. Without `OCR_SPACE_API_KEY`, live
tests should skip and local tests should still pass.

## Local Accuracy OCR Model Cannot Load

The local accuracy OCR engine returns `OCR_MODEL_LOAD_ERROR` when the optional
package or model cannot load. Importing the project and running bootstrap help
must not load the heavy model.

## Emergency OCR Is Missing

The emergency OCR engine returns `OCR_EXECUTABLE_NOT_FOUND` when Tesseract is not
installed and `OCR_LANGUAGE_DATA_MISSING` when Arabic or English language data is
not available.

## OCR Finds No Text

Empty or weak OCR output is returned as `NO_TEXT_DETECTED` or `WEAK_OCR_RESULT`,
not as successful OCR.

## Image Is Too Dark Or Too Bright

Phase 2 returns image-quality guidance instead of running OCR. Improve lighting,
avoid glare, and recapture before sending the image to later OCR phases.

## Image Is Blurry

Phase 2 returns steadiness or recapture guidance. Hold the camera steady and try
again before OCR is attempted.

## Image Has Low Contrast

Phase 2 classifies low contrast separately from dark or blurry input. Move the
document to clearer contrast or better lighting, then recapture.

## No Text-Like Region Is Found

Phase 2 blocks unlikely-text images and returns point-to-text guidance. The
text-presence estimator is local and does not run OCR.

## Image Format Is Unsupported

Missing, empty, unreadable, or unsupported image input returns a structured
image-processing error instead of crashing.

## Rejected Image Was Not Preprocessed

That is expected in the normal Phase 2 workflow. Rejected or uncertain images
return corrective guidance first; preprocessing variants are produced only after
an accepted quality report.

## Camera Is Unavailable

Phase 3 first attempts the target depth camera adapter and then generic RGB
fallback. If neither source opens, the capture result returns
`CAMERA_OPEN_FAILED` with user-safe guidance. Local automated tests still pass
without camera hardware because live camera validation is opt-in.

## Generic RGB Fallback Is Used

RGB fallback is expected when the target depth camera, Orbbec SDK, OpenNI2, or
depth support is unavailable. The system can still capture RGB frames and select
the best frame. Depth status may be recorded as unavailable without failing the
capture.

## Camera Capture Times Out

If at least one valid frame was captured before timeout, Phase 3 scores those
valid frames and records `partial_timeout=true`. If no valid frames were
captured, the result returns `CAMERA_CAPTURE_TIMEOUT` and recapture guidance.

## Camera Returns Empty Or Invalid Frames

Empty frames return `CAMERA_EMPTY_FRAME`. Corrupted or dimensionally invalid
frames return `CAMERA_INVALID_FRAME`. These failures are structured and should
not crash the assistant.

## Depth Is Unavailable Or Noisy

Missing, unsupported, unaligned, invalid, or noisy depth maps return an
unavailable depth report. RGB-only selection continues, and the result preserves
the depth status for later spoken guidance.

## Camera Cleanup Fails

Capture code releases resources after success, failure, timeout, and
cancellation. If release fails, the result can return
`CAMERA_RESOURCE_RELEASE_FAILED`. Restart the camera process or disconnect and
reconnect the camera before retrying live validation.

## Image Is Not Ready For OCR

Phase 4 returns `IMAGE_NOT_READY_FOR_OCR` without calling OCR engines when the
selected image was already rejected by image-quality checks. Improve focus,
lighting, framing, or distance, then recapture before retrying OCR.

## Online OCR Is Unavailable

When online OCR is disabled, unavailable, or its availability check times out,
the cascade skips online OCR and routes locally. This is expected offline
behavior and should not upload the image. Local accuracy OCR runs first, with
emergency OCR as fallback.

## Gemini OCR Is Unavailable

Gemini is the preferred online OCR route when `GEMINI_API_KEY` is set and
`ASSISTANT_GEMINI_OCR_ENABLED=true`. If the key is missing, internet is
unavailable, the provider times out, quota is exhausted, or the response cannot
be parsed, the assistant falls back to local OCR when
`ASSISTANT_GEMINI_OCR_FALLBACK_LOCAL=true`.

Use these settings for the Gemini route:

```bash
GEMINI_API_KEY=your-key
ASSISTANT_GEMINI_OCR_ENABLED=true
ASSISTANT_GEMINI_OCR_MODEL=gemini-2.5-flash-lite
ASSISTANT_GEMINI_OCR_TIMEOUT_SECONDS=20
ASSISTANT_GEMINI_OCR_FALLBACK_LOCAL=true
```

Gemini OCR sends the selected image to the Gemini API. Normal logs do not store
the image, Base64 payload, prompt, raw OCR text, cleaned text, or API key. The
Gemini free tier is useful for development, but production use can require
account limits, quota review, or billing depending on Google's current Gemini
API terms.

## Weak OCR Result

OCR output below the default `0.70` quality threshold is treated as weak even if
the engine returned text. Empty, very short, symbol-heavy, repeated-character,
excessively spaced, or fragmented Arabic output can trigger fallback to the next
engine.

## All OCR Engines Failed

If every allowed engine fails or returns unacceptable text, Phase 4 returns
`ALL_OCR_ENGINES_FAILED` with recapture guidance. Try better lighting, steadier
framing, a flatter page angle, or a closer acceptable distance before retrying.

## High Accuracy Mode Picks The Local Result

High Accuracy Mode may choose local accuracy OCR over online OCR when their
quality scores are similar within `0.05`. This is intentional because local OCR
avoids upload and is preferred for near-tie results.

## Sensitive OCR Text Is Missing From Logs

That is expected by default. Phase 4 logs only safe cascade metadata unless both
debug mode and explicit sensitive-text logging are enabled. Do not enable
sensitive text logging for normal use because OCR text can contain private
document content.

## Clean Text Is Empty

Phase 5 returns an empty cleanup result when OCR text is empty or whitespace
only. This is structured and should be spoken later as no readable text being
available. Recapture or rerun OCR with a clearer image.

## Clean Text Is Marked Noisy

Noisy cleanup means the text may contain uncertain OCR fragments. Phase 5 keeps
those fragments instead of deleting them, because they may be meaningful names,
prices, codes, or mixed-language tokens. Review capture quality or rerun OCR if
the spoken result is unclear.

## Language Is Unknown

Unknown language means there was not enough Arabic or English evidence to make a
safe decision. Empty, very short, symbol-heavy, or mostly numeric text can
produce this result. Later workflows should use safe defaults or ask the user
instead of guessing.

## Mixed Direction Text Is Reported

Mixed direction is expected for bilingual Arabic/English content, receipts,
labels, prices, and product names. Phase 5 preserves logical reading order and
records mixed direction metadata for later reading or display workflows.

## Raw Or Clean Text Is Missing From Logs

That is expected by default. Phase 5 logs only safe metadata unless both debug
mode and explicit sensitive-text logging are enabled. Do not enable sensitive
text logging for normal use because raw and clean OCR text can contain private
document content.

## Local TTS Engine Is Missing

Phase 6 returns `TTS_ENGINE_UNAVAILABLE` when the local eSpeak NG executable is
not installed or cannot be found. Automated tests use a mocked speech engine, so
they still pass without live audio. Install eSpeak NG on the Raspberry Pi or
development machine before running the manual TTS smoke test.

## eSpeak NG Crashes On Windows (exit -1073741819)

If `espeak-ng` is installed but crashes immediately on Windows with exit code
`-1073741819` (`0xC0000005` access violation), the process may not be able to
locate its `espeak-ng-data` directory.

Fix by setting `ESPEAK_DATA_PATH` to the folder that contains `phontab` and the
`voices/` directory, then retry:

PowerShell (current session):

```powershell
$env:ESPEAK_DATA_PATH = "$env:USERPROFILE\scoop\apps\espeak-ng\current\espeak-ng-data"
espeak-ng --version
```

CMD (current session):

```bat
set ESPEAK_DATA_PATH=%USERPROFILE%\scoop\apps\espeak-ng\current\espeak-ng-data
espeak-ng --version
```

To persist the setting for your user account (new terminals only):

```powershell
setx ESPEAK_DATA_PATH "$env:USERPROFILE\scoop\apps\espeak-ng\current\espeak-ng-data"
```

## Reading Does Not Pause Natively

Native pause and resume are not guaranteed for the initial eSpeak NG adapter.
When pause is unsupported, Phase 6 stops speech safely, preserves the current
segment, and reports that continue will replay that segment. This is expected
fallback behavior, not a crash.

## Continue Replays Text Instead Of Resuming Mid-Sentence

If the speech engine does not expose a portable resume point, Phase 6 continues
by replaying the current segment. This avoids guessing ahead when spoken
progress is unknown.

## Stop Is Requested When Nothing Is Reading

Stop is idempotent in Phase 6. It leaves reading inactive and returns structured
guidance even when no speech was active.

## Speech Rate Sounds Too Slow Or Too Fast

Requested rates are clamped to the Phase 6 range of 80 through 220 words per
minute. The default is 150 words per minute. Values outside the range are
accepted but adjusted before future speech requests reach the engine.

## Repeat Says There Is Nothing To Repeat

Phase 6 repeats only tracked sentence or paragraph history. If no clean text has
been read yet, repeat returns `NOTHING_TO_REPEAT` guidance and does not speak
unrelated text. Start reading clean text first, then repeat the sentence or
paragraph.

## TTS Smoke Test Prints JSON Instead Of Text

`scripts/test_tts.py` intentionally prints structured safe metadata only. It
does not echo the supplied text because clean OCR text may contain private
document content.

## Online Translation Is Unavailable

Phase 7 uses the online translation path only when online translation is allowed
and a provider is configured. If the online provider is disabled, missing,
timed out, failed, or returns an invalid result, the controller attempts the
local offline fallback when fallback is allowed.

Some public LibreTranslate instances require an API key and will return an
error like "get an API key" without one. If you are using the official managed
endpoint, set `LIBRETRANSLATE_URL` to the `/translate` endpoint and provide an
API key through `LIBRETRANSLATE_API_KEY`.

## Local Translation Fallback Is Unavailable

The Argos Translate fallback is loaded lazily. If the package, installed
languages, or direction model is missing, Phase 7 returns a structured
`OFFLINE_TRANSLATION_UNAVAILABLE` result instead of crashing. Install the local
Argos package and Arabic/English translation packages before relying on offline
translation.

## Translation Timed Out Or Returned An Invalid Result

Timeouts, malformed online responses, empty translated text, wrong-language
output, and unchanged non-no-op output are not accepted as successful
translations. Phase 7 falls back locally when possible, then returns
user-safe recovery guidance if no allowed provider succeeds.

## All Translation Providers Failed

If every allowed translation provider fails or returns invalid output, Phase 7
returns `ALL_TRANSLATION_PROVIDERS_FAILED`. Try again with a clearer language
direction, allow offline fallback, or check that local translation resources are
installed.

## Online Voice Command Recognition Is Unavailable

Phase 8 uses online speech recognition only when allowed and configured. If the
online path is disabled, unavailable, timed out, failed, or produced no
supported command, the assistant attempts local fixed-command recognition when
that fallback is allowed.

## Local Vosk Command Recognition Is Unavailable

The local Vosk command recognizer is loaded lazily. If the package or model is
missing, Phase 8 returns `LOCAL_STT_UNAVAILABLE` instead of crashing. Install
the local Vosk package and fixed-command model resources before relying on
offline voice commands.

## Voice Command Was Not Recognized

Unknown, low-confidence, or no-supported-command phrases return spoken guidance
instead of routing an action. Use short fixed commands such as read text, stop,
continue, repeat sentence, repeat paragraph, translate to Arabic, translate to
English, or help.

## Voice Translation Says There Is No Text

Phase 8 translation commands use the latest clean text only. If no clean text is
available, the command returns guidance instead of translating raw OCR text or
stale content. Run the OCR and cleanup flow first, then ask to translate to
Arabic or English.

## Voice Translation Is Unavailable

The command system does not perform translation itself. It calls an injected
Phase 7 translation controller when available. If that boundary is missing or
returns a failure, Phase 8 returns structured guidance without calling camera,
OCR, image processing, cleanup, or the TTS engine directly.

## Help Command Does Not Start An Action

That is expected. The help command only returns examples of supported fixed
commands and must not trigger reading, translation, capture, OCR, cleanup, or
workflow orchestration.

## All Command Recognizers Failed

If online and local command recognition both fail, Phase 8 returns
`ALL_RECOGNIZERS_FAILED` with recovery guidance. Try again with one short
supported command, or check the local command recognition setup.

## Phase 9 Workflow Is Busy

If another read command is spoken while capture, OCR, cleanup, or reading
startup is already active, the assistant keeps the active workflow and returns
busy guidance. Wait for the current workflow to finish, use playback controls,
or stop the running process through the service or test harness if operational
shutdown is needed.

## Phase 9 Recapture Guidance

If every frame in the bounded capture burst is rejected, the assistant ends the
read attempt and asks for a clearer recapture. It does not automatically loop
captures. Improve lighting, hold the camera steady, point toward printed text,
and issue another read command.

## Phase 9 OCR Or Cleanup Failure

If OCR fails, all OCR engines return weak text, or cleanup produces empty text,
the assistant preserves the previous successful clean text and explains the
failure aloud. Retry with a clearer document position or use translation and
playback controls against the previous successful text when appropriate.

## Phase 9 Translation Or Speech Failure

If translation or reading output fails, the assistant reports the failure and
keeps the session responsive. The latest successful clean text and latest
successful translation remain in memory until replaced by a later success or
cleared by shutdown.

## Phase 9 Boundary Is Unavailable

If command handling, camera capture, OCR, cleanup, translation, or reading has
not been wired into the workflow, Phase 9 returns unavailable guidance instead
of importing or starting a live engine directly. In automated tests, provide
mocked boundaries. In manual runs, wire the existing earlier-phase controllers
before expecting live camera, OCR, translation, or speech behavior.

## Phase 9 Timeout Or Unexpected Failure

Camera, OCR, translation, and speech timeouts are treated as recoverable
workflow failures. Unexpected component failures are converted to safe guidance
without exposing captured text, translated text, command transcripts, images,
or snippets in default logs.

## Phase 9 Operational Shutdown

Use process interruption, service stop, or the test-harness shutdown entrypoint
for operational shutdown. Voice stop is intentionally only a playback control.
Shutdown stops active speech when possible, runs cleanup hooks, clears volatile
text state, and blocks new workflow work.

## Phase 11 Deployment Diagnostics

Run `python scripts/pi_deployment_check.py --full --skip-hardware` on a
development machine, or remove `--skip-hardware` on the Raspberry Pi after
camera, speaker, and microphone are connected. Reports are local privacy-safe
summaries only.

Lightweight startup checks report one of four non-visual states:

- Ready: startup checks passed.
- Degraded: the assistant can continue with reduced capability, such as no
  internet while local fallback is available.
- Blocked: a required dependency or folder must be fixed before normal use.
- Manual Verification Needed: automated checks cannot prove the condition.

If internet is unavailable at startup, the assistant reports degraded offline
mode instead of failing when local reading fallback is available. Reconnect the
network to restore online-first services.

Full diagnostics add camera, speaker, microphone, and local OCR fallback checks.
Depth-capable camera readiness is Ready when RGB and depth can be verified.
RGB-only camera operation is Degraded, not failed, when capture can still
continue. Speaker and microphone checks may return Manual Verification Needed
because audibility and command quality must be confirmed on the real device.
Preferred offline OCR is checked without eager startup model loading; emergency
Tesseract readiness verifies executable and Arabic/English language data.

For intermittent networks, deployment diagnostics distinguish three cases:
no-internet startup, temporary outage during use, and restored connectivity.
No-internet startup is Degraded when local OCR and speech fallback can continue.
Temporary outage should trigger a spoken local-fallback explanation. Restored
connectivity is checked for later workflows so online-first services can return
without restarting the assistant.

Manual startup uses `scripts/run_assistant.sh`, which installs signal traps and
forwards stop requests to `main.py`. The optional systemd template in
`deploy/blind-ocr-assistant.service.template` is disabled by default; copy and
enable it only after full diagnostics and privacy checks are accepted. Use
normal systemd `status`, `stop`, and `disable` commands when service mode is
intentionally enabled. Normal logs are checked against a 50 MB budget and old
normal log files should be pruned before debug captures or private artifacts are
touched.

### Manual Raspberry Pi Hardware Acceptance

Before handing the device to a user, run these checks on the target Raspberry Pi:

- Start with `scripts/run_assistant.sh` and confirm spoken startup readiness.
- Run `python scripts/pi_deployment_check.py --full` with camera, speaker, and
  microphone connected.
- Confirm RGB capture and depth status, accepting RGB-only as Degraded when
  reading can continue.
- Confirm speaker output is audible and microphone commands are recognized.
- Disconnect internet and confirm Degraded offline startup with local fallback.
- Restore internet and confirm later diagnostics can detect restored
  connectivity.
- Stop and restart the assistant repeatedly and confirm camera/audio resources
  are released.
- Confirm normal logs remain under the 50 MB default budget.
- Review reports and logs for privacy-safe summaries only.
## Phase 10 Benchmarking

Dataset issues:

- If `benchmark dataset manifest missing` appears, pass an explicit local
  `--dataset` path such as `tests/benchmark/manifest.json`.
- If coverage validation fails, confirm the manifest includes at least 12 safe
  samples and labels for Arabic, English, mixed text, book page, printed
  document, medicine package, receipt, sign, low light, angled image, far image,
  and blurry image.
- If expected-text validation fails, add safe expected text for every
  normal-quality Arabic, English, and mixed sample and at least half of
  difficult samples.

Engine availability:

- `online_unavailable` means the online path was requested but no live adapter
  was provided or configured for that benchmark run.
- `online_disabled` is expected when `--offline` is used with an online path.
- `engine_unavailable` means a local path such as PaddleOCR, Tesseract, or the
  cascade was requested without an injected/live adapter.

Result retention:

- Benchmark runs write timestamped directories under `benchmark_results/`.
- Existing result directories are not overwritten. Remove old local output
  directories manually only when they are no longer needed.

Optional live dependencies:

- Automated tests use mocked OCR boundaries and safe fixtures.
- Live OCR.space, PaddleOCR, and Tesseract checks remain optional maintainer
  workflows and should not be required for normal unit validation.

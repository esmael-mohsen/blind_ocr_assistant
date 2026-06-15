"""Phase 0 bootstrap entrypoint for Blind OCR Assistant."""

from __future__ import annotations

import argparse
from dataclasses import replace
import importlib
import os
from pathlib import Path
import signal
import tempfile
from types import FrameType

from config import load_config
from modules.assistant.runtime import AssistantRuntime, AssistantRuntimeOptions
from modules.common.bootstrap import run_self_check
from modules.deployment.diagnostics import (
    format_report_for_cli,
    run_lightweight_startup_diagnostics,
)
from modules.deployment.readiness_checks import offline_recovery_spoken_summary
from modules.deployment.readiness_models import ReadinessStatus


def build_workflow():
    """Create the Phase 9 workflow without starting hardware at import time."""
    from modules.assistant.workflow import AssistantWorkflow

    return AssistantWorkflow()


def install_signal_handlers(workflow) -> None:
    """Install operational shutdown handlers for an assistant workflow."""

    def _handle_shutdown(signum: int, frame: FrameType | None) -> None:
        workflow.shutdown()

    signal.signal(signal.SIGINT, _handle_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_shutdown)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser without loading future engine modules."""
    parser = argparse.ArgumentParser(
        prog="blind-ocr-assistant",
        description=(
            "Integrated Blind OCR Assistant runtime. Run without flags to start "
            "the always-on camera, voice, OCR, TTS, and translation system."
        ),
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="verify Phase 0 repository readiness without hardware or services",
    )
    parser.add_argument(
        "--once",
        metavar="COMMAND",
        help=(
            "handle one assistant command through the Phase 9 workflow wiring "
            "without starting a continuous microphone loop"
        ),
    )
    parser.add_argument(
        "--live-read",
        action="store_true",
        help=(
            "run one laptop-camera capture through frame selection, OCR, text "
            "cleanup, and optional speech"
        ),
    )
    parser.add_argument(
        "--full-workflow",
        action="store_true",
        help=(
            "run one command through the fully wired assistant workflow: command "
            "parser, dialogue manager, state, camera, OCR, cleanup, TTS, and "
            "optional translation"
        ),
    )
    parser.add_argument(
        "--assistant-loop",
        action="store_true",
        help=(
            "run the assistant as one continuous system with shared state, "
            "persistent camera, command loop, OCR, TTS, and translation"
        ),
    )
    parser.add_argument(
        "--voice-input",
        action="store_true",
        help="use the microphone and local Vosk for --assistant-loop commands",
    )
    parser.add_argument(
        "--list-microphones",
        action="store_true",
        help="print available microphone device indexes for voice configuration",
    )
    parser.add_argument(
        "--voice-model",
        help="Vosk model path for --assistant-loop --voice-input",
    )
    parser.add_argument(
        "--command-timeout",
        type=float,
        default=8.0,
        help="seconds to listen for each voice command in --assistant-loop",
    )
    parser.add_argument(
        "--tts-engine",
        choices=("auto", "windows", "espeak", "mock"),
        default="auto",
        help="TTS engine used by --assistant-loop and --full-workflow",
    )
    parser.add_argument(
        "--workflow-command",
        default="read text",
        help="command transcript used by --full-workflow (default: read text)",
    )
    parser.add_argument(
        "--translate-to",
        choices=("ar", "en"),
        help="after a successful --full-workflow read, translate latest text",
    )
    parser.add_argument(
        "--trace-workflow",
        action="store_true",
        help="print detailed safe step-by-step workflow progress",
    )
    parser.add_argument(
        "--no-speak",
        action="store_true",
        help="use an in-memory TTS engine for --full-workflow without audio output",
    )
    parser.add_argument(
        "--allow-uncertain-frame",
        action="store_true",
        help=(
            "for --full-workflow testing, continue OCR with the best captured "
            "frame when image quality is acceptable but text presence is uncertain"
        ),
    )
    parser.add_argument(
        "--force-best-frame",
        action="store_true",
        help=(
            "for --full-workflow testing only, continue OCR with the best captured "
            "frame even when the image-quality gate rejects it"
        ),
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="OpenCV camera index used by --live-read (default: 0)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="force --live-read to use local OCR fallback only",
    )
    parser.add_argument(
        "--high-accuracy",
        action="store_true",
        help="ask --live-read to compare available OCR routes when possible",
    )
    parser.add_argument(
        "--show-text",
        action="store_true",
        help="print recognized clean text for manual testing",
    )
    parser.add_argument(
        "--speak",
        action="store_true",
        help="read recognized clean text aloud using the local TTS engine",
    )
    parser.add_argument(
        "--skip-startup-checks",
        action="store_true",
        help="skip Phase 11 lightweight deployment readiness checks",
    )
    return parser


def run_startup_checks() -> int:
    """Run non-visual lightweight deployment startup checks."""
    report = run_lightweight_startup_diagnostics(local_fallback_available=True)
    print(format_report_for_cli(report))
    print(offline_recovery_spoken_summary(report.overall_status))
    if report.overall_status is ReadinessStatus.BLOCKED:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the Phase 0 CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_check:
        result = run_self_check()
        if not result.success:
            print(f"FAIL {result.error_code}: {result.message}")
            return 1
        report = result.value
        print("Phase 0 self-check: PASS")
        if report is not None:
            for message in report.messages:
                print(f"- {message}")
            for tool in report.quality_tools:
                status = "installed" if tool.installed else "not installed"
                print(f"- optional {tool.name}: {status}")
        return 0
    if args.list_microphones:
        return list_microphones()
    if _should_run_integrated_runtime(args):
        config = load_config()
        options = replace(
            AssistantRuntimeOptions.from_config(config),
            startup_checks_enabled=not args.skip_startup_checks,
        )
        return AssistantRuntime(config=config, options=options).run()
    if not args.skip_startup_checks:
        startup_code = run_startup_checks()
        if startup_code != 0:
            return startup_code
    if args.assistant_loop:
        return run_assistant_loop(
            camera_index=args.camera_index,
            offline=args.offline,
            high_accuracy=args.high_accuracy,
            show_text=args.show_text,
            trace=args.trace_workflow,
            speak=not args.no_speak,
            force_best_frame=args.force_best_frame,
            voice_input=args.voice_input,
            voice_model=args.voice_model,
            command_timeout=args.command_timeout,
            tts_engine=args.tts_engine,
        )
    if args.full_workflow:
        return run_full_workflow(
            command=args.workflow_command,
            camera_index=args.camera_index,
            offline=args.offline,
            high_accuracy=args.high_accuracy,
            show_text=args.show_text,
            translate_to=args.translate_to,
            trace=args.trace_workflow,
            speak=not args.no_speak,
            allow_uncertain_frame=args.allow_uncertain_frame,
            force_best_frame=args.force_best_frame,
            tts_engine=args.tts_engine,
        )
    if args.live_read:
        return run_live_read(
            camera_index=args.camera_index,
            offline=args.offline,
            high_accuracy=args.high_accuracy,
            show_text=args.show_text,
            speak=args.speak,
        )
    if args.once:
        workflow = build_workflow()
        result = workflow.handle_command(args.once)
        print(result.guidance)
        return 0 if result.success else 1
    return 0


def _should_run_integrated_runtime(args: argparse.Namespace) -> bool:
    """Return whether no explicit developer/debug mode was requested."""
    return not any(
        (
            args.assistant_loop,
            args.full_workflow,
            args.live_read,
            args.list_microphones,
            bool(args.once),
        )
    )


def list_microphones() -> int:
    """Print microphone indexes usable by ASSISTANT_MICROPHONE_INDEX."""
    printed = False
    try:
        import speech_recognition as sr

        print("SpeechRecognition microphones:")
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"- {index}: {name}")
        printed = True
    except Exception as exc:
        print(f"SpeechRecognition microphone list failed: {type(exc).__name__}: {exc}")

    try:
        import sounddevice as sd

        print("sounddevice devices:")
        print(sd.query_devices())
        print(f"sounddevice default: {sd.default.device}")
        printed = True
    except Exception as exc:
        print(f"sounddevice device list failed: {type(exc).__name__}: {exc}")

    print("Set ASSISTANT_MICROPHONE_INDEX in .env to the input device index you use.")
    return 0 if printed else 1


def run_full_workflow(
    *,
    command: str,
    camera_index: int,
    offline: bool,
    high_accuracy: bool,
    show_text: bool,
    translate_to: str | None,
    trace: bool,
    speak: bool,
    allow_uncertain_frame: bool,
    force_best_frame: bool,
    tts_engine: str,
) -> int:
    """Run one fully wired command-driven assistant workflow."""
    modules = _load_full_workflow_modules()
    config = load_config()
    trace_step = _trace_printer(enabled=trace)

    trace_step("User Voice", "using provided command transcript")
    trace_step("STT / Command Input", command)

    reading_controller = modules["reading"].ReadingController(
        _build_tts_engine(modules=modules, speak=speak, tts_engine=tts_engine)
    )
    translation_controller = modules["translation_controller"].TranslationController(
        online_engine=_build_online_translation_engine(modules=modules, config=config),
        offline_engine=modules["translation_argos"].ArgosTranslateFallback(),
        reading_controller=reading_controller,
    )
    dialogue_manager = modules["dialogue"].DialogueManager(
        reading_controller=reading_controller,
        translation_controller=translation_controller,
        route_immediately=False,
    )

    workflow = modules["workflow"].AssistantWorkflow(
        dialogue_manager=dialogue_manager,
        capture_burst=_capture_boundary(
            modules=modules,
            config=config,
            camera_index=camera_index,
            trace_step=trace_step,
            allow_uncertain_frame=allow_uncertain_frame,
            force_best_frame=force_best_frame,
        ),
        run_ocr_cascade=_ocr_boundary(
            modules=modules,
            config=config,
            offline=offline,
            high_accuracy=high_accuracy,
            trace_step=trace_step,
        ),
        clean_ocr_text=_cleanup_boundary(modules=modules, trace_step=trace_step),
        reading_controller=reading_controller,
        translation_controller=translation_controller,
        online_status_provider=lambda: _online_ocr_allowed(config, offline=offline),
    )
    install_signal_handlers(workflow)

    trace_step("Command Parser", "parsing supported fixed command")
    trace_step("Dialogue Manager", "routing command to assistant workflow")
    result = workflow.handle_command(command, high_accuracy=high_accuracy)
    _print_read_workflow_result(result, show_text=show_text)
    if not getattr(result, "success", False):
        return 1

    state = workflow.get_state()
    trace_step(
        "Assistant State",
        f"last_clean_text={bool(state.last_clean_text)} language={state.last_language}",
    )
    trace_step("Back to Listening", "read workflow completed")

    if translate_to:
        translate_command = (
            "translate to arabic" if translate_to == "ar" else "translate to english"
        )
        trace_step("Translation Command", translate_command)
        translation = workflow.handle_command(translate_command)
        _print_translation_workflow_result(translation, show_text=show_text)
        if not getattr(translation, "success", False):
            return 1
        trace_step("Back to Listening", "translation workflow completed")

    return 0


def run_assistant_loop(
    *,
    camera_index: int,
    offline: bool,
    high_accuracy: bool,
    show_text: bool,
    trace: bool,
    speak: bool,
    force_best_frame: bool,
    voice_input: bool,
    voice_model: str | None,
    command_timeout: float,
    tts_engine: str,
) -> int:
    """Run a continuous command-driven assistant session."""
    modules = _load_full_workflow_modules()
    config = load_config()
    trace_step = _trace_printer(enabled=trace)
    camera_source = _persistent_camera_source(
        modules["camera"],
        camera_index=camera_index,
    )
    reading_controller = modules["reading"].ReadingController(
        _build_tts_engine(modules=modules, speak=speak, tts_engine=tts_engine)
    )
    translation_controller = modules["translation_controller"].TranslationController(
        online_engine=_build_online_translation_engine(modules=modules, config=config),
        offline_engine=modules["translation_argos"].ArgosTranslateFallback(),
        reading_controller=reading_controller,
    )
    workflow = modules["workflow"].AssistantWorkflow(
        dialogue_manager=modules["dialogue"].DialogueManager(route_immediately=False),
        capture_burst=_capture_boundary(
            modules=modules,
            config=config,
            camera_index=camera_index,
            trace_step=trace_step,
            allow_uncertain_frame=True,
            force_best_frame=force_best_frame,
            camera_source=camera_source,
        ),
        run_ocr_cascade=_ocr_boundary(
            modules=modules,
            config=config,
            offline=offline,
            high_accuracy=high_accuracy,
            trace_step=trace_step,
        ),
        clean_ocr_text=_cleanup_boundary(modules=modules, trace_step=trace_step),
        reading_controller=reading_controller,
        translation_controller=translation_controller,
        online_status_provider=lambda: _online_ocr_allowed(config, offline=offline),
        cleanup_hooks=(camera_source.close,),
    )
    install_signal_handlers(workflow)

    print("Assistant loop started.")
    print(
        "Commands: start, read text, translate to arabic, translate to english, stop, continue, repeat sentence, repeat paragraph, help, exit"
    )
    welcome_text = (
        "Welcome. The assistant is ready. Say start to read text, "
        "or say help for commands."
    )
    print(welcome_text)
    if speak:
        welcome = _speak_guidance(
            modules=modules,
            engine=reading_controller.engine,
            text=welcome_text,
        )
        if not welcome.success:
            print(f"Audio warning: {welcome.guidance}")
    try:
        if voice_input:
            return _run_voice_command_loop(
                workflow=workflow,
                modules=modules,
                voice_model=voice_model,
                command_timeout=command_timeout,
                high_accuracy=high_accuracy,
                show_text=show_text,
            )
        return _run_text_command_loop(
            workflow=workflow,
            high_accuracy=high_accuracy,
            show_text=show_text,
        )
    finally:
        workflow.shutdown()


def run_live_read(
    *,
    camera_index: int,
    offline: bool,
    high_accuracy: bool,
    show_text: bool,
    speak: bool,
) -> int:
    """Run one end-to-end live read from the laptop camera."""
    reading_module = importlib.import_module("modules.assistant.reading_controller")
    camera_models = importlib.import_module("modules.camera.camera_models")
    camera_module = importlib.import_module("modules.camera.orbbec_camera")
    cascade_module = importlib.import_module("modules.ocr.ocr_cascade")
    gemini_module = importlib.import_module("modules.ocr.gemini_ocr_engine")
    ocr_space_module = importlib.import_module("modules.ocr.ocr_space_client")
    paddle_module = importlib.import_module("modules.ocr.paddle_ocr_engine")
    tesseract_module = importlib.import_module("modules.ocr.tesseract_engine")
    cleanup_module = importlib.import_module("modules.text.cleanup")
    tts_module = importlib.import_module("modules.voice.tts_engine")

    config = load_config()
    print(f"Opening laptop camera index {camera_index}...")
    capture_result = camera_module.capture_burst_from_sources(
        [
            camera_module.GenericRGBCameraSource(
                camera_index=camera_index,
                source_id=f"opencv-rgb-{camera_index}",
            )
        ],
        camera_models.CaptureRequest(
            requested_count=config.camera_frame_capture_count,
            timeout_seconds=config.camera_capture_timeout_seconds,
            prefer_depth=False,
            allow_rgb_fallback=True,
            debug_save_enabled=config.debug_save_images,
        ),
    )
    if (
        not capture_result.success
        or capture_result.selection_result is None
        or not capture_result.selection_result.success
        or capture_result.selection_result.selected_frame is None
    ):
        message = capture_result.message or "Camera capture failed."
        if capture_result.error is not None:
            message = capture_result.error.message
        print(f"Camera failed: {message}")
        return 1

    selected_frame = capture_result.selection_result.selected_frame
    image_path = _write_temp_capture(selected_frame.rgb_image)
    try:
        gemini_allowed = _gemini_ocr_allowed(config, offline=offline)
        ocr_space_allowed = bool(config.ocr_space_api_key) and not offline
        online_allowed = gemini_allowed or ocr_space_allowed
        preferred_online_engine = "gemini" if gemini_allowed else "online"
        engines = {
            "local": paddle_module.PaddleOCREngine(),
            "emergency": tesseract_module.TesseractEngine(),
        }
        if gemini_allowed:
            engines["gemini"] = gemini_module.GeminiOCREngine(
                api_key=config.gemini_api_key,
                model=config.assistant_gemini_ocr_model,
                timeout_seconds=config.assistant_gemini_ocr_timeout_seconds,
            )
        elif ocr_space_allowed:
            engines["online"] = ocr_space_module.OCRSpaceClient(
                api_key=config.ocr_space_api_key
            )

        print("Running OCR cascade...")
        cascade = cascade_module.run_ocr_cascade(
            cascade_module.OCRCascadeRequest(
                image=str(image_path),
                language_hints=("ar", "en"),
                allow_online=online_allowed,
                allow_offline=config.assistant_gemini_ocr_fallback_local
                or not online_allowed,
                high_accuracy=high_accuracy,
                quality_threshold=config.ocr_quality_threshold,
                max_attempts_per_engine=config.ocr_max_attempts_per_engine,
                sensitive_text_logging_enabled=config.sensitive_text_logging,
            ),
            engines,
            online_status_provider=lambda: online_allowed,
            preferred_online_engine=preferred_online_engine,
        )
    finally:
        image_path.unlink(missing_ok=True)

    if not cascade.success or cascade.selected_result is None:
        print(f"OCR failed: {cascade.guidance}")
        for attempt in cascade.attempts:
            code = (
                attempt.error_code.value if attempt.error_code is not None else "none"
            )
            print(f"- {attempt.engine_name}: {attempt.status.value} ({code})")
        return 1

    cleanup = cleanup_module.clean_ocr_text(
        cleanup_module.TextCleanupRequest(
            raw_text=cascade.selected_result.raw_text,
            language_hints=("ar", "en"),
            source_engine=cascade.selected_engine,
            sensitive_text_logging_enabled=config.sensitive_text_logging,
        )
    )
    if not cleanup.clean_text.strip():
        print("No readable text was found after cleanup.")
        return 1

    print(
        "Live read succeeded: "
        f"engine={cascade.selected_engine}, "
        f"language={cleanup.language.value}, "
        f"chars={len(cleanup.clean_text)}"
    )
    if show_text:
        print("\nRecognized text:")
        print(cleanup.clean_text)

    if not speak:
        print("Speech skipped. Add --speak to test local TTS.")
        return 0

    speech = reading_module.ReadingController(
        tts_module.EspeakNGEngine()
    ).start_reading(
        cleanup.clean_text,
        language=cleanup.language.value,
    )
    if not speech.success:
        error_code = speech.error.code.value if speech.error is not None else "unknown"
        print(f"TTS failed: {speech.guidance} ({error_code})")
        return 1
    print("Speech started.")
    return 0


def _run_text_command_loop(*, workflow, high_accuracy: bool, show_text: bool) -> int:
    while True:
        try:
            command = input("assistant> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAssistant stopped.")
            return 0
        if not command:
            continue
        if _is_exit_command(command):
            print("Assistant stopped.")
            return 0
        result = workflow.handle_command(command, high_accuracy=high_accuracy)
        _print_loop_result(result, show_text=show_text)
        print("Back to listening.")


def _run_voice_command_loop(
    *,
    workflow,
    modules,
    voice_model: str | None,
    command_timeout: float,
    high_accuracy: bool,
    show_text: bool,
) -> int:
    model_path = _resolve_vosk_model_path(voice_model)
    listener = modules["live_vosk"].LiveVoskCommandListener(
        model_path=model_path,
        phrase_timeout_seconds=command_timeout,
    )
    try:
        with listener:
            while True:
                print("Listening...")
                command = listener.listen_once().strip()
                if not command:
                    print("No command heard.")
                    continue
                print(f"Heard command: {command}")
                if _is_exit_command(command):
                    print("Assistant stopped.")
                    return 0
                result = workflow.handle_command(command, high_accuracy=high_accuracy)
                _print_loop_result(result, show_text=show_text)
                print("Back to listening.")
    except KeyboardInterrupt:
        print("\nAssistant stopped.")
        return 0
    except Exception as exc:
        print(f"Voice input failed: {type(exc).__name__}: {exc}")
        return 1


def _is_exit_command(command: str) -> bool:
    return command.strip().lower() in {"exit", "quit", "shutdown", "stop assistant"}


def _load_full_workflow_modules() -> dict[str, object]:
    return {
        "camera_models": importlib.import_module("modules.camera.camera_models"),
        "camera": importlib.import_module("modules.camera.orbbec_camera"),
        "cleanup": importlib.import_module("modules.text.cleanup"),
        "dialogue": importlib.import_module("modules.assistant.dialogue_manager"),
        "image_models": importlib.import_module(
            "modules.image_processing.image_models"
        ),
        "preprocessing": importlib.import_module(
            "modules.image_processing.preprocessing"
        ),
        "ocr_cascade": importlib.import_module("modules.ocr.ocr_cascade"),
        "gemini_ocr": importlib.import_module("modules.ocr.gemini_ocr_engine"),
        "ocr_space": importlib.import_module("modules.ocr.ocr_space_client"),
        "paddle": importlib.import_module("modules.ocr.paddle_ocr_engine"),
        "reading": importlib.import_module("modules.assistant.reading_controller"),
        "tesseract": importlib.import_module("modules.ocr.tesseract_engine"),
        "translation_argos": importlib.import_module(
            "modules.translation.argos_fallback"
        ),
        "translation_controller": importlib.import_module(
            "modules.assistant.translation_controller"
        ),
        "gemini_translation": importlib.import_module(
            "modules.translation.gemini_translation_engine"
        ),
        "translation_online": importlib.import_module(
            "modules.translation.online_translation_stack"
        ),
        "tts": importlib.import_module("modules.voice.tts_engine"),
        "voice_models": importlib.import_module("modules.voice.voice_models"),
        "live_vosk": importlib.import_module("modules.voice.live_vosk_listener"),
        "workflow": importlib.import_module("modules.assistant.workflow"),
    }


def _build_tts_engine(*, modules, speak: bool, tts_engine: str):
    if not speak or tts_engine == "mock":
        return modules["tts"].MockTTSEngine(name="no_audio_tts")
    if tts_engine == "windows" or (tts_engine == "auto" and os.name == "nt"):
        return modules["tts"].WindowsSapiEngine()
    return modules["tts"].EspeakNGEngine()


def _build_online_translation_engine(*, modules, config):
    online_translation = modules["translation_online"].OnlineFallbackTranslationEngine(
        primary=modules["translation_online"].GoogleTranslatorEngine(),
        backup=modules["translation_online"].MyMemoryTranslatorEngine(),
    )
    if (
        config.assistant_gemini_translation_enabled
        and config.gemini_api_key
    ):
        online_translation = modules["translation_online"].OnlineFallbackTranslationEngine(
            primary=modules["gemini_translation"].GeminiTranslationEngine(
                api_key=config.gemini_api_key,
                model=config.assistant_gemini_translation_model,
                timeout_seconds=config.assistant_gemini_translation_timeout_seconds,
            ),
            backup=online_translation,
        )
    return online_translation


def _speak_guidance(*, modules, engine, text: str):
    return engine.speak(
        modules["voice_models"].SpeechRequest(
            text=text,
            language="en",
            operation=modules["voice_models"].SpeechOperation.GUIDANCE,
        )
    )


def _persistent_camera_source(camera_module, *, camera_index: int):
    class PersistentRGBCameraSource(camera_module.GenericRGBCameraSource):
        def open(self) -> bool:
            capture = getattr(self, "_capture", None)
            if capture is not None and capture.isOpened():
                return True
            return super().open()

        def release(self) -> None:
            return None

        def close(self) -> None:
            super().release()

    return PersistentRGBCameraSource(
        camera_index=camera_index,
        source_id=f"persistent-opencv-rgb-{camera_index}",
    )


def _resolve_vosk_model_path(voice_model: str | None) -> str:
    if voice_model:
        return voice_model
    return (
        os.getenv("VOSK_MODEL_EN")
        or os.getenv("VOSK_MODEL")
        or str(Path("models") / "vosk" / "vosk-model-small-en-us-0.15")
    )


def _gemini_ocr_allowed(config, *, offline: bool) -> bool:
    return bool(
        config.assistant_gemini_ocr_enabled
        and config.gemini_api_key
        and not offline
    )


def _online_ocr_allowed(config, *, offline: bool) -> bool:
    return _gemini_ocr_allowed(config, offline=offline) or bool(
        config.ocr_space_api_key and not offline
    )


def _capture_boundary(
    *,
    modules,
    config,
    camera_index: int,
    trace_step,
    allow_uncertain_frame: bool,
    force_best_frame: bool,
    camera_source=None,
):
    def _capture():
        trace_step("Camera Open", f"OpenCV camera index {camera_index}")
        source = camera_source or modules["camera"].GenericRGBCameraSource(
            camera_index=camera_index,
            source_id=f"opencv-rgb-{camera_index}",
        )
        result = modules["camera"].capture_burst_from_sources(
            [source],
            modules["camera_models"].CaptureRequest(
                requested_count=config.camera_frame_capture_count,
                timeout_seconds=config.camera_capture_timeout_seconds,
                prefer_depth=False,
                allow_rgb_fallback=True,
                debug_save_enabled=config.debug_save_images,
            ),
        )
        trace_step(
            "Capture Frames",
            f"success={result.success} candidates={len(getattr(result, 'candidates', []))}",
        )
        selection = getattr(result, "selection_result", None)
        if force_best_frame:
            result, selection = _continue_with_best_frame(
                modules=modules,
                capture_result=result,
                selection=selection,
                trace_step=trace_step,
            )
        elif allow_uncertain_frame:
            result, selection = _continue_with_uncertain_frame(
                modules=modules,
                capture_result=result,
                selection=selection,
                trace_step=trace_step,
            )
        selected = getattr(selection, "selected_frame", None) if selection else None
        quality = getattr(selected, "quality_report", None) if selected else None
        if quality is None:
            quality = _best_quality_report_from_candidates(
                getattr(result, "candidates", [])
            )
        if quality is not None:
            trace_step(
                "Image Quality Check",
                (
                    f"acceptable={quality.is_acceptable} "
                    f"score={quality.quality_score:.2f} "
                    f"brightness={quality.brightness_status.value} "
                    f"blur={quality.blur_status.value} "
                    f"contrast={quality.contrast_status.value} "
                    f"text={quality.text_presence_status.value}"
                ),
            )
            if not quality.is_acceptable:
                trace_step("Voice Guidance if Bad", quality.guidance.english_text)
        if selection is not None and not selection.success:
            trace_step("Frame Rejection", selection.guidance)
            _trace_candidate_reports(getattr(result, "candidates", []), trace_step)
        trace_step(
            "Best Frame Selection",
            f"success={bool(selection and selection.success)}",
        )
        return result

    return _capture


def _continue_with_best_frame(*, modules, capture_result, selection, trace_step):
    if selection is not None and selection.success:
        return capture_result, selection
    candidates = list(getattr(capture_result, "candidates", []) or [])
    if not candidates:
        return capture_result, selection
    candidate = _highest_quality_candidate(candidates)
    report = getattr(candidate, "quality_report", None)
    detail = ""
    if report is not None:
        detail = (
            f" score={report.quality_score:.2f}"
            f" text={report.text_presence_status.value}"
            f" blur={report.blur_status.value}"
        )
    trace_step(
        "Frame Override",
        f"forcing best captured frame for manual end-to-end testing{detail}",
    )
    override_selection = _build_override_selection(
        modules=modules,
        capture_result=capture_result,
        selection=selection,
        candidates=candidates,
        candidate=candidate,
        guidance="Forcing the best captured frame for testing.",
    )
    return (
        replace(capture_result, selection_result=override_selection),
        override_selection,
    )


def _continue_with_uncertain_frame(*, modules, capture_result, selection, trace_step):
    if selection is not None and selection.success:
        return capture_result, selection
    candidates = list(getattr(capture_result, "candidates", []) or [])
    if not candidates:
        return capture_result, selection
    candidate = _highest_quality_candidate(candidates)
    report = getattr(candidate, "quality_report", None)
    if report is None:
        return capture_result, selection
    if not (
        report.brightness_status.value == "acceptable"
        and report.blur_status.value == "acceptable"
        and report.contrast_status.value == "acceptable"
        and report.text_presence_status.value in {"uncertain_text", "unlikely_text"}
    ):
        return capture_result, selection

    trace_step(
        "Frame Override",
        (
            "continuing with best frame despite "
            f"text={report.text_presence_status.value} for manual end-to-end testing"
        ),
    )
    override_selection = _build_override_selection(
        modules=modules,
        capture_result=capture_result,
        selection=selection,
        candidates=candidates,
        candidate=candidate,
        guidance="Continuing with the clearest frame for testing.",
    )
    return (
        replace(capture_result, selection_result=override_selection),
        override_selection,
    )


def _highest_quality_candidate(candidates):
    return max(
        candidates,
        key=lambda item: float(
            getattr(getattr(item, "quality_report", None), "quality_score", 0.0)
        ),
    )


def _build_override_selection(
    *,
    modules,
    capture_result,
    selection,
    candidates,
    candidate,
    guidance: str,
):
    camera_models = modules["camera_models"]
    return camera_models.BestFrameSelectionResult(
        success=True,
        selected_frame=candidate,
        candidate_summaries=getattr(selection, "candidate_summaries", [])
        or [item.safe_summary() for item in candidates],
        guidance=guidance,
        source_type=capture_result.source_type,
        partial_timeout=capture_result.partial_timeout,
        cleanup_status=capture_result.cleanup_status,
    )


def _ocr_boundary(*, modules, config, offline: bool, high_accuracy: bool, trace_step):
    def _run(image):
        trace_step("Preprocessing Variants", "creating OCR-specific image variants")
        variants = modules["preprocessing"].create_preprocessing_variants(
            modules["image_models"].ImageInput(
                image_array=image,
                source_id="workflow-selected-frame",
            )
        )
        variant = variants.variants[
            modules["image_models"].PreprocessingVariantName.LOCAL_NATURAL
        ]
        image_path = _write_temp_capture(variant.image)
        try:
            gemini_allowed = _gemini_ocr_allowed(config, offline=offline)
            ocr_space_allowed = bool(config.ocr_space_api_key) and not offline
            online_allowed = gemini_allowed or ocr_space_allowed
            preferred_online_engine = "gemini" if gemini_allowed else "online"
            engines = {
                "local": modules["paddle"].PaddleOCREngine(),
                "emergency": modules["tesseract"].TesseractEngine(),
            }
            if gemini_allowed:
                engines["gemini"] = modules["gemini_ocr"].GeminiOCREngine(
                    api_key=config.gemini_api_key,
                    model=config.assistant_gemini_ocr_model,
                    timeout_seconds=config.assistant_gemini_ocr_timeout_seconds,
                )
            elif ocr_space_allowed:
                engines["online"] = modules["ocr_space"].OCRSpaceClient(
                    api_key=config.ocr_space_api_key
                )
            trace_step(
                "OCR Cascade",
                f"online={online_allowed} offline=True high_accuracy={high_accuracy}",
            )
            result = modules["ocr_cascade"].run_ocr_cascade(
                modules["ocr_cascade"].OCRCascadeRequest(
                    image=str(image_path),
                    language_hints=("ar", "en"),
                    allow_online=online_allowed,
                    allow_offline=config.assistant_gemini_ocr_fallback_local
                    or not online_allowed,
                    high_accuracy=high_accuracy,
                    quality_threshold=config.ocr_quality_threshold,
                    max_attempts_per_engine=config.ocr_max_attempts_per_engine,
                    sensitive_text_logging_enabled=config.sensitive_text_logging,
                ),
                engines,
                online_status_provider=lambda: online_allowed,
                preferred_online_engine=preferred_online_engine,
            )
        finally:
            image_path.unlink(missing_ok=True)
        trace_step(
            "OCR Quality Check",
            f"success={result.success} engine={result.selected_engine}",
        )
        for index, attempt in enumerate(getattr(result, "attempts", []), start=1):
            error_code = (
                attempt.error_code.value if attempt.error_code is not None else "none"
            )
            ocr_result = getattr(attempt, "ocr_result", None)
            error_message = getattr(ocr_result, "error_message", None)
            safe_metadata = getattr(attempt, "safe_metadata", {}) or {}
            http_status = safe_metadata.get("status_code")
            model = safe_metadata.get("model")
            provider_error_status = safe_metadata.get("provider_error_status")
            quality = getattr(attempt, "quality_report", None)
            quality_detail = (
                f" quality={quality.quality_score:.2f}"
                f" acceptable={quality.is_acceptable}"
                if quality is not None
                else ""
            )
            provider_detail = (
                f" http={http_status}" if http_status is not None else ""
            )
            provider_detail += f" provider_status={provider_error_status}" if provider_error_status else ""
            provider_detail += f" model={model}" if model else ""
            message_detail = f" message={error_message}" if error_message else ""
            trace_step(
                f"OCR Attempt {index}",
                (
                    f"engine={attempt.engine_name} "
                    f"status={attempt.status.value} "
                    f"error={error_code}"
                    f"{provider_detail}"
                    f"{quality_detail}"
                    f"{message_detail}"
                ),
            )
        return result

    return _run


def _cleanup_boundary(*, modules, trace_step):
    def _clean(raw_text: str):
        trace_step("Text Cleanup + RTL", f"raw_chars={len(raw_text or '')}")
        result = modules["cleanup"].clean_ocr_text(raw_text)
        trace_step(
            "Language Detection",
            f"language={result.language.value} direction={result.direction.value}",
        )
        trace_step("Save last_clean_text", f"clean_chars={len(result.clean_text)}")
        trace_step("TTS Read Full Text", "handoff through ReadingController")
        return result

    return _clean


def _best_quality_report_from_candidates(candidates):
    reports = [
        getattr(candidate, "quality_report", None)
        for candidate in candidates
        if getattr(candidate, "quality_report", None) is not None
    ]
    if not reports:
        return None
    return max(reports, key=lambda report: float(getattr(report, "quality_score", 0.0)))


def _trace_candidate_reports(candidates, trace_step) -> None:
    ranked = sorted(
        [
            getattr(candidate, "quality_report", None)
            for candidate in candidates
            if getattr(candidate, "quality_report", None) is not None
        ],
        key=lambda report: float(getattr(report, "quality_score", 0.0)),
        reverse=True,
    )[:3]
    for index, report in enumerate(ranked, start=1):
        trace_step(
            f"Candidate {index}",
            (
                f"quality={float(report.quality_score):.2f} "
                f"acceptable={report.is_acceptable} "
                f"text={report.text_presence_status.value} "
                f"blur={report.blur_status.value} "
                f"brightness={report.brightness_status.value} "
                f"contrast={report.contrast_status.value}"
            ),
        )


def _trace_printer(*, enabled: bool):
    def _trace(step: str, detail: str) -> None:
        if enabled:
            print(f"[{step}] {detail}")

    return _trace


def _print_read_workflow_result(result, *, show_text: bool) -> None:
    print(
        "Read workflow: "
        f"success={result.success} status={result.status.value} "
        f"engine={result.selected_ocr_engine} language={result.language}"
    )
    print(f"Guidance: {result.guidance}")
    if show_text and getattr(result, "clean_text", ""):
        print("\nClean text:")
        print(result.clean_text)


def _print_translation_workflow_result(result, *, show_text: bool) -> None:
    print(
        "Translation workflow: "
        f"success={result.success} status={result.status.value} "
        f"source={result.source_language} target={result.target_language}"
    )
    print(f"Guidance: {result.guidance}")
    if show_text and getattr(result, "translated_text", ""):
        print("\nTranslated text:")
        print(result.translated_text)


def _print_loop_result(result, *, show_text: bool) -> None:
    if hasattr(result, "capture_success"):
        _print_read_workflow_result(result, show_text=show_text)
        return
    if hasattr(result, "translated_text_available"):
        _print_translation_workflow_result(result, show_text=show_text)
        return
    print(getattr(result, "guidance", str(result)))


def _write_temp_capture(image) -> Path:
    import cv2

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image_path = Path(tmp.name)
    ok = cv2.imwrite(str(image_path), image)
    if not ok:
        image_path.unlink(missing_ok=True)
        raise RuntimeError("OpenCV could not write the captured frame")
    return image_path


if __name__ == "__main__":
    raise SystemExit(main())

"""Tests for online-first runtime voice manager."""

from __future__ import annotations

import time

from modules.voice.command_parser import CommandParser
from modules.voice.command_models import CommandIntent
from modules.voice.voice_runtime_manager import (
    InjectedSTTProvider,
    ListenerResult,
    RuntimeSTTService,
    RuntimeVoiceListener,
    VoiceRuntimeManager,
)


def test_online_voice_command_dispatches_without_local_fallback() -> None:
    dispatched = []
    manager = VoiceRuntimeManager(
        dispatch_command=dispatched.append,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model=None,
        command_timeout_seconds=0.01,
        online_listen_func=lambda: "read text",
        tts_echo_ignore_seconds=0.0,
    )

    manager._handle_command("read text", source="voice")

    assert dispatched == ["read text"]


def test_voice_noise_is_filtered_with_cooldown(capsys) -> None:
    dispatched = []
    manager = VoiceRuntimeManager(
        dispatch_command=dispatched.append,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model=None,
        command_timeout_seconds=0.01,
    )

    manager._handle_command("random noise", source="voice")
    manager._handle_command("random noise", source="voice")

    assert dispatched == []
    assert capsys.readouterr().out.count("Heard audio") == 1


def test_text_command_dispatches_even_when_unknown() -> None:
    dispatched = []
    manager = VoiceRuntimeManager(
        dispatch_command=dispatched.append,
        request_shutdown=lambda: None,
        voice_enabled=False,
        voice_model=None,
        command_timeout_seconds=0.01,
    )

    manager._handle_command("manual unknown", source="text")

    assert dispatched == ["manual unknown"]


def test_voice_manager_switches_online_stt_language(monkeypatch) -> None:
    calls = []

    class Audio:
        pass

    class Source:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    class Recognizer:
        def adjust_for_ambient_noise(self, *_args, **_kwargs):
            return None

        def listen(self, *_args, **_kwargs):
            return Audio()

        def recognize_google(self, _audio, *, language):
            calls.append(language)
            return "اقرا النص"

    monkeypatch.setitem(
        __import__("sys").modules,
        "speech_recognition",
        type("SR", (), {"Recognizer": Recognizer, "Microphone": Source}),
    )
    manager = VoiceRuntimeManager(
        dispatch_command=lambda _command: None,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model=None,
        command_timeout_seconds=0.01,
    )

    manager.set_language("ar")
    assert manager._listen_online_once() == "اقرا النص"
    assert calls == ["ar-EG"]


def test_voice_manager_switches_local_model_when_available(monkeypatch, tmp_path) -> None:
    ar_model = tmp_path / "vosk-ar"
    en_model = tmp_path / "vosk-en"
    ar_model.mkdir()
    en_model.mkdir()
    monkeypatch.setenv("VOSK_MODEL_AR", str(ar_model))
    monkeypatch.setenv("VOSK_MODEL_EN", str(en_model))
    manager = VoiceRuntimeManager(
        dispatch_command=lambda _command: None,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model=str(en_model),
        command_timeout_seconds=0.01,
    )

    manager.set_language("ar")
    assert manager._voice_model == str(ar_model)
    manager.set_language("en")
    assert manager._voice_model == str(en_model)


def test_voice_manager_no_barge_in_pauses_listening_until_tts_finishes() -> None:
    dispatched = []
    manager = VoiceRuntimeManager(
        dispatch_command=dispatched.append,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model=None,
        command_timeout_seconds=0.01,
        online_listen_func=lambda: "read text",
        tts_echo_ignore_seconds=0.0,
    )

    manager.set_tts_busy(True)
    manager.start()
    try:
        time.sleep(0.12)
        assert dispatched == []

        manager.set_tts_busy(False)
        deadline = time.monotonic() + 1.0
        while not dispatched and time.monotonic() < deadline:
            time.sleep(0.01)
    finally:
        manager.stop()

    assert dispatched[:1] == ["read text"]


def test_voice_manager_ignores_result_captured_while_tts_was_busy() -> None:
    dispatched = []
    manager = VoiceRuntimeManager(
        dispatch_command=dispatched.append,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model=None,
        command_timeout_seconds=0.01,
        online_listen_func=lambda: "read text",
    )

    manager.set_tts_busy(True)
    try:
        result = ListenerResult(
            intent=CommandIntent.READ,
            raw_text="read text",
            normalized_text="read text",
            success=True,
            stt_provider="online",
        )

        assert manager._should_ignore_listener_result(result) is True
        manager._execute(result)
    finally:
        manager.set_tts_busy(False)

    assert dispatched == []


def test_voice_manager_ignores_tts_echo_for_longer_cooldown(monkeypatch) -> None:
    now = [100.0]
    monkeypatch.setattr(
        "modules.voice.voice_runtime_manager.time.monotonic",
        lambda: now[0],
    )
    manager = VoiceRuntimeManager(
        dispatch_command=lambda _command: None,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model=None,
        command_timeout_seconds=0.01,
    )
    result = ListenerResult(
        intent=CommandIntent.READ,
        raw_text="translation job started",
        normalized_text="translation job started",
        success=False,
        stt_provider="google_web",
    )

    manager.set_tts_busy(True)
    manager.set_tts_busy(False)
    now[0] = 102.0

    assert manager._should_ignore_listener_result(result) is True


def test_voice_manager_exit_requires_confirmation_by_default(capsys) -> None:
    shutdown_calls = []
    manager = VoiceRuntimeManager(
        dispatch_command=lambda _command: None,
        request_shutdown=lambda: shutdown_calls.append("shutdown"),
        voice_enabled=True,
        voice_model=None,
        command_timeout_seconds=0.01,
    )

    manager._handle_command("exit", source="voice")
    assert shutdown_calls == []
    assert "confirm" in capsys.readouterr().out.lower()

    manager._handle_command("exit", source="voice")
    assert shutdown_calls == ["shutdown"]


def test_listener_uses_non_audio_fallback_provider_after_audio_failure() -> None:
    class FailingAudioInput:
        def listen(self):
            raise RuntimeError("microphone failed")

    listener = RuntimeVoiceListener(
        audio_input=FailingAudioInput(),
        stt_service=RuntimeSTTService(
            [InjectedSTTProvider("local", lambda: "read text")]
        ),
        parser=CommandParser(),
        command_timeout_seconds=0.01,
    )

    result = listener.listen_for_command()

    assert result.success is True
    assert result.intent.value == "read"
    assert result.stt_provider == "local"


def test_auto_listener_uses_direct_vosk_when_online_audio_is_unavailable(
    monkeypatch, tmp_path
) -> None:
    model = tmp_path / "vosk-model"
    model.mkdir()
    events = []
    manager = VoiceRuntimeManager(
        dispatch_command=lambda _command: None,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model=str(model),
        command_timeout_seconds=0.01,
        log_event=lambda event, **fields: events.append((event, fields)),
    )

    class BrokenAudioInput:
        def __init__(self, **_kwargs):
            raise RuntimeError("SpeechRecognition is missing.")

    monkeypatch.setattr(
        "modules.voice.voice_runtime_manager.AudioInput",
        BrokenAudioInput,
    )

    listener = manager._build_listener()

    assert listener.provider_names == ["vosk"]
    assert any(event == "VOICE_ONLINE_STT_UNAVAILABLE" for event, _ in events)

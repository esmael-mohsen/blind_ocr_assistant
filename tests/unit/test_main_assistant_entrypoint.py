"""Tests for the Phase 9 assistant entrypoint wiring."""

from __future__ import annotations

import signal

import pytest

import main


def test_main_help_preserves_import_safe_cli(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main.main(["--help"])

    captured = capsys.readouterr()
    assert excinfo.value.code == 0
    assert "blind-ocr-assistant" in captured.out
    assert "--self-check" in captured.out
    assert "Integrated Blind OCR Assistant runtime" in captured.out


def test_main_without_args_starts_integrated_runtime(monkeypatch):
    calls = []

    class RuntimeStub:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def run(self):
            return 0

    monkeypatch.setattr(main, "AssistantRuntime", RuntimeStub)

    assert main.main([]) == 0
    assert calls
    assert calls[0]["options"].startup_checks_enabled is True


def test_main_skip_startup_checks_applies_to_default_runtime(monkeypatch):
    calls = []

    class RuntimeStub:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def run(self):
            return 0

    monkeypatch.setattr(main, "AssistantRuntime", RuntimeStub)

    assert main.main(["--skip-startup-checks"]) == 0
    assert calls[0]["options"].startup_checks_enabled is False


def test_main_list_microphones_does_not_start_runtime(monkeypatch, capsys):
    monkeypatch.setattr(main, "list_microphones", lambda: print("mic list") or 0)

    assert main.main(["--list-microphones"]) == 0
    assert "mic list" in capsys.readouterr().out


def test_build_workflow_does_not_start_live_hardware():
    workflow = main.build_workflow()

    assert workflow.capture_burst is None
    assert workflow.reading_controller is None


def test_install_signal_handlers_wires_shutdown(monkeypatch):
    registered = {}

    def fake_signal(sig, handler):
        registered[sig] = handler

    monkeypatch.setattr(signal, "signal", fake_signal)
    workflow = main.build_workflow()

    main.install_signal_handlers(workflow)
    registered[signal.SIGINT](signal.SIGINT, None)

    assert signal.SIGINT in registered
    assert workflow.session.shutdown_requested is True

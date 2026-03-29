"""T107 — Integration tests for REPL exit paths (main.py)."""

import sys
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _clean_argv(monkeypatch):
    """Prevent argparse from seeing pytest's CLI args."""
    monkeypatch.setattr(sys, "argv", ["main.py"])


# ── AC-4: exit command ───────────────────────────────────────────────────


@patch("main.load_tools", return_value=([], {}, set(), []))
@patch("main.AnthropicProvider")
@patch("main.register_logging_listener")
@patch("main.register_ui_listener")
@patch("main.ainput")
async def test_exit_command_ends_session(mock_ainput, mock_ui, mock_log,
                                         mock_provider, mock_load,
                                         monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_ainput.side_effect = ["exit"]
    from main import main
    await main()  # should return without error


@patch("main.load_tools", return_value=([], {}, set(), []))
@patch("main.AnthropicProvider")
@patch("main.register_logging_listener")
@patch("main.register_ui_listener")
@patch("main.ainput")
async def test_quit_command_ends_session(mock_ainput, mock_ui, mock_log,
                                         mock_provider, mock_load,
                                         monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_ainput.side_effect = ["quit"]
    from main import main
    await main()


# ── AC-4: Ctrl+C ─────────────────────────────────────────────────────────


@patch("main.load_tools", return_value=([], {}, set(), []))
@patch("main.AnthropicProvider")
@patch("main.register_logging_listener")
@patch("main.register_ui_listener")
@patch("main.ainput")
async def test_ctrl_c_ends_session(mock_ainput, mock_ui, mock_log,
                                    mock_provider, mock_load,
                                    monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_ainput.side_effect = KeyboardInterrupt()
    from main import main
    await main()


# ── AC-4: EOFError ───────────────────────────────────────────────────────


@patch("main.load_tools", return_value=([], {}, set(), []))
@patch("main.AnthropicProvider")
@patch("main.register_logging_listener")
@patch("main.register_ui_listener")
@patch("main.ainput")
async def test_eof_ends_session(mock_ainput, mock_ui, mock_log,
                                 mock_provider, mock_load,
                                 monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_ainput.side_effect = EOFError()
    from main import main
    await main()


# ── Empty input ignored ─────────────────────────────────────────────────


@patch("main.load_tools", return_value=([], {}, set(), []))
@patch("main.AnthropicProvider")
@patch("main.register_logging_listener")
@patch("main.register_ui_listener")
@patch("main.ainput")
async def test_empty_input_ignored(mock_ainput, mock_ui, mock_log,
                                    mock_provider, mock_load,
                                    monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    mock_ainput.side_effect = ["", "  ", "exit"]
    from main import main
    await main()
    # If agent.run was called, it would fail since provider is a mock.
    # The fact that main() completed proves empty inputs were skipped.
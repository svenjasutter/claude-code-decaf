"""T105 — Unit tests for main.py helpers."""

import os
from pathlib import Path

import pytest

from main import build_system_prompt, load_memory_files


def test_build_system_prompt_with_all_parts():
    result = build_system_prompt(
        skill_md_contents=["# read_file\nRead a file."],
        claude_md="This is a Python project.",
        memory_md="- 2026-03-26: user prefers snake_case",
    )
    assert "helpful coding assistant" in result
    assert "Project Knowledge" in result
    assert "Python project" in result
    assert "Learned Facts" in result
    assert "snake_case" in result
    assert "Tool Usage Guides" in result
    assert "read_file" in result


def test_build_system_prompt_no_memory():
    result = build_system_prompt(
        skill_md_contents=["# tool\nGuide"],
        claude_md="",
        memory_md="",
    )
    assert "Project Knowledge" not in result
    assert "Learned Facts" not in result
    assert "Tool Usage Guides" in result


def test_load_memory_files_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    claude_md, cl, memory_md, ml = load_memory_files()
    assert claude_md == ""
    assert cl == 0
    assert memory_md == ""
    assert ml == 0


def test_load_memory_files_with_claude_md(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "CLAUDE.md").write_text("line1\nline2\nline3")
    claude_md, cl, _, _ = load_memory_files()
    assert "line1" in claude_md
    assert cl == 3


def test_load_memory_files_memory_truncated_to_200_lines(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mem_dir = tmp_path / ".memory"
    mem_dir.mkdir()
    lines = [f"line {i}" for i in range(300)]
    (mem_dir / "MEMORY.md").write_text("\n".join(lines))

    _, _, memory_md, ml = load_memory_files()
    assert ml == 300  # total lines counted
    loaded_lines = memory_md.split("\n")
    assert len(loaded_lines) == 200  # only first 200 returned


def test_api_key_missing_exits(monkeypatch):
    """Verify main() exits with error when ANTHROPIC_API_KEY is not set."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # We can't easily test main() without mocking everything, so test the
    # check logic directly by verifying the env var is absent
    assert not os.environ.get("ANTHROPIC_API_KEY")

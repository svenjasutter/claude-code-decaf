"""T104 — Unit tests for tool loader (tools/loader.py)."""

import asyncio
import inspect

import pytest

from tools.loader import load_tools


@pytest.fixture(scope="module")
def loaded_tools():
    return load_tools()


def test_discovers_all_python_tools(loaded_tools):
    defs, fns, _, _ = loaded_tools
    names = {d["name"] for d in defs}
    expected = {"read_file", "write_file", "find_files",
                "list_directory", "run_bash", "update_memory"}
    assert expected.issubset(names), f"Missing: {expected - names}"


def test_discovers_cli_tool(loaded_tools):
    defs, fns, _, _ = loaded_tools
    names = {d["name"] for d in defs}
    assert "prettier" in names


def test_tool_functions_are_async_callables(loaded_tools):
    _, fns, _, _ = loaded_tools
    for name, fn in fns.items():
        assert inspect.iscoroutinefunction(fn), f"{name} is not async"


def test_approval_required_from_config(loaded_tools):
    _, _, approval, _ = loaded_tools
    assert "write_file" in approval
    assert "run_bash" in approval


def test_skill_md_contents_populated(loaded_tools):
    defs, _, _, skills = loaded_tools
    assert len(skills) > 0
    assert len(skills) == len(defs)


def test_directory_without_skill_md_ignored(loaded_tools):
    defs, _, _, _ = loaded_tools
    names = {d["name"] for d in defs}
    assert "__pycache__" not in names

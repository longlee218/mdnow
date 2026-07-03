"""Tests for mdnow --update (network-free, no real install)."""
import subprocess
import sys

import pytest
import typer
from typer.testing import CliRunner

import mdnow.cli as cli
import mdnow.commands as commands

runner = CliRunner()


def _app():
    app = typer.Typer()
    app.command()(cli.main)
    return app


def _fake_find_spec(present: set[str]):
    def find_spec(name, *a, **k):
        return object() if name in present else None
    return find_spec


def _patch_env(monkeypatch, present_extras: set[str], uv_path: str | None):
    monkeypatch.setattr(commands.importlib.util, "find_spec", _fake_find_spec(present_extras))
    monkeypatch.setattr(commands.shutil, "which", lambda cmd: uv_path if cmd == "uv" else None)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs.get("check")))

    monkeypatch.setattr(commands.subprocess, "run", fake_run)
    return calls


def test_self_update_base_install_when_no_extras(monkeypatch):
    calls = _patch_env(monkeypatch, set(), "/fake/uv")
    res = runner.invoke(_app(), ["--update"])
    assert res.exit_code == 0
    assert len(calls) == 1
    cmd, check = calls[0]
    assert cmd == [
        "/fake/uv",
        "tool",
        "install",
        "--force",
        "mdnow @ git+https://github.com/longlee218/mdnow",
    ]
    assert check is True
    assert "updated successfully" in res.stdout


def test_self_update_combined_extras_when_detected(monkeypatch):
    calls = _patch_env(monkeypatch, {"camoufox", "markitdown"}, "/fake/uv")
    res = runner.invoke(_app(), ["--update"])
    assert res.exit_code == 0
    cmd, _ = calls[0]
    assert cmd == [
        "/fake/uv",
        "tool",
        "install",
        "--force",
        "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow",
    ]
    assert "updated successfully" in res.stdout


def test_self_update_falls_back_to_uv_python_module(monkeypatch):
    calls = _patch_env(monkeypatch, set(), None)
    monkeypatch.setattr(commands.importlib.util, "find_spec", _fake_find_spec({"uv"}))
    res = runner.invoke(_app(), ["--update"])
    assert res.exit_code == 0
    cmd, _ = calls[0]
    assert cmd[:3] == [sys.executable, "-m", "uv"]
    assert "mdnow @ git+https://github.com/longlee218/mdnow" in cmd[-1]


def test_self_update_uv_missing_shows_friendly_fallback(monkeypatch):
    _patch_env(monkeypatch, set(), None)
    monkeypatch.setattr(commands.importlib.util, "find_spec", _fake_find_spec(set()))
    res = runner.invoke(_app(), ["--update"])
    assert res.exit_code == 1
    assert "uv not found" in res.output
    assert "uv tool install --force" in res.output
    assert "install.sh" in res.output


def test_self_update_install_failure_exits_nonzero(monkeypatch):
    def failing_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(commands.importlib.util, "find_spec", _fake_find_spec(set()))
    monkeypatch.setattr(commands.shutil, "which", lambda cmd: "/fake/uv" if cmd == "uv" else None)
    monkeypatch.setattr(commands.subprocess, "run", failing_run)

    res = runner.invoke(_app(), ["--update"])
    assert res.exit_code == 1
    assert "Error" in res.output

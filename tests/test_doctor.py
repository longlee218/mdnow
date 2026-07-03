"""Tests for mdnow --doctor and --fetch-browser (network-free, no real download)."""
import typer
from typer.testing import CliRunner

import mdnow.cli as cli
import mdnow.commands as commands
import mdnow.doctor as doctor

runner = CliRunner()


def _app():
    app = typer.Typer()
    app.command()(cli.main)
    return app


def _fake_find_spec(present: set[str]):
    def find_spec(name, *a, **k):
        return object() if name in present else None
    return find_spec


# --- missing_extra_message ----------------------------------------------------


def test_missing_extra_message_includes_extra_and_install_command():
    msg = doctor.missing_extra_message("render")
    assert "[render]" in msg
    assert "mdnow[render]" in msg
    assert "git+" in msg  # distributed via git, not PyPI


# --- doctor.run_checks / render_report ----------------------------------------


def test_run_checks_reports_missing_extras_with_fix_commands(monkeypatch):
    monkeypatch.setattr(doctor.importlib.util, "find_spec", _fake_find_spec(set()))
    monkeypatch.setattr(doctor, "_check_skill", lambda: doctor.Check("Claude skill", False, "not installed", fix="mdnow --install-skill"))

    checks = doctor.run_checks()
    report = doctor.render_report(checks)

    assert "[MISSING] [docs] extra" in report
    assert "mdnow[docs]" in report
    assert "[MISSING] [render] extra" in report
    assert "mdnow[render]" in report
    assert "git+" in report  # git-based install hint, not PyPI
    assert "[MISSING] Claude skill" in report
    assert "mdnow --install-skill" in report


def test_run_checks_reports_installed_extras_as_ok(monkeypatch):
    monkeypatch.setattr(doctor.importlib.util, "find_spec", _fake_find_spec({"markitdown", "camoufox"}))
    monkeypatch.setattr(doctor, "_check_render_browser", lambda: doctor.Check("render browser", True, "downloaded (1.0)"))
    monkeypatch.setattr(doctor, "_check_skill", lambda: doctor.Check("Claude skill", True, "installed at ~/.claude/skills/mdnow"))

    report = doctor.render_report(doctor.run_checks())

    assert "[OK] [docs] extra: installed" in report
    assert "[OK] [render] extra: installed" in report
    assert "[OK] Claude skill" in report


def test_check_render_browser_unknown_when_camoufox_absent(monkeypatch):
    monkeypatch.setattr(doctor.importlib.util, "find_spec", _fake_find_spec(set()))
    check = doctor._check_render_browser()
    assert check.ok is False
    assert "render" in check.fix.lower() or "pip install" in check.fix


def test_check_render_browser_falls_back_to_unknown_on_error(monkeypatch):
    monkeypatch.setattr(doctor.importlib.util, "find_spec", _fake_find_spec({"camoufox"}))

    class FakePkgman:
        @staticmethod
        def camoufox_path(download_if_missing=True):
            raise FileNotFoundError("not downloaded")

    import sys
    monkeypatch.setitem(sys.modules, "camoufox.pkgman", FakePkgman())

    check = doctor._check_render_browser()
    assert check.ok is False
    assert "--fetch-browser" in check.fix


# --- saved-session store check --------------------------------------------------


def test_check_session_store_counts_files(tmp_path, monkeypatch):
    import mdnow.sessions as sessions
    store = tmp_path / "sessions"
    store.mkdir()
    (store / "a.corp.com.txt").write_text("# Netscape HTTP Cookie File\n")
    (store / "b.corp.com.txt").write_text("# Netscape HTTP Cookie File\n")
    monkeypatch.setattr(sessions, "SESSION_DIR", store)
    check = doctor._check_session_store()
    assert check.ok is True
    assert "2 saved" in check.detail and str(store) in check.detail


def test_check_session_store_empty_or_missing(tmp_path, monkeypatch):
    import mdnow.sessions as sessions
    monkeypatch.setattr(sessions, "SESSION_DIR", tmp_path / "nope")
    check = doctor._check_session_store()
    assert check.ok is True and check.detail == "none"


# --- --doctor CLI flag ---------------------------------------------------------


def test_doctor_flag_exits_zero_and_prints_report(monkeypatch):
    monkeypatch.setattr(doctor, "run_checks", lambda: [doctor.Check("Python", True, "3.13.0")])
    res = runner.invoke(_app(), ["--doctor"])
    assert res.exit_code == 0
    # --doctor renders a Rich table (render_report's [OK]/[MISSING] text format
    # is still covered by the render_report tests above)
    assert "mdnow doctor" in res.stdout
    assert "Python" in res.stdout and "3.13.0" in res.stdout


def test_doctor_flag_ignores_url_argument(monkeypatch):
    monkeypatch.setattr(doctor, "run_checks", lambda: [doctor.Check("Python", True, "3.13.0")])
    res = runner.invoke(_app(), ["--doctor", "https://s.com/p"])
    assert res.exit_code == 0
    assert "mdnow doctor" in res.stdout


# --- fetch_browser / --fetch-browser -------------------------------------------


def test_fetch_browser_without_render_extra_raises_friendly_error(monkeypatch):
    import pytest

    monkeypatch.setattr(commands.importlib.util, "find_spec", lambda name: None)

    def no_subprocess(*a, **k):
        raise AssertionError("must not attempt a download without [render]")
    monkeypatch.setattr(commands.subprocess, "run", no_subprocess)

    with pytest.raises(RuntimeError, match=r"\[render\]"):
        commands.fetch_browser()


def test_fetch_browser_with_render_extra_invokes_subprocess(monkeypatch):
    monkeypatch.setattr(commands.importlib.util, "find_spec", lambda name: object())
    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        called["check"] = check
    monkeypatch.setattr(commands.subprocess, "run", fake_run)

    commands.fetch_browser()

    assert called["check"] is True
    assert called["cmd"][1:] == ["-m", "camoufox", "fetch"]


def test_fetch_browser_flag_errors_cleanly_without_render(monkeypatch):
    def boom():
        raise RuntimeError(doctor.missing_extra_message("render"))
    monkeypatch.setattr(commands, "fetch_browser", boom)

    res = runner.invoke(_app(), ["--fetch-browser"])
    assert res.exit_code == 1
    assert "[render]" in res.output


def test_fetch_browser_flag_success_prints_confirmation(monkeypatch):
    monkeypatch.setattr(commands, "fetch_browser", lambda: None)
    res = runner.invoke(_app(), ["--fetch-browser"])
    assert res.exit_code == 0
    assert "downloaded" in res.stdout.lower()

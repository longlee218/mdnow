"""Unit tests for the self-healing Playwright driver patch (network-free)."""
import mdnow.playwright_patch as pp

_UNPATCHED = """\
location: {
  url: pageError.location.url,
  line: pageError.location.lineNumber,
  column: pageError.location.columnNumber
}
"""


def test_patch_applies_null_safe_defaults(tmp_path, monkeypatch):
    bundle = tmp_path / "coreBundle.js"
    bundle.write_text(_UNPATCHED, encoding="utf-8")
    monkeypatch.setattr(pp, "_core_bundle_path", lambda: bundle)

    assert pp.ensure_driver_patched() is True
    text = bundle.read_text()
    assert 'pageError.location?.url ?? ""' in text
    assert "pageError.location?.lineNumber ?? 0" in text
    assert "pageError.location?.columnNumber ?? 0" in text
    assert "pageError.location.url," not in text  # no unpatched dereference left


def test_patch_is_idempotent(tmp_path, monkeypatch):
    bundle = tmp_path / "coreBundle.js"
    bundle.write_text(_UNPATCHED, encoding="utf-8")
    monkeypatch.setattr(pp, "_core_bundle_path", lambda: bundle)

    assert pp.ensure_driver_patched() is True   # first: patched
    assert pp.ensure_driver_patched() is False  # second: nothing to do


def test_patch_noop_when_bundle_missing(monkeypatch):
    monkeypatch.setattr(pp, "_core_bundle_path", lambda: None)
    assert pp.ensure_driver_patched() is False


def test_patch_never_raises(tmp_path, monkeypatch):
    # unreadable path → swallowed, returns False (render must still proceed)
    monkeypatch.setattr(pp, "_core_bundle_path", lambda: tmp_path / "does-not-exist.js")
    assert pp.ensure_driver_patched() is False

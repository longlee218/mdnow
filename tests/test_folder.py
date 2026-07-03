"""Folder batch-convert: walk, per-file isolation, path mapping, artifacts."""
import json

import mdnow.convert as convert
import mdnow.folder as folder
from mdnow.extractor import Extracted


def _stub_convert(monkeypatch, bad: set[str] | None = None):
    """Stub convert.from_path: markdown echoes the file stem; paths in `bad` raise."""
    bad = bad or set()

    def fake(path, *, allow_remote=False):
        name = path.name
        if name in bad:
            raise ValueError(f"No content extracted from {name}")
        return Extracted(f"# {path.stem}\n\nbody of {name}", path.stem, None)

    monkeypatch.setattr(convert, "from_path", fake)


def _noise(msgs):
    return lambda m: msgs.append(m)


def test_nested_tree_converts_all(tmp_path, monkeypatch):
    (tmp_path / "a.md").write_text("x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.pdf").write_text("x")
    out = tmp_path / "out"
    _stub_convert(monkeypatch)

    ok, failed = folder.convert_folder(tmp_path, out, False, _noise([]))
    assert (ok, failed) == (2, 0)
    assert (out / "a.md").exists()
    assert (out / "sub" / "b.md").exists()  # extension stripped, parent preserved


def test_failure_is_isolated(tmp_path, monkeypatch):
    (tmp_path / "good.pdf").write_text("x")
    (tmp_path / "bad.pdf").write_text("x")
    out = tmp_path / "out"
    _stub_convert(monkeypatch, bad={"bad.pdf"})
    msgs = []

    ok, failed = folder.convert_folder(tmp_path, out, False, _noise(msgs))
    assert (ok, failed) == (1, 1)
    assert (out / "good.md").exists()
    assert not (out / "bad.md").exists()
    assert any("skipped bad.pdf" in m for m in msgs)


def test_dotfiles_and_dotdirs_skipped(tmp_path, monkeypatch):
    (tmp_path / "keep.txt").write_text("x")
    (tmp_path / ".DS_Store").write_text("x")
    git = tmp_path / ".git"
    git.mkdir()
    (git / "config").write_text("x")
    out = tmp_path / "out"
    _stub_convert(monkeypatch)

    ok, failed = folder.convert_folder(tmp_path, out, False, _noise([]))
    assert (ok, failed) == (1, 0)
    assert (out / "keep.md").exists()


def test_leaf_collision_gets_suffix(tmp_path, monkeypatch):
    # Two files whose leaf slugs collide (same dir): both slug to "report".
    (tmp_path / "Report.pdf").write_text("x")
    (tmp_path / "report.docx").write_text("x")
    out = tmp_path / "out"
    _stub_convert(monkeypatch)

    ok, failed = folder.convert_folder(tmp_path, out, False, _noise([]))
    assert (ok, failed) == (2, 0)
    mds = sorted(p.name for p in out.glob("*.md"))
    assert "report.md" in mds
    # the second file is disambiguated with a -<sha1[:6]> suffix
    assert any(m != "report.md" and m.startswith("report-") for m in mds)


def test_empty_folder(tmp_path, monkeypatch):
    out = tmp_path / "out"
    _stub_convert(monkeypatch)
    ok, failed = folder.convert_folder(tmp_path, out, False, _noise([]))
    assert (ok, failed) == (0, 0)
    assert (out / "manifest.json").exists()


def test_progress_called_per_file(tmp_path, monkeypatch):
    (tmp_path / "a.md").write_text("x")
    (tmp_path / "b.md").write_text("x")
    out = tmp_path / "out"
    _stub_convert(monkeypatch)
    calls = []

    folder.convert_folder(tmp_path, out, False, _noise([]),
                          progress=lambda i, t, rel: calls.append((i, t, rel)))
    assert [c[0] for c in calls] == [1, 2]
    assert all(c[1] == 2 for c in calls)


def test_real_unsupported_file_is_isolated_not_crash(tmp_path):
    """H1 regression: a file markitdown can't convert (UnsupportedFormat/
    FileConversion — neither RuntimeError nor ValueError) must be an isolated
    per-file failure, never abort the batch. Uses the REAL convert.from_path."""
    (tmp_path / "good.md").write_text("# Good\n\nreal content here\n")
    # empty file with an unknown extension → markitdown UnsupportedFormatException
    # (subclasses neither RuntimeError nor ValueError before the convert.py fix)
    (tmp_path / "bad.xyz").write_bytes(b"")
    out = tmp_path / "out"

    ok, failed = folder.convert_folder(tmp_path, out, False, _noise([]))
    assert (ok, failed) == (1, 1)  # good converted, bad.xyz skipped, no crash
    assert (out / "good.md").exists()
    assert (out / "manifest.json").exists()


def test_artifacts_content(tmp_path, monkeypatch):
    (tmp_path / "a.md").write_text("x")
    out = tmp_path / "out"
    _stub_convert(monkeypatch)

    folder.convert_folder(tmp_path, out, False, _noise([]))
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["host"] == tmp_path.name
    assert manifest["generated_from"] == str(tmp_path)
    assert manifest["page_count"] == 1
    assert manifest["pages"][0]["local_path"] == "a.md"
    assert (out / "llms.txt").read_text().startswith(f"# {tmp_path.name}")
    assert "a" in (out / "llms-full.txt").read_text()

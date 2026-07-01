import pytest

import mdnow.commands as commands


def test_install_skill_copies_files(tmp_path):
    dest = tmp_path / "installed"
    result = commands.install_skill(dest, force=False)

    assert result == dest
    assert (dest / "SKILL.md").exists()
    assert (dest / "references" / "usage-and-flags.md").exists()


def test_install_skill_default_dir(monkeypatch, tmp_path):
    default = tmp_path / "claude-skills" / "mdnow"
    monkeypatch.setattr(commands, "DEFAULT_SKILL_DIR", default)

    result = commands.install_skill(None, force=False)

    assert result == default
    assert (default / "SKILL.md").exists()


def test_installed_skill_has_no_machine_specific_paths(tmp_path):
    dest = tmp_path / "installed"
    commands.install_skill(dest, force=False)

    for path in dest.rglob("*.md"):
        text = path.read_text()
        assert "/Users/" not in text
        assert ".venv" not in text


def test_install_skill_refuses_to_overwrite_without_force(tmp_path):
    dest = tmp_path / "installed"
    commands.install_skill(dest, force=False)

    with pytest.raises(FileExistsError):
        commands.install_skill(dest, force=False)


def test_install_skill_overwrites_with_force(tmp_path):
    dest = tmp_path / "installed"
    commands.install_skill(dest, force=False)
    (dest / "stale-marker.txt").write_text("stale")

    commands.install_skill(dest, force=True)

    assert (dest / "SKILL.md").exists()
    assert not (dest / "stale-marker.txt").exists()


def test_install_skill_missing_source_raises(monkeypatch, tmp_path):
    class MissingSource:
        def is_dir(self):
            return False

        def __truediv__(self, other):
            return self

    monkeypatch.setattr(commands.importlib.resources, "files", lambda pkg: MissingSource())

    with pytest.raises(FileNotFoundError):
        commands.install_skill(tmp_path / "dest", force=False)

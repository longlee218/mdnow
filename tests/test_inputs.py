"""Input-type detection predicates."""
from mdnow.inputs import is_local_dir, is_local_file, is_youtube


def test_is_local_dir_true_for_existing_dir(tmp_path):
    assert is_local_dir(str(tmp_path)) is True


def test_is_local_dir_false_for_file(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    assert is_local_dir(str(f)) is False


def test_is_local_dir_false_for_missing_path(tmp_path):
    assert is_local_dir(str(tmp_path / "nope")) is False


def test_is_local_dir_false_for_http_url():
    assert is_local_dir("https://example.com/") is False
    assert is_local_dir("http://example.com") is False


def test_is_local_dir_false_for_empty():
    assert is_local_dir("") is False


def test_is_local_dir_and_file_mutually_exclusive(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    assert is_local_dir(str(tmp_path)) and not is_local_file(str(tmp_path))
    assert is_local_file(str(f)) and not is_local_dir(str(f))


def test_is_youtube_still_works():
    assert is_youtube("https://youtu.be/abc") is True

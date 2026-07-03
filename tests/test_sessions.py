"""Session store: playwright cookies → Netscape cookies.txt under ~/.mdnow/sessions."""
import pytest

from mdnow import sessions
from mdnow.auth import load_cookies

# Playwright page.context.cookies() shape
PW_COOKIES = [
    {
        "name": "session", "value": "abc123", "domain": ".corp.example.com",
        "path": "/", "expires": 1893456000.5, "httpOnly": False,
        "secure": True, "sameSite": "Lax",
    },
    {
        "name": "JSESSIONID", "value": "deadbeef", "domain": "wiki.corp.example.com",
        "path": "/wiki", "expires": -1, "httpOnly": True,
        "secure": False, "sameSite": "None",
    },
]


@pytest.fixture
def session_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(sessions, "SESSION_DIR", tmp_path / "sessions")
    return tmp_path / "sessions"


# --- to_netscape --------------------------------------------------------------

def test_to_netscape_emits_header_and_seven_tab_fields():
    text = sessions.to_netscape(PW_COOKIES)
    lines = text.splitlines()
    assert lines[0].startswith("# Netscape HTTP Cookie File")
    data = [l for l in lines if (l and not l.startswith("#")) or l.startswith("#HttpOnly_")]
    assert len(data) == 2
    for line in data:
        raw = line[len("#HttpOnly_"):] if line.startswith("#HttpOnly_") else line
        assert len(raw.split("\t")) == 7


def test_to_netscape_field_mapping():
    line = sessions.to_netscape([PW_COOKIES[0]]).splitlines()[-1]
    domain, subdomains, path, secure, expiry, name, value = line.split("\t")
    assert domain == ".corp.example.com"
    assert subdomains == "TRUE"  # leading-dot domain covers subdomains
    assert path == "/"
    assert secure == "TRUE"
    assert expiry == "1893456000"  # truncated to int
    assert (name, value) == ("session", "abc123")


def test_to_netscape_httponly_prefix_and_session_expiry():
    line = sessions.to_netscape([PW_COOKIES[1]]).splitlines()[-1]
    assert line.startswith("#HttpOnly_wiki.corp.example.com\t")
    fields = line[len("#HttpOnly_"):].split("\t")
    assert fields[1] == "FALSE"  # no leading dot → host-only
    assert fields[4] == "0"  # session cookie (-1) clamps to 0


def test_to_netscape_roundtrips_through_auth_load_cookies(tmp_path):
    p = tmp_path / "cookies.txt"
    p.write_text(sessions.to_netscape(PW_COOKIES), encoding="utf-8")
    cookies = load_cookies(p)
    assert {"name": "session", "value": "abc123", "domain": ".corp.example.com", "path": "/"} in cookies
    # httpOnly cookie survives the round-trip (prefix stripped by the parser)
    assert {"name": "JSESSIONID", "value": "deadbeef", "domain": "wiki.corp.example.com", "path": "/wiki"} in cookies
    assert len(cookies) == 2


def test_to_netscape_skips_cookies_that_would_break_the_line_format(tmp_path):
    """Control chars in a field = line injection into a persisted secrets file."""
    evil = [
        {"name": "tabbed", "value": "a\tb", "domain": "s.com", "path": "/"},
        {"name": "injected", "value": "x\n.evil.com\tTRUE\t/\tFALSE\t0\tsid\tpwned",
         "domain": "s.com", "path": "/"},
        {"name": "nodomain", "value": "v", "domain": "", "path": "/"},
        {"name": "good", "value": "ok", "domain": "s.com", "path": "/"},
    ]
    p = tmp_path / "cookies.txt"
    p.write_text(sessions.to_netscape(evil), encoding="utf-8")
    cookies = load_cookies(p)  # must stay parseable — unsafe entries skipped
    assert [c["name"] for c in cookies] == ["good"]
    assert not any(c["domain"] == ".evil.com" for c in cookies)


def test_to_netscape_none_expires_clamps_to_zero():
    line = sessions.to_netscape([
        {"name": "n", "value": "v", "domain": "s.com", "path": "/", "expires": None},
    ]).splitlines()[-1]
    assert line.split("\t")[4] == "0"


# --- save_session / lookup_session ---------------------------------------------

def test_save_session_writes_owner_only_file(session_dir):
    path = sessions.save_session("internal.corp.com", PW_COOKIES)
    assert path == session_dir / "internal.corp.com.txt"
    assert path.read_text(encoding="utf-8") == sessions.to_netscape(PW_COOKIES)
    assert path.stat().st_mode & 0o777 == 0o600
    assert session_dir.stat().st_mode & 0o777 == 0o700


def test_save_session_tightens_perms_of_preexisting_file(session_dir):
    session_dir.mkdir(parents=True)
    stale = session_dir / "internal.corp.com.txt"
    stale.write_text("old")
    stale.chmod(0o644)  # e.g. hand-copied file with umask perms
    path = sessions.save_session("internal.corp.com", PW_COOKIES)
    assert path == stale and path.stat().st_mode & 0o777 == 0o600


def test_save_session_normalizes_host_key(session_dir):
    path = sessions.save_session("Internal.Corp.COM:8443", PW_COOKIES)
    assert path.name == "internal.corp.com.txt"


def test_lookup_session_exact_host(session_dir):
    saved = sessions.save_session("internal.corp.com", PW_COOKIES)
    assert sessions.lookup_session("internal.corp.com") == saved
    assert sessions.lookup_session("INTERNAL.corp.com:443") == saved
    # exact host only — no parent-domain fallback (documented YAGNI)
    assert sessions.lookup_session("sub.internal.corp.com") is None


def test_lookup_session_missing_returns_none(session_dir):
    assert sessions.lookup_session("nowhere.example.com") is None


def test_lookup_session_no_dir_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(sessions, "SESSION_DIR", tmp_path / "does-not-exist")
    assert sessions.lookup_session("internal.corp.com") is None

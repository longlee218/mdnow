"""Auth material parsing: --header strings and cookie files (Netscape + JSON)."""
import json

import pytest

from mdnow.auth import load_cookies, parse_headers


# --- parse_headers -----------------------------------------------------------

def test_parse_headers_basic():
    assert parse_headers(["Authorization: Bearer tok123", "X-Team:  ops "]) == {
        "Authorization": "Bearer tok123",
        "X-Team": "ops",
    }


def test_parse_headers_value_may_contain_colons():
    assert parse_headers(["X-Time: 12:34:56"]) == {"X-Time": "12:34:56"}


def test_parse_headers_empty_list():
    assert parse_headers([]) == {}


@pytest.mark.parametrize("bad", ["NoColonHere", ": value-only", "Name:", "Name:   "])
def test_parse_headers_invalid_raises(bad):
    with pytest.raises(ValueError):
        parse_headers([bad])


def test_parse_headers_error_never_leaks_value():
    # secret hygiene: a malformed pair's VALUE must not appear in the error text
    with pytest.raises(ValueError) as exc:
        parse_headers([": supersecrettoken"])
    assert "supersecrettoken" not in str(exc.value)


# --- load_cookies: JSON ------------------------------------------------------

def test_load_cookies_json(tmp_path):
    p = tmp_path / "cookies.json"
    p.write_text(json.dumps([
        {"name": "session", "value": "abc", "domain": ".corp.example.com", "path": "/"},
        {"name": "csrf", "value": "x"},
    ]))
    cookies = load_cookies(p)
    assert cookies[0] == {"name": "session", "value": "abc", "domain": ".corp.example.com", "path": "/"}
    assert cookies[1]["name"] == "csrf" and cookies[1]["path"] == "/"


def test_load_cookies_json_rejects_entries_without_name_or_value(tmp_path):
    p = tmp_path / "cookies.json"
    p.write_text(json.dumps([{"name": "only-name"}]))
    with pytest.raises(ValueError):
        load_cookies(p)


# --- load_cookies: Netscape cookies.txt --------------------------------------

NETSCAPE = """\
# Netscape HTTP Cookie File
# This is a generated file! Do not edit.

.corp.example.com\tTRUE\t/\tTRUE\t1893456000\tsession\tabc123
#HttpOnly_.corp.example.com\tTRUE\t/wiki\tTRUE\t0\tJSESSIONID\tdeadbeef
"""


def test_load_cookies_netscape(tmp_path):
    p = tmp_path / "cookies.txt"
    p.write_text(NETSCAPE)
    cookies = load_cookies(p)
    assert {"name": "session", "value": "abc123", "domain": ".corp.example.com", "path": "/"} in cookies
    # #HttpOnly_ prefix is a real cookie, not a comment
    assert {"name": "JSESSIONID", "value": "deadbeef", "domain": ".corp.example.com", "path": "/wiki"} in cookies


def test_load_cookies_netscape_skips_comments_and_blanks(tmp_path):
    p = tmp_path / "cookies.txt"
    p.write_text(NETSCAPE)
    assert len(load_cookies(p)) == 2


def test_load_cookies_netscape_malformed_line_raises(tmp_path):
    p = tmp_path / "cookies.txt"
    p.write_text("not\ta\tcookie\n")
    with pytest.raises(ValueError):
        load_cookies(p)


def test_load_cookies_json_not_a_list_raises(tmp_path):
    p = tmp_path / "cookies.json"
    p.write_text('{"name": "x", "value": "y"}')
    # a bare object is ambiguous — require an explicit list
    with pytest.raises(ValueError):
        load_cookies(p)


def test_load_cookies_invalid_json_raises(tmp_path):
    p = tmp_path / "cookies.json"
    p.write_text("[not json")
    with pytest.raises(ValueError):
        load_cookies(p)


def test_parse_headers_no_colon_error_never_leaks_content():
    # regression: "Name=Value" typo must not echo the (possibly secret) argument
    with pytest.raises(ValueError) as exc:
        parse_headers(["Authorization=Bearer sk-supersecret"])
    msg = str(exc.value)
    assert "sk-supersecret" not in msg and "Authorization=" not in msg

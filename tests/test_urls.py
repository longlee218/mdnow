from mdnow.urls import build_path_map, canonical, same_host


def test_canonical_strips_query_fragment_and_slash():
    assert canonical("https://Site.com/a/?x=1#f") == "https://site.com/a"
    assert canonical("https://site.com/a") == canonical("https://site.com/a/")
    assert canonical("https://site.com/") == "https://site.com/"


def test_canonical_strips_default_ports_only():
    assert canonical("http://h.com:80/a") == "http://h.com/a"
    assert canonical("https://h.com:443/a") == "https://h.com/a"
    assert canonical("https://h.com:8080/a") == "https://h.com:8080/a"


def test_same_host():
    assert same_host("https://h.com/a", "h.com")
    assert not same_host("https://other.com/a", "h.com")


def test_path_map_mirrors_paths_root_is_home():
    m = build_path_map(["https://s.com/", "https://s.com/guides/auth"])
    assert m["https://s.com/"] == "home.md"
    assert m["https://s.com/guides/auth"] == "guides/auth.md"


def test_path_map_deterministic_and_collision_safe():
    a = build_path_map(["https://s.com/guides/auth", "https://s.com/guides/Auth"])
    b = build_path_map(["https://s.com/guides/auth", "https://s.com/guides/Auth"])
    assert a == b                       # stable across runs
    assert len(set(a.values())) == 2    # distinct URLs never overwrite


def test_path_map_avoids_reserved_index():
    m = build_path_map(["https://s.com/index"])
    assert m["https://s.com/index"] != "index.md"

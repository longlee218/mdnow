"""Extraction-quality heuristics: word-count thinness + link-density boilerplate."""
from mdnow.quality import THIN_WORDS, is_thin, link_density

PROSE = "This is a real paragraph of content with plenty of ordinary words in it. " * 10

LINK_FARM = "\n".join(
    f"- [Read more about topic number {i} here]({'https://x.com/' + str(i)})" for i in range(20)
)


def test_link_density_zero_for_prose():
    assert link_density(PROSE) == 0.0


def test_link_density_high_for_link_farm():
    assert link_density(LINK_FARM) > 0.8


def test_link_density_empty_input():
    assert link_density("") == 0.0


def test_is_thin_short_content():
    assert is_thin("too few words")


def test_is_thin_prose_is_not_thin():
    assert not is_thin(PROSE)


def test_is_thin_link_farm_over_word_threshold():
    # >THIN_WORDS words, but nearly all inside links → boilerplate → thin
    assert len(LINK_FARM.split()) > THIN_WORDS
    assert is_thin(LINK_FARM)


def test_is_thin_long_link_heavy_page_is_kept():
    # legit index pages can be link-heavy; past the size cap we keep them
    big_index = LINK_FARM * 10
    assert not is_thin(big_index)


def test_word_count_ignores_link_targets():
    # a URL is one "word" by naive split; density math must not count targets
    md = "[a](https://very-long-url.example.com/with/many/segments) " + "word " * 60
    assert not is_thin(md)

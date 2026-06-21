"""Render the `index.md` context tree from the crawled page set.

A nested bullet list keyed by URL-path depth — an AI-traversable map with
relative links to every per-page markdown file.
"""
from __future__ import annotations


def build_index(host: str, pages, url_map: dict[str, str]) -> str:
    lines = [f"# Site Index — {host}", ""]
    rows = sorted((url_map[p.canon], p.title or url_map[p.canon]) for p in pages)
    for rel, title in rows:
        depth = rel.count("/")
        lines.append(f"{'  ' * depth}- [{title}]({rel})")
    return "\n".join(lines) + "\n"

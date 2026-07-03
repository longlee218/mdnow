"""Emit AI-doc artifacts from a completed crawl.

- llms.txt      : llmstxt.org-shaped annotated index (supersedes the old index.md)
- llms-full.txt : every page's full markdown concatenated, source-tagged
- manifest.json : machine-readable index an orchestrating agent can traverse

`pages` is a list of dicts: {title, source_url, local_path, body} where body is
the FINAL (link-rewritten) markdown written to disk.
"""
from __future__ import annotations

import json
import re

from . import outline
from .frontmatter import content_hash


def _label(p: dict) -> str:
    """Single-line, bracket-free label — titles come from attacker-controlled HTML,
    so sanitize before interpolating into markdown link/heading syntax."""
    raw = p["title"] or p["local_path"]
    clean = re.sub(r"\s+", " ", raw).replace("[", "").replace("]", "").strip()
    return clean or p["local_path"]


def build_llms_txt(host: str, site_summary: str, pages: list[dict]) -> str:
    lines = [f"# {host}", "", f"> {site_summary}", "", "## Pages"]
    for p in pages:
        s = outline.summary_of(p["body"])
        lines.append(f"- [{_label(p)}]({p['local_path']})" + (f": {s}" if s else ""))
    return "\n".join(lines) + "\n"


def build_llms_full(host: str, site_summary: str, pages: list[dict]) -> str:
    parts = [f"# {host}", "", f"> {site_summary}", ""]
    for p in pages:
        parts += [f"## {_label(p)}", f"Source: {p['source_url']}", "", p["body"], ""]
    return "\n".join(parts).rstrip() + "\n"


def build_manifest(host: str, start_url: str, pages: list[dict]) -> str:
    entries = []
    for p in pages:
        body = p["body"]
        entries.append({
            "source_url": p["source_url"],
            "local_path": p["local_path"],
            "title": p["title"] or "",
            "content_hash": content_hash(body),
            "token_estimate": outline.token_estimate(body),
            "word_count": len(body.split()),
            "summary": outline.summary_of(body),
            "headings": outline.headings(body),
            # heading-delimited chunk map (slug/level/word/token sizes) so an
            # agent can pick a section before reading the local .md at all
            "sections": outline.sections(body),
        })
    doc = {
        "host": host,
        "generated_from": start_url,
        "page_count": len(entries),
        "pages": entries,
    }
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"

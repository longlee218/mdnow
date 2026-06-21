"""Build YAML frontmatter with content-hash versioning.

YAML is always rendered via a real dumper so titles containing ':' or quotes
can never break the document.
"""
from __future__ import annotations

import hashlib

import yaml


def content_hash(body: str) -> str:
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()


def build(
    source_url: str,
    title: str | None,
    published_date: str | None,
    fetched_date: str,
    version: int,
    body: str,
) -> dict:
    return {
        "source_url": source_url,
        "title": title or "",
        "published_date": published_date or None,
        "fetched_date": fetched_date,
        "version": version,
        "content_hash": content_hash(body),
        "word_count": len(body.split()),
    }


def render(meta: dict, body: str) -> str:
    fm = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm}\n---\n\n{body}\n"

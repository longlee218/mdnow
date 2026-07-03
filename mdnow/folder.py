"""Batch-convert a local directory to markdown + AI-doc artifacts.

Mirrors crawler.crawl_site over a local folder instead of a website: walk the
tree, convert each file via convert.from_path (with per-file error isolation —
one bad file never aborts the run), write versioned markdown, then emit the same
crawl-style artifacts (llms.txt / llms-full.txt / manifest.json).

Reuses existing seams unchanged: convert (file→markdown), writer (nested mkdir +
content-hash versioning), artifacts (index emission). Output filenames come from
slugs.file_slug (extension-stripped, same as single-file conversion) — NOT
urls.build_path_map, which is URL-only and would keep the extension as a slug
suffix. Genuine leaf-name collisions get a short deterministic sha1 suffix.
"""
from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Callable

from . import artifacts, convert
from .slugs import file_slug
from .writer import write


def _is_hidden(rel: PurePosixPath) -> bool:
    """True if any path component is a dotfile/dotdir (.git, .DS_Store, .venv…)."""
    return any(part.startswith(".") for part in rel.parts)


def _collect(root: Path) -> list[str]:
    """Sorted POSIX relpath strings for every non-hidden file under root."""
    rels: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if not _is_hidden(PurePosixPath(rel)):
            rels.append(rel)
    return sorted(rels)


def _map_paths(relpaths: list[str]) -> dict[str, str]:
    """Map each source relpath to a unique output .md relpath.

    Parent dirs are kept as-is (user's own local names); the leaf is
    file_slug(name)+".md" (drops the extension). On a collision the second and
    later files get a deterministic -<sha1[:6]> suffix from the source relpath.
    """
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for rel in relpaths:
        p = PurePosixPath(rel)
        leaf = f"{file_slug(Path(p.name))}.md"
        candidate = leaf if p.parent == PurePosixPath(".") else f"{p.parent}/{leaf}"
        if candidate in used:
            suffix = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:6]
            candidate = f"{candidate[:-3]}-{suffix}.md"
        used.add(candidate)
        mapping[rel] = candidate
    return mapping


def convert_folder(
    root: Path,
    out: Path,
    allow_remote: bool,
    echo: Callable[[str], None],
    *,
    progress: Callable[[int, int, str], None] | None = None,
) -> tuple[int, int]:
    """Convert every file under root → out/*.md + artifacts. Returns (ok, failed)."""
    relpaths = _collect(root)
    total = len(relpaths)
    echo(f"Found {total} file(s) to convert")

    extracted_by_rel: dict = {}
    failures: list[tuple[str, str]] = []
    for i, rel in enumerate(relpaths, 1):
        try:
            extracted_by_rel[rel] = convert.from_path(root / rel, allow_remote=allow_remote)
        except (RuntimeError, ValueError) as exc:
            failures.append((rel, str(exc)))
        if progress is not None:
            progress(i, total, rel)

    path_map = _map_paths(list(extracted_by_rel))
    out.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    rendered: list[dict] = []
    for rel, ex in extracted_by_rel.items():
        local = path_map[rel]
        src = str(root / rel)
        write(out / local, src, ex.title, ex.published_date, today, ex.markdown)
        rendered.append({"title": ex.title, "source_url": src, "local_path": local, "body": ex.markdown})

    host = root.name
    summary = f"Documentation converted from {host}"
    (out / "llms.txt").write_text(artifacts.build_llms_txt(host, summary, rendered), encoding="utf-8")
    (out / "llms-full.txt").write_text(artifacts.build_llms_full(host, summary, rendered), encoding="utf-8")
    (out / "manifest.json").write_text(artifacts.build_manifest(host, str(root), rendered), encoding="utf-8")

    for rel, err in failures:
        echo(f"  skipped {rel}: {err}")
    return len(rendered), len(failures)

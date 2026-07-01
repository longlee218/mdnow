"""Action helpers for CLI flags that aren't part of the fetch/convert funnel.

Kept separate from cli.py so the orchestration module stays under 200 lines.
"""
from __future__ import annotations

import importlib.resources
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_SKILL_DIR = Path.home() / ".claude" / "skills" / "mdnow"


def install_skill(dest_dir: Path | None, force: bool) -> Path:
    """Copy the bundled Claude skill to dest_dir (default: ~/.claude/skills/mdnow).

    Raises FileNotFoundError if the bundled skill is missing, and FileExistsError
    if dest_dir already exists and force is False.
    """
    source = importlib.resources.files("mdnow") / "skill"
    if not source.is_dir():
        raise FileNotFoundError(f"Bundled skill not found at {source}")

    dest = dest_dir or DEFAULT_SKILL_DIR
    if dest.exists():
        if not force:
            raise FileExistsError(f"{dest} already exists. Use --force to overwrite.")
        shutil.rmtree(dest)

    dest.parent.mkdir(parents=True, exist_ok=True)
    with importlib.resources.as_file(source) as source_path:
        shutil.copytree(source_path, dest)
    return dest


def fetch_browser() -> None:
    """Download the Camoufox browser binary inside the current environment.

    Raises RuntimeError with a friendly hint if the [render] extra isn't installed.
    """
    if importlib.util.find_spec("camoufox") is None:
        from .doctor import missing_extra_message
        raise RuntimeError(missing_extra_message("render"))
    subprocess.run([sys.executable, "-m", "camoufox", "fetch"], check=True)

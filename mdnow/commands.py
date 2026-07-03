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

import typer

DEFAULT_SKILL_DIR = Path.home() / ".claude" / "skills" / "mdnow"

_GIT_URL = "git+https://github.com/longlee218/mdnow"
_EXTRA_PROBES = [("render", "camoufox"), ("docs", "markitdown")]


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


def _detect_extras() -> list[str]:
    return [name for name, module in _EXTRA_PROBES if importlib.util.find_spec(module) is not None]


def _find_uv() -> list[str] | None:
    uv = shutil.which("uv")
    if uv:
        return [uv]
    if importlib.util.find_spec("uv") is not None:
        return [sys.executable, "-m", "uv"]
    return None


def self_update() -> None:
    """Upgrade mdnow in place using `uv tool install --force` from git.

    Detects installed extras best-effort and preserves them. Raises typer.Exit
    with a friendly manual-install hint when `uv` is not available.
    """
    extras = _detect_extras()
    pkg = f"mdnow[{','.join(extras)}]" if extras else "mdnow"
    spec = f"{pkg} @ {_GIT_URL}"

    uv_cmd = _find_uv()
    if uv_cmd is None:
        typer.secho("Error: uv not found on PATH.", fg=typer.colors.RED, err=True)
        typer.echo("To upgrade manually, run:")
        typer.echo(f'    uv tool install --force "{spec}"')
        typer.echo("Or use the shell one-liner:")
        typer.echo("    curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh")
        raise typer.Exit(1)

    cmd = [*uv_cmd, "tool", "install", "--force", spec]
    typer.echo(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    typer.echo("mdnow updated successfully.")

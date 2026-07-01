#!/bin/sh
# install.sh — one-line installer for mdnow (macOS/Linux only).
#
#   curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh
#
# What it does:
#   1. Ensures `uv` is installed (via the official astral.sh installer if missing).
#   2. Runs `uv tool install "mdnow[<extras>] @ git+<repo>"` from GitHub for an
#      isolated, PATH-ready install (mdnow is distributed via git, not PyPI).
#   3. If --render was selected, runs `mdnow --fetch-browser` (one-time ~300MB download).
#   4. If --skill was passed, runs `mdnow --install-skill`.
#   5. Prints next steps, including a PATH export line if needed.
#
# Flags:
#   --render        include the [render] extra (Camoufox stealth browser)
#   --docs          include the [docs] extra (markitdown file conversion)
#   --mcp           include the [mcp] extra (MCP server mode)
#   --all           shorthand for --render --docs --mcp
#   --skill         install the bundled Claude Code skill after install
#   -h, --help      show this help and exit
#
# Security-conscious alternative (don't pipe to sh):
#   curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh -o install.sh
#   less install.sh   # inspect it
#   sh install.sh --all --skill
set -eu

want_render=0
want_docs=0
want_mcp=0
want_skill=0

GIT_URL="git+https://github.com/longlee218/mdnow"

usage() {
    cat <<'EOF'
Usage: install.sh [--render] [--docs] [--mcp] [--all] [--skill] [-h|--help]

  --render   install the [render] extra (Camoufox stealth browser, ~300MB one-time download)
  --docs     install the [docs] extra (markitdown file conversion: PDF, Office, images, audio)
  --mcp      install the [mcp] extra (MCP server mode for AI assistants)
  --all      shorthand for --render --docs --mcp
  --skill    install the bundled Claude Code skill to ~/.claude/skills/mdnow
  -h, --help show this help and exit
EOF
}

for arg in "$@"; do
    case "$arg" in
        --render) want_render=1 ;;
        --docs) want_docs=1 ;;
        --mcp) want_mcp=1 ;;
        --all) want_render=1; want_docs=1; want_mcp=1 ;;
        --skill) want_skill=1 ;;
        -h|--help) usage; exit 0 ;;
        *)
            echo "Unknown option: $arg" >&2
            usage >&2
            exit 1
            ;;
    esac
done

# --- 1. Ensure uv is installed ---------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
    echo "==> uv not found; installing via astral.sh ..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # The official installer places uv in ~/.local/bin (or ~/.cargo/bin on
    # older releases) and writes an env file we can source for this shell.
    if [ -f "$HOME/.local/bin/env" ]; then
        # shellcheck disable=SC1091
        . "$HOME/.local/bin/env"
    fi
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) PATH="$HOME/.local/bin:$PATH" ;;
    esac
    case ":$PATH:" in
        *":$HOME/.cargo/bin:"*) ;;
        *) PATH="$HOME/.cargo/bin:$PATH" ;;
    esac
    export PATH

    if ! command -v uv >/dev/null 2>&1; then
        echo "Error: uv install completed but 'uv' is still not on PATH." >&2
        echo "Open a new shell (or source ~/.local/bin/env) and re-run this script." >&2
        exit 1
    fi
fi

# --- 2. Build extras list and install ---------------------------------------
extras=""
add_extra() {
    if [ -z "$extras" ]; then
        extras="$1"
    else
        extras="$extras,$1"
    fi
}
[ "$want_render" = 1 ] && add_extra render
[ "$want_docs" = 1 ] && add_extra docs
[ "$want_mcp" = 1 ] && add_extra mcp

# Package spec, with optional extras (e.g. "mdnow" or "mdnow[render,mcp]").
if [ -n "$extras" ]; then
    pkg="mdnow[$extras]"
else
    pkg="mdnow"
fi

echo "==> Installing $pkg from GitHub ($GIT_URL) ..."
# --force makes re-running the installer idempotent (upgrade / overwrite an
# existing mdnow install) instead of erroring with "Executable already exists".
uv tool install --force "$pkg @ $GIT_URL"

# --- 2b. Ensure uv's tool-bin dir is on PATH so the mdnow calls below work ---
# (Needed when uv was already installed and its bin dir isn't on PATH yet.)
uv_bin_dir="$(uv tool dir --bin 2>/dev/null || true)"
[ -z "$uv_bin_dir" ] && uv_bin_dir="$HOME/.local/bin"
case ":$PATH:" in
    *":$uv_bin_dir:"*) ;;
    *) PATH="$uv_bin_dir:$PATH"; export PATH ;;
esac

# --- 3. Download render browser if requested --------------------------------
if [ "$want_render" = 1 ]; then
    echo "==> Downloading Camoufox browser (one-time, ~300MB) ..."
    mdnow --fetch-browser
fi

# --- 4. Install Claude Code skill if requested -------------------------------
if [ "$want_skill" = 1 ]; then
    echo "==> Installing Claude Code skill ..."
    mdnow --install-skill
fi

# --- 5. Verify + next steps ---------------------------------------------------
echo ""
if command -v mdnow >/dev/null 2>&1; then
    echo "==> mdnow installed: $(command -v mdnow)"
    mdnow --doctor
else
    echo "Warning: install finished but 'mdnow' is not yet on PATH in this shell." >&2
fi

uv_bin_dir="$HOME/.local/bin"
case ":$PATH:" in
    *":$uv_bin_dir:"*) ;;
    *)
        echo ""
        echo "NOTE: $uv_bin_dir is not on your PATH. Add this to your shell profile:"
        echo ""
        echo "    export PATH=\"$uv_bin_dir:\$PATH\""
        echo ""
        ;;
esac

echo "Done. Try:  mdnow https://example.com"

# install.ps1 — one-line installer for mdnow (Windows).
#
#   irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 | iex
#
# What it does:
#   1. Ensures `uv` is installed (via the official astral.sh installer if missing).
#   2. Runs `uv tool install --force "mdnow[<extras>] @ git+<repo>"` from GitHub
#      for an isolated, PATH-ready install (mdnow is distributed via git, not PyPI).
#   3. If --render was selected, runs `mdnow --fetch-browser` (one-time ~300MB download).
#   4. If --skill was passed, runs `mdnow --install-skill`.
#   5. Prints next steps, including a PATH export line if needed.
#
# Flags:
#   -Render        include the [render] extra (Camoufox stealth browser)
#   -Docs          include the [docs] extra (markitdown file conversion)
#   -Mcp           include the [mcp] extra (MCP server mode)
#   -All           shorthand for -Render -Docs -Mcp
#   -Skill         install the bundled Claude Code skill after install
#   -Help          show this help and exit
#
# Security-conscious alternative (don't pipe to iex):
#   irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 -o install.ps1
#   notepad install.ps1   # inspect it
#   .\install.ps1 -All -Skill
param(
    [switch]$Render,
    [switch]$Docs,
    [switch]$Mcp,
    [switch]$All,
    [switch]$Skill,
    [switch]$Help
)

$GIT_URL = "git+https://github.com/longlee218/mdnow"

function Show-Usage {
    Write-Host "Usage: install.ps1 [-Render] [-Docs] [-Mcp] [-All] [-Skill] [-Help]"
    Write-Host ""
    Write-Host "  -Render   install the [render] extra (Camoufox stealth browser, ~300MB one-time download)"
    Write-Host "  -Docs     install the [docs] extra (markitdown file conversion: PDF, Office, images, audio)"
    Write-Host "  -Mcp      install the [mcp] extra (MCP server mode for AI assistants)"
    Write-Host "  -All      shorthand for -Render -Docs -Mcp"
    Write-Host "  -Skill    install the bundled Claude Code skill to `$env:USERPROFILE\.claude\skills\mdnow"
    Write-Host "  -Help     show this help and exit"
}

if ($Help) {
    Show-Usage
    exit 0
}

if ($All) {
    $Render = $true
    $Docs = $true
    $Mcp = $true
}

try {
    # --- 1. Ensure uv is installed ---------------------------------------------
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Write-Host "==> uv not found; installing via astral.sh ..."
        irm https://astral.sh/uv/install.ps1 | iex

        # The official installer places uv in ~\.local\bin (or ~\.cargo\bin on
        # older releases). Make sure those directories are on PATH for this shell.
        $localBin = Join-Path $env:USERPROFILE ".local\bin"
        $cargoBin = Join-Path $env:USERPROFILE ".cargo\bin"

        foreach ($dir in @($localBin, $cargoBin)) {
            if (Test-Path $dir -PathType Container) {
                $pathParts = $env:PATH -split ';'
                if ($pathParts -notcontains $dir) {
                    $env:PATH = "$dir;$env:PATH"
                }
            }
        }

        $uv = Get-Command uv -ErrorAction SilentlyContinue
        if (-not $uv) {
            throw "uv install completed but 'uv' is still not on PATH. Open a new PowerShell window and re-run this script."
        }
    }

    # --- 2. Build extras list and install ---------------------------------------
    $extras = @()
    if ($Render) { $extras += "render" }
    if ($Docs) { $extras += "docs" }
    if ($Mcp) { $extras += "mcp" }

    if ($extras.Count -gt 0) {
        $pkg = "mdnow[$($extras -join ',')]"
    } else {
        $pkg = "mdnow"
    }

    Write-Host "==> Installing $pkg from GitHub ($GIT_URL) ..."
    # --force makes re-running the installer idempotent (upgrade / overwrite an
    # existing mdnow install) instead of erroring with "Executable already exists".
    uv tool install --force "$pkg @ $GIT_URL"
    if ($LASTEXITCODE -ne 0) {
        throw "uv tool install failed with exit code $LASTEXITCODE."
    }

    # --- 2b. Ensure uv's tool-bin dir is on PATH so the mdnow calls below work ---
    # (Needed when uv was already installed and its bin dir isn't on PATH yet.)
    $uvBinDir = (uv tool dir --bin 2>$null) | Out-String
    $uvBinDir = $uvBinDir.Trim()
    if ([string]::IsNullOrWhiteSpace($uvBinDir)) {
        $uvBinDir = Join-Path $env:USERPROFILE ".local\bin"
    }
    if (Test-Path $uvBinDir -PathType Container) {
        $pathParts = $env:PATH -split ';'
        if ($pathParts -notcontains $uvBinDir) {
            $env:PATH = "$uvBinDir;$env:PATH"
        }
    }

    # --- 3. Download render browser if requested --------------------------------
    if ($Render) {
        Write-Host "==> Downloading Camoufox browser (one-time, ~300MB) ..."
        mdnow --fetch-browser
        if ($LASTEXITCODE -ne 0) {
            throw "mdnow --fetch-browser failed with exit code $LASTEXITCODE."
        }
    }

    # --- 4. Install Claude Code skill if requested -------------------------------
    if ($Skill) {
        Write-Host "==> Installing Claude Code skill ..."
        mdnow --install-skill
        if ($LASTEXITCODE -ne 0) {
            throw "mdnow --install-skill failed with exit code $LASTEXITCODE."
        }
    }

    # --- 5. Verify + next steps ---------------------------------------------------
    Write-Host ""
    $mdnow = Get-Command mdnow -ErrorAction SilentlyContinue
    if ($mdnow) {
        Write-Host "==> mdnow installed: $($mdnow.Source)"
        mdnow --doctor
    } else {
        Write-Warning "Install finished but 'mdnow' is not yet on PATH in this shell."
    }

    if (-not ($env:PATH -split ';' | Where-Object { $_ -eq $uvBinDir })) {
        Write-Host ""
        Write-Host "NOTE: $uvBinDir is not on your PATH. Add this to your PowerShell profile:"
        Write-Host ""
        Write-Host "    `$env:PATH = `"$uvBinDir;`$env:PATH`""
        Write-Host ""
    }

    Write-Host "Done. Try:  mdnow https://example.com"
    Write-Host "Upgrade:    mdnow --update"
} catch {
    Write-Error "install.ps1 failed: $_"
    exit 1
}

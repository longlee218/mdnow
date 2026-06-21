# FirstOpen Bootstrap Guide

## Overview

`/bootstrap-android` bootstraps a **new** Android project with Apero's FirstOpen + Ads SDK template.
- **Local mode**: clone to current directory
- **Remote mode**: clone + push to GitHub repo

**New projects only. Do NOT use on dirs/repos with existing source code.**

## Prerequisites

- Claude Code CLI installed
- GitHub CLI (`gh`) authenticated (remote mode)
- Access to [ADA-Tera-Template](https://github.com/Apero-Partner/ADA-Tera-Template) — request from team lead

## TODO_LIST.md Template

Agent creates this file in project root after bootstrap:

```markdown
# TODO List — Post-Bootstrap Setup

Complete these tasks to finalize your new project:

- [ ] **Change package name** — Update `applicationId` and `namespace` in `build.gradle.kts`, `AndroidManifest.xml`, and move source directories (skip if done via agent)
- [ ] **Replace google-services.json** — Download from Firebase Console → `app/google-services.json`
- [ ] **Update AppConstant.kt** — API keys, base URLs, app-specific constants
- [ ] **Update credentials in settings.gradle.kts** — Maven tokens, GitHub packages auth
- [ ] **Customize FirstOpen UI** — Splash screen, onboarding, language selection
```

## Standalone Package Rename

Run script directly on any Android project:

```bash
# Dry-run
bash scripts/rename_package.sh --new com.example.newapp --project-root /path/to/project

# Apply
bash scripts/rename_package.sh --new com.example.newapp --apply --project-root /path/to/project
```

Options: `--modules`, `--no-backup`, `--run-build`, `--verbose`. Run `-h` for help.

## Template Contents

- **Ads**: AdsInitializer, InterAdManager, RewardAdManager, BannerConfigs, CustomBannerAd (Compose)
- **FirstOpen**: SplashActivity, 11-language support, 3 onboarding screens, splash ad configs
- **Remote Config**: BaseRemoteConfiguration + 3 config classes (Ads, Logic, UI), Firebase RemoteConfig
- **Dependencies**: apero-firstopen 3.3.0, apero-ads 8.0.3, Firebase BOM 33.7.0, Koin 4.1.1
- **Architecture**: MVI base, permission management, locale/toast systems, Koin DI

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Push permission denied | `gh auth status` — need push access |
| Target repo not found | Create repo on GitHub first — must be empty |
| Dir/repo not empty | New projects only — use empty directory or repo |
| Build fails after bootstrap | Check `TODO_LIST.md` — credentials/google-services.json missing |

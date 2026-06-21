---
name: project-kickoff
description: Generate Project Kickoff XLSX for mobile app projects. Use when user provides idea/usecase and needs structured kickoff document with user segment, competitor analysis, feature scope, design direction, and timeline.
---

# Project Kickoff Generator

## Purpose

Transform product ideas into structured XLSX kickoff documents for mobile app development. Automates user segmentation, persona mapping, and MVP scoping.

## When to Use

- User has a new app idea and needs kickoff documentation
- Need to analyze target users and competitors for a product concept
- Creating MVP scope with prioritized features (Must have / Nice have)
- Mapping product to design persona (P1-P7)

## Quick Start

```bash
node scripts/generate.js \
  --idea "AI Photo Editor" \
  --usecase "Edit photos with AI filters" \
  --target "Users 18-35" \
  --output "./"
```

Minimal (infers missing fields):
```bash
node scripts/generate.js --idea "AI Pet Studio"
```

## Core Principles

1. **English output only** - All document content must be in English
2. **MVP focus** - Prioritize features as Must have / Nice have
3. **Persona-driven design** - Auto-detect P1-P7 based on keywords
4. **Research-backed** - Include real competitor apps from Play Store

## Available References

- `references/personas.md` - Full P1-P7 persona style mapping with keywords
- `references/features.md` - Common feature templates by app category
- `references/output-format.md` - Detailed XLSX structure and styling specs

## Scripts

| Script                 | Purpose                              |
|------------------------|--------------------------------------|
| `scripts/generate.js`  | Generate XLSX + MD files             |
| `scripts/translate.js` | Ensure English-only output           |

## Anti-patterns

- ❌ DO NOT output Vietnamese in document
- ❌ DO NOT skip competitor research
- ❌ DO NOT use placeholder apps (App 1, App 2...)
- ❌ DO NOT add features outside MVP scope

## Notes

- Requires `exceljs` package in scripts folder
- Output: `AAPxxx_<idea>_Kickoff.xlsx`
- Timeline always has exactly 4 phases

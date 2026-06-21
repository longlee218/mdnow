---
name: product-requirements
description: Generate Product Requirements Document (PRD) for mobile app projects. Use AFTER kickoff is approved. Creates detailed PRD with user stories, UI specs, user flows, and remote config.
---

# Product Requirements Document (PRD) Generator

## Purpose

Generate detailed PRD documents for mobile app development. Converts approved kickoff scope into actionable requirements for dev team.

## When to Use

- After kickoff document is approved
- Need detailed user stories with acceptance criteria
- Need UI specifications and checklists
- Need user flow diagrams
- Preparing for sprint planning

## Prerequisites

- Approved kickoff document (from `project-kickoff` skill)
- Defined feature list with priorities
- Basic understanding of screens/flows

## Quick Start

```bash
node scripts/generate.js \
  --name "AI Family Archive" \
  --code "AAP857" \
  --description "App lưu trữ và khôi phục ảnh gia đình bằng AI" \
  --screens "Home,Pick Photo,Prepare,Loading,Result,History,Settings" \
  --output "./"
```

## Output Structure

Markdown file with 11 sections + appendix (ADA911 format):

1. **Overview** - Product vision, scope, assumptions
2. **User Stories** - Grouped by feature, table format (ID/Story/Priority/Acceptance Criteria)
3. **Feature Specifications** - Per-feature property tables, component breakdowns
4. **Screen Flows & Navigation** - Activity map, navigation structure (ASCII), key user flows
5. **UI Specifications** - Design system, color palette, spacing, typography, screen layouts (ASCII art)
6. **Remote Configuration** - Feature flags, monetization config, processing config
7. **Non-Functional Requirements** - Performance, compatibility, security, reliability, localization
8. **API Specifications** - Endpoints, request/response formats, error codes
9. **Data Models** - Kotlin/Swift data classes, state models, navigation destinations
10. **Analytics Events** - Lifecycle, navigation, core feature, export, monetization events
11. **Release Plan** - Current release features, quality gates, next release, version history
- **Appendix** - Key files reference, third-party integrations, build configuration

## Core Principles

1. **Actionable** - Every item must be implementable
2. **Testable** - Clear acceptance criteria
3. **Complete** - Cover all screens and flows
4. **Consistent** - Follow standard format

## Available References

- `references/user-story-template.md` - User story format and examples
- `references/ui-checklist-template.md` - UI spec format
- `references/flow-template.md` - User flow diagram format

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/generate.js` | Generate PRD markdown file |

## Anti-patterns

- ❌ DO NOT write PRD before kickoff approval
- ❌ DO NOT skip acceptance criteria
- ❌ DO NOT use vague requirements ("should be fast")
- ❌ DO NOT mix different features in one user story

## Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--name` | Yes | Product name |
| `--code` | Yes | Product code (AAPxxx) |
| `--description` | Yes | Product description |
| `--screens` | Yes | Comma-separated screen list |
| `--features` | No | Feature list from kickoff |
| `--output` | No | Output directory |

## Notes

- Output: `{code}_{name}_PRD.md`
- Agent should analyze kickoff and expand into detailed PRD
- Template generates placeholder structure; agent fills in real content

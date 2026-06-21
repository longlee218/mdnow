# QA & UAT Skill

Generate QA Test Cases and UAT Scenarios from PRD for mobile app projects.

## Quick Start

```bash
node scripts/generate.js \
  --name "Project Name" \
  --code "AAP001" \
  --prd "./path/to/PRD.md"
```

## Output

- `AAPxxx_ProjectName_QA_UAT.md` - Test cases organized by feature

## Test Categories

Each feature table includes these test types:

| Type | Description |
|------|-------------|
| `Functional` | Feature works as specified |
| `UI/UX` | Colors, layout structure (basic) |
| `Navigation` | Screen flows, back button, gestures |
| `Network` | Online/offline, slow connection |
| `Interrupt` | Calls, notifications, background/foreground |
| `Localization` | Languages, date/currency formats |
| `Remote Config` | Feature flags, config values, A/B tests, force update |
| `Regression` | Core features checklist |
| `UAT` | End-user acceptance scenarios |

## Document Structure

See `references/output-format.md` for detailed structure.

## Workflow

1. Read PRD document
2. Extract features and user stories
3. Generate test cases per feature
4. Add standard tests (Regression, UAT)
5. Output markdown file

## Parameters

| Param | Required | Description |
|-------|----------|-------------|
| `--name` | Yes | Project name |
| `--code` | Yes | Project code (AAPxxx) |
| `--prd` | Yes | Path to PRD file |
| `--output` | No | Output directory (default: current) |

## Integration with PRD

```
PRD User Stories → Functional + UAT tests
PRD UI Specs → UI/UX tests
PRD Navigation → Navigation tests
PRD Features → Feature-based tables
```

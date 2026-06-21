---
name: kickoff
description: Kickoff mobile app project — generate docs, estimate, and wireframes
argument-hint: <app idea / description> [--code AAPxxx] [--target "user segment"] [--region "market"]
sub-skills:
  doc:
    description: ⚡ Generate project docs only (no UI-UX)
    argument-hint: <app idea / description> [--code AAPxxx] [--target "user segment"] [--region "market"]
  auto:
    description: ⚡ Generate all project docs + UI-UX without prompts
    argument-hint: <app idea / description> [--code AAPxxx] [--target "user segment"] [--region "market"]
  normal:
    description: ⚡ Generate project docs with review prompts (default)
    argument-hint: <app idea / description> [--code AAPxxx] [--target "user segment"] [--region "market"]
---

## Your Mission

Generate project documentation for:
<idea>
$ARGUMENTS
</idea>

## Execution Modes

Detect mode from arguments or use sub-skills:
- `/kickoff:auto` or `--auto` → **Auto Mode**: Run all steps, no prompts, include UI-UX
- `/kickoff:doc` or `--doc` → **Doc Mode**: Run all steps, no prompts, docs only (no UI-UX)
- `/kickoff` or `/kickoff:normal` → **Normal Mode**: Prompt for review after each step

## Output Structure

All project files are saved in a dedicated project folder:
```
plans/{AAPxxx}_{slug}/
├── AAPxxx_Project_Kickoff.md
├── AAPxxx_Project_Kickoff.xlsx
├── design-system.md
├── AAPxxx_Project_PRD.md
├── AAPxxx_Project_QA_UAT.md
└── wireframes/
    └── AAPxxx_Wireframe.pen
```

**IMPORTANT:** Create the project folder first, then pass the folder path to all agents.

## Workflow

### Phase 1: Kickoff (ba-writer)

1. Create project folder: `plans/{AAPxxx}_{slug}/`
2. **Delegate to `ba-writer` agent** with the app idea and project folder path
3. Agent generates **Kickoff only** (prompt: "generate Kickoff only, Step 1 only")
4. Collect Kickoff output file paths

**Mode behavior:**
- **Normal**: Agent prompts for review after Kickoff
- **Auto/Doc**: Agent runs Kickoff straight through without prompts

---

### Phase 1.5: Design System (ui-ux-pro-max)

After Kickoff is generated, orchestrator runs design system generation inline (~5 seconds).

1. **Extract query params from Kickoff output** — parse the `DESIGN STYLE` section:
   - `Main Usecase` → app type keywords (e.g. "photo editor AI")
   - `Persona` → persona style (e.g. "creator")
   - `Primary Style` → style keywords (e.g. "minimalistic professional")
2. **Run design system generation** (inline, ~5 seconds):
```bash
.claude/skills/.venv/bin/python3 .claude/skills/ui-ux-pro-max/scripts/search.py \
  "<app_type> <persona_style> <style_keywords>" \
  --design-system -p "<project_name>" --format markdown \
  > {project_folder}/design-system.md
```
3. **Verify output** — confirm `design-system.md` contains colors, typography, and style tokens

**IMPORTANT:** This step runs between Kickoff and PRD. The design system ensures visual consistency across PRD specs and wireframes.

---

### Phase 2: PRD (ba-writer)

After design system is generated, delegate PRD generation to ba-writer.

1. **Delegate to `ba-writer` agent** with project folder path (prompt: "generate PRD only, Step 2 only")
2. Agent reads `design-system.md` from project folder for UI specs
3. Collect PRD output file path

**Mode behavior:**
- **Normal**: Agent prompts for review after PRD
- **Auto/Doc**: Agent runs PRD straight through without prompts

---

### Phase 3: QA-UAT + Wireframe (parallel)

After PRD is complete, spawn both in parallel:

**If Doc Mode**: Spawn QA-UAT only, skip wireframe.

**If Normal Mode**: Ask user if they want wireframe, then spawn accordingly.

**If Auto Mode**: Spawn both automatically.

**Parallel execution:**
```
PRD complete ──┬── ba-writer agent → QA-UAT (background)
               └── ui-designer agent → Wireframe .pen (background, reads design-system.md)
```

1. **Spawn `ba-writer` agent** (background) — generate QA-UAT from PRD
2. **Spawn `ui-designer` agent** (background) — generate wireframe from PRD + design-system.md
3. Both agents run simultaneously, both read from the same PRD
4. Wait for both to complete, collect output file paths

**IMPORTANT:** Spawn both agents in a SINGLE message with multiple Agent tool calls to ensure true parallel execution.

---

## Completion

Show final summary:

```
✅ **PROJECT GENERATION COMPLETE**

📁 Project folder: plans/{AAPxxx}_{slug}/

📄 Documents:
- Kickoff: AAPxxx_Project_Kickoff.xlsx/.md
- Design System: design-system.md
- PRD: AAPxxx_Project_PRD.md
- QA-UAT: AAPxxx_Project_QA_UAT.md

🎨 UI-UX: [Generated / Skipped]
- wireframes/AAPxxx_Wireframe.pen
```

---

## Mode Summary

| Mode | Docs | Review docs? | UI-UX | Review UI? |
|------|------|--------------|-------|------------|
| Normal | ✅ | ✅ Each step | Ask user | ✅ Wireframe |
| Auto | ✅ | ❌ | ✅ Auto | ❌ |
| Doc | ✅ | ❌ | ❌ Skip | - |

## Examples

```
/kickoff Pet Health Tracker           → Normal mode
/kickoff Recipe Scanner --auto        → Auto mode (all + UI-UX)
/kickoff Split Bill --doc             → Doc mode (docs only)
```

## Important Notes

**IMPORTANT:** This command runs in BACKGROUND mode.
**IMPORTANT:** Each agent runs in background, does not block main session.
**IMPORTANT:** Only notify user when:
  - Need input/approval (Normal mode)
  - Output complete (show file paths)
**IMPORTANT:** Pass PRD file path to ui-designer agent.
**IMPORTANT:** Ensure token efficiency while maintaining high quality.

# Output Formats

## Wireframe Output

### Pencil MCP File (`{code}_Wireframe.pen`)

Interactive wireframe created via Pencil MCP `batch_design` operations. Editable in Pencil editor.

**Elements:**
- Screen frames (390x844px, iPhone standard)
- Status bar, app bar, content wrapper, bottom nav
- Component placeholders with labels
- Navigation flow indicators

## File Naming Convention

| File | Pattern | Example |
|------|---------|---------|
| Wireframe | `{code}_Wireframe.pen` | `AAP001_Wireframe.pen` |

## Output Directory Structure

```
plans/{code}_{slug}/
└── wireframes/
    └── {code}_Wireframe.pen
```

## Viewing Wireframe

Open `.pen` file in Pencil desktop app, or edit via Pencil MCP tools:
- `batch_get` — read nodes
- `batch_design` — modify nodes
- `get_screenshot` — visual preview

## Integration with Other Skills

| Skill | Input | Output |
|-------|-------|--------|
| product-requirements | — | PRD.md → ui-design-pencil input |
| ui-design-pencil | PRD.md | Wireframe.pen |
| qa-uat | PRD.md | Test cases |

# Pencil MCP Cheatsheet

## Operation Syntax

Every line is a single operation with optional binding:
```javascript
binding=I(parent, {nodeData})   // Insert
binding=C("nodeId", parent, {}) // Copy
binding=R("path", {nodeData})   // Replace
U("nodeId", {updateData})       // Update (no children!)
D("nodeId")                     // Delete
M("nodeId", parent, index)      // Move
G("nodeId", "ai"|"stock", "prompt") // Generate image fill
```

## Property Reference

### Text Nodes
| Property | Type | Example |
|----------|------|---------|
| `content` | string | `"Hello World"` |
| `fill` | hex color | `"#1A1A1A"` (this IS the text color) |
| `fontSize` | number | `16` |
| `fontWeight` | string | `"600"`, `"bold"`, `"normal"` |
| `fontFamily` | string | `"Inter"`, `"DM Sans"` |
| `letterSpacing` | number | `0.5` |

### Frame Nodes
| Property | Type | Example |
|----------|------|---------|
| `fill` | hex color | `"#FFFFFF"` (background color) |
| `layout` | string | `"vertical"` or `"horizontal"` |
| `gap` | number | `12` (spacing between children) |
| `padding` | array | `[top, right, bottom, left]` or `[vertical, horizontal]` |
| `width` | number/string | `390`, `"fill_container"`, `"fit_content(0)"` |
| `height` | number/string | `844`, `"fill_container"`, `"fit_content(0)"` |
| `cornerRadius` | array/number | `[16,16,16,16]` or `16` |
| `justifyContent` | string | `"center"`, `"space-between"`, `"flex-start"`, `"flex-end"` |
| `alignItems` | string | `"center"`, `"flex-start"`, `"flex-end"` |
| `placeholder` | boolean | `true` — marks frame as container for children |
| `stroke` | hex color | `"#E5E7EB"` (border color) |
| `strokeWidth` | number | `1` |

## Common Gotchas

1. **Text color is `fill`, NOT `color` or `textColor`** — `textColor` is silently ignored
2. **`SF Pro` font is invalid** — use `"Inter"` as fallback for system font
3. **No `flexWrap`** — for 2-col grids, use nested horizontal row frames
4. **`placeholder: true`** — MUST set on frames that receive child insertions
5. **Max 25 operations per `batch_design` call** — split across multiple calls
6. **Bindings expire after each `batch_design` call** — use returned node IDs for subsequent calls
7. **Cannot Update children** — use Insert/Replace for child modifications
8. **`justifyContent: "space-between"`** → stored as `"space_between"` (underscore)
9. **Images** — no `image` node type; use G() on a frame/rectangle to apply image fill

## Screen Template (390x844 iPhone)

```javascript
// 1. Screen frame
screen=I(document, {type:"frame", name:"Screen Name", width:390, height:844, fill:"#FFFFFF", layout:"vertical", placeholder:true})

// 2. Status bar (62px, always first)
sb=I(screen, {type:"frame", name:"Status Bar", width:"fill_container", height:62, fill:"#FFFFFF", layout:"horizontal", padding:[0,24,0,24], justifyContent:"space-between", alignItems:"center"})
time=I(sb, {type:"text", content:"9:41", fontSize:16, fontWeight:"600", fontFamily:"Inter", fill:"#1A1A1A"})
icons=I(sb, {type:"text", content:"signal battery", fontSize:12, fill:"#1A1A1A"})

// 3. App bar (52px)
bar=I(screen, {type:"frame", name:"App Bar", width:"fill_container", height:52, layout:"horizontal", padding:[0,20,0,20], justifyContent:"space-between", alignItems:"center"})
title=I(bar, {type:"text", content:"Title", fontSize:20, fontWeight:"700", fontFamily:"DM Sans", fill:"#1A1A1A"})

// 4. Content wrapper (fill remaining space)
content=I(screen, {type:"frame", name:"Content", width:"fill_container", height:"fill_container", layout:"vertical", gap:20, padding:[0,20,24,20], placeholder:true})

// 5. Bottom nav (83px, pill style)
nav=I(screen, {type:"frame", name:"Bottom Nav", width:"fill_container", height:83, layout:"horizontal", padding:[12,21,21,21]})
pill=I(nav, {type:"frame", width:"fill_container", height:62, cornerRadius:[36,36,36,36], layout:"horizontal", padding:[4,4,4,4], stroke:"#E5E7EB"})
```

## 2-Column Grid Pattern

```javascript
grid=I(content, {type:"frame", name:"Grid", width:"fill_container", layout:"vertical", gap:12})
row=I(grid, {type:"frame", layout:"horizontal", gap:12, width:"fill_container"})
c1=I(row, {type:"frame", width:"fill_container", height:200, fill:"#F6F7F8", cornerRadius:[16,16,16,16]})
c2=I(row, {type:"frame", width:"fill_container", height:200, fill:"#F6F7F8", cornerRadius:[16,16,16,16]})
```

## Pill Tab Bar Pattern

```javascript
tab=I(pill, {type:"frame", name:"Tab Active", width:"fill_container", height:"fill_container", cornerRadius:[26,26,26,26], fill:"#6C5CE7", layout:"vertical", gap:4, justifyContent:"center", alignItems:"center"})
ico=I(tab, {type:"text", content:"icon", fontSize:18, fill:"#FFFFFF"})
lbl=I(tab, {type:"text", content:"HOME", fontSize:10, fontWeight:"600", fontFamily:"DM Sans", fill:"#FFFFFF", letterSpacing:0.5})
```

## Design Tokens via Variables

Convert `get_style_guide()` output into Pencil variables, then reference with `$` prefix:

```javascript
// 1. Define variables via set_variables()
set_variables(variables={
  "color.bg": {"type":"color", "value":"#FFFFFF"},
  "color.surface": {"type":"color", "value":"#F6F7F8"},
  "color.primary": {"type":"color", "value":"#6C5CE7"},
  "color.text": {"type":"color", "value":"#1A1A1A"},
  "text.title": {"type":"number", "value":20}
})

// 2. Reference in batch_design with $ prefix
screen=I(document, {type:"frame", fill:"$color.bg", width:390, height:844})
title=I(screen, {type:"text", fill:"$color.text", fontSize:"$text.title", content:"Title"})
```

Theming: variables can have multiple values per theme axis (light/dark).

## Validation Checklist

After building each screen:
1. `get_screenshot(nodeId=screenId)` — visual check for alignment, visibility
2. `snapshot_layout(parentId=screenId, maxDepth=2)` — verify computed positions
3. `snapshot_layout(problemsOnly=true)` — detect clipping/overflow issues
4. Check all text has `fill` set — default is invisible on white background

# Component Library

## Standard Components

| Type | Description | Common Props |
|------|-------------|--------------|
| `AppBar` | Top navigation bar | title, backButton, actions |
| `BottomNav` | Bottom tab navigation | items (3-5), activeIndex |
| `Card` | Content card container | image, title, subtitle, action |
| `List` | Scrollable vertical list | items, divider, onItemClick |
| `Grid` | Grid layout | columns (2-4), items, gap |
| `Button` | Action button | text, variant (primary/secondary), icon |
| `FAB` | Floating action button | icon, position, onPress |
| `TextField` | Text input field | label, placeholder, type, error |
| `Image` | Image/icon placeholder | src, aspectRatio, rounded |
| `Carousel` | Horizontal scroll cards | items, autoPlay, indicators |
| `Avatar` | User profile image | src, size (sm/md/lg), badge |
| `Chip` | Filter/tag chip | text, selected, onToggle |
| `Toggle` | On/off switch | value, label, disabled |
| `ProgressIndicator` | Loading spinner/bar | type (circular/linear), value |
| `Divider` | Horizontal line separator | - |

## Component Specifications

### AppBar
```
┌─────────────────────────────────────┐
│ [←]  Title                   [⋮][🔍]│
└─────────────────────────────────────┘

Height: 56dp
Background: Primary color or white
Leading: Back button or menu
Title: Screen name (16-20sp, bold)
Trailing: 1-3 action icons
```

### BottomNav
```
┌─────────────────────────────────────┐
│  🏠     🔍     ➕     ❤️     👤    │
│ Home  Search  Add   Saved Profile  │
└─────────────────────────────────────┘

Height: 56-64dp
Items: 3-5 tabs
Icon: 24dp
Label: 10-12sp (optional)
Active: Primary color
Inactive: Gray
```

### Card
```
┌─────────────────────┐
│ ┌─────────────────┐ │
│ │     Image       │ │  Height: flexible
│ └─────────────────┘ │
│ Title               │  16sp bold
│ Subtitle            │  14sp gray
│ [Action]            │  Optional button
└─────────────────────┘

Padding: 12-16dp
Corner radius: 8-12dp
Elevation: 2-4dp
```

### TextField
```
┌─────────────────────────────────────┐
│ Label                               │
│ ┌─────────────────────────────────┐ │
│ │ Placeholder text...              │ │
│ └─────────────────────────────────┘ │
│ Helper text or error                │
└─────────────────────────────────────┘

Height: 48-56dp
Padding: 12-16dp
Border: 1dp, rounded 8dp
Label: 12sp, above or inside
```

### Button
```
Primary:
┌─────────────────────┐
│ [Icon] Button Text  │  Background: Primary
└─────────────────────┘  Text: White

Secondary:
┌─────────────────────┐
│ [Icon] Button Text  │  Border: Primary
└─────────────────────┘  Text: Primary

Text:
  Button Text            Text: Primary

Height: 40-48dp
Padding: 16dp horizontal
Corner radius: 8dp or full-rounded
```

### List Item
```
┌─────────────────────────────────────┐
│ [○]  Title                    [→]  │
│      Subtitle                       │
├─────────────────────────────────────┤

Height: 56-72dp
Leading: Icon/Avatar/Checkbox
Title: 16sp
Subtitle: 14sp gray
Trailing: Arrow/Action/Info
```

## Component States

| State | Visual Change |
|-------|---------------|
| Default | Normal appearance |
| Focused | Border highlight, elevation |
| Pressed | Darker/lighter shade |
| Disabled | 50% opacity, no interaction |
| Error | Red border, error message |
| Loading | Spinner overlay |

## Spacing Guidelines

| Size | Value | Use Case |
|------|-------|----------|
| xs | 4dp | Icon padding |
| sm | 8dp | Tight spacing |
| md | 16dp | Standard margin/padding |
| lg | 24dp | Section spacing |
| xl | 32dp | Large gaps |

## Typography

| Style | Size | Weight | Use Case |
|-------|------|--------|----------|
| H1 | 28sp | Bold | Screen title |
| H2 | 22sp | Bold | Section header |
| H3 | 18sp | SemiBold | Card title |
| Body | 16sp | Regular | Content text |
| Caption | 14sp | Regular | Secondary text |
| Small | 12sp | Regular | Labels, hints |

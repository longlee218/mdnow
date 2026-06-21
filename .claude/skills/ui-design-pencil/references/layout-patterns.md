# Layout Patterns

## Screen Layout Template

```markdown
## [Screen Name]

### Layout Structure
| Section | Components |
|---------|------------|
| Header | AppBar, Search icon |
| Body | Content list/grid |
| Footer | BottomNav |

### Visual Layout
┌─────────────────────────┐
│ Header                  │
├─────────────────────────┤
│ Body                    │
├─────────────────────────┤
│ Footer                  │
└─────────────────────────┘
```

## Patterns by App Type

| App Type | Home Layout | Common Components |
|----------|-------------|-------------------|
| E-commerce | Banner + Grid + BottomNav | ProductCard, Cart, Search |
| Social | Feed + FAB + BottomNav | PostCard, Avatar, Story |
| Utility | List + AppBar | SettingItem, Toggle |
| Media | Carousel + Grid | MediaCard, Player |

## Patterns by Screen Name

### Home / Dashboard
```
Header: AppBar with logo, Search icon
Body: Banner/Carousel, Content grid or list
Footer: BottomNav (4-5 tabs)
```

### Login / Register / Auth
```
Header: Logo centered
Body: Input fields, Action buttons
Footer: Alternative actions (Forgot password, Sign up)
```

### Detail / View / Result
```
Header: AppBar with back button, Title, Action icons
Body: Hero image/content, Details section, Related items
Footer: Action buttons (CTA)
```

### List / Search / Browse
```
Header: AppBar, Search bar, Filter chips
Body: Scrollable list/grid
Footer: BottomNav or none
```

### Profile / Account
```
Header: AppBar with settings icon
Body: Avatar, User info, Menu list
Footer: BottomNav
```

### Settings / Config
```
Header: AppBar with back button, Title
Body: Settings list with toggles
Footer: None
```

### Loading / Process
```
Header: None
Body: Loading animation, Progress indicator, Status text
Footer: Cancel button (optional)
```

### Pick / Select / Choose
```
Header: AppBar with back button, Title
Body: Selection grid/list, Preview area
Footer: Confirm button
```

### History
```
Header: AppBar with back button, Title, Filter
Body: Timeline/list of items
Footer: BottomNav or none
```

## Visual Layout Examples

### Standard with BottomNav
```
┌─────────────────────────┐
│ [←] Title        [⋮][🔍]│  ← AppBar
├─────────────────────────┤
│                         │
│      Main Content       │  ← Body
│                         │
├─────────────────────────┤
│ [🏠] [🔍] [❤️] [👤]     │  ← BottomNav
└─────────────────────────┘
```

### Form Screen
```
┌─────────────────────────┐
│        [Logo]           │  ← Header
├─────────────────────────┤
│  ┌─────────────────┐    │
│  │ Email           │    │
│  └─────────────────┘    │
│  ┌─────────────────┐    │  ← Input Fields
│  │ Password        │    │
│  └─────────────────┘    │
│                         │
│  ┌─────────────────┐    │
│  │    Login        │    │  ← Action Button
│  └─────────────────┘    │
├─────────────────────────┤
│   Forgot? | Sign up     │  ← Alternative Actions
└─────────────────────────┘
```

### Detail Screen
```
┌─────────────────────────┐
│ [←]              [♡][↗]│  ← AppBar with actions
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │    Hero Image       │ │  ← Hero
│ └─────────────────────┘ │
│                         │
│ Title                   │
│ Subtitle | Price        │  ← Details
│                         │
│ Description text...     │
│ ┌─────────────────────┐ │
│ │   Add to Cart       │ │  ← CTA Button
│ └─────────────────────┘ │
└─────────────────────────┘
```
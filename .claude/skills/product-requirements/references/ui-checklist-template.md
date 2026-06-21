# UI Specifications Template (ADA911 Format)

## 5.1 Design System

```
### 5.1 Design System

- **UI Framework:** [Jetpack Compose / SwiftUI / React Native]
- **Theme:** [Theme description]
- **Architecture:** [MVI / MVVM / Clean]
```

## 5.2 Color Palette

Table with Token / Hex / Usage columns.

```
### 5.2 Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| PrimaryBg | #FFF8F0 | Primary background |
| SecondaryBg | #FFF0F0 | Secondary background |
| Surface | #FFFFFF | Cards |
| PrimaryAccent | #B76E79 | Primary accent/CTA |
| PrimaryText | #2D2D2D | Primary text |
| SecondaryText | #8B7E7E | Secondary text |

**Gradients:**
- `CtaGradient`: PrimaryAccent -> SecondaryAccent (horizontal)
```

## 5.3 Spacing

```
### 5.3 Spacing

| Token | Value |
|-------|-------|
| xs | 4.dp |
| sm | 8.dp |
| md | 12.dp |
| lg | 16.dp |
| xl | 20.dp |
| xxl | 24.dp |
| xxxl | 32.dp |
```

## 5.4 Typography

```
### 5.4 Typography

| Style | Font | Size | Weight |
|-------|------|------|--------|
| displayLarge | Serif | 32sp | Normal |
| headlineLarge | Serif | 28sp | Normal |
| titleLarge | Default | 22sp | SemiBold |
| bodyLarge | Default | 16sp | Normal |
| bodyMedium | Default | 14sp | Normal |
| labelLarge | Default | 14sp | Medium |
```

## 5.5+ Screen Layouts

Use ASCII art for each key screen. Show dimensions where relevant.

```
### 5.5 Home Screen Layout

+------------------------------------------+
|  [Icon]      App Title          [Action]  |  <- 56.dp top bar
+------------------------------------------+
|                                          |
|   [Main Content Area]                    |  <- Scrollable
|                                          |
|   +----------------+ +----------------+  |
|   | Feature Card 1 | | Feature Card 2 |  |  <- 80.dp height
|   +----------------+ +----------------+  |
|                                          |
+------------------------------------------+
|   [Tab 1]      [Tab 2]      [Tab 3]     |  <- 80.dp bottom nav
+------------------------------------------+
```

## Guidelines

- Design System: framework, theme, architecture pattern
- Color Palette: use semantic token names, include gradients
- Spacing: define token scale used across app
- Typography: list all text styles with font/size/weight
- Screen Layouts: ASCII art for key screens, annotate dimensions
- No UI checklist checkboxes -- use descriptive layouts instead

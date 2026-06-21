# Navigation Flow Extraction

## Overview

The blueprint generator extracts navigation from multiple PRD sections to create a comprehensive screen flow.

## Extraction Sources

### 1. Main User Flow (Primary)
```markdown
## **1.4 Main User Flow**

**Splash → Login → Home → Browse → Detail → Cart → Checkout → Success**
```

Extracted as `primary` type transitions with highest priority.

### 2. User Stories (User Actions)
```markdown
### **US-01: User Login**
**Acceptance Criteria:**
- User can navigate to registration screen
- After login, redirect to Home screen
```

Patterns detected:
- `navigate to [Screen]`
- `redirect to [Screen]`
- `go to [Screen]`
- `open [Screen]`
- `back to [Screen]`

### 3. Feature Descriptions
```markdown
### **F-01: Product Search**
User can search products from Home screen and view results in Search Results screen.
```

Screens mentioned together imply relationship.

### 4. Inferred Patterns
Common navigation patterns automatically inferred:

| From | To | Trigger |
|------|-----|---------|
| Login | Home | Successful login |
| Login | Register | Create account |
| Register | Home | Successful registration |
| Home | Profile | View profile |
| Profile | Settings | Open settings |
| Home | List screens | Browse items |
| List | Detail | Select item |

## Transition Types

| Type | Description | Visual Style |
|------|-------------|--------------|
| `primary` | Main user flow | Green solid arrow |
| `user-action` | User-triggered | Purple solid arrow |
| `feature` | Feature interaction | Purple solid arrow |
| `inferred` | Pattern-based | Purple dashed arrow |

## Output Format

### Screen Flow Markdown

```markdown
## Screen Transitions

| # | From Screen | To Screen | Trigger/Action | Type |
|---|-------------|-----------|----------------|------|
| 1 | Login | Home | Successful login | primary |
| 2 | Home | Search | Tap search | user-action |
| 3 | Search | Detail | Select item | inferred |

## Screen Relationships

### Home
- **Navigates to:** Profile (View profile), Settings (Open settings)
- **Receives from:** Login (Successful login)
```

### Navigation Map ASCII

```
                    ┌─────────────────┐
                    │  Login          │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Home           │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
  │  Profile        │ │  Search         │ │  Settings       │
  └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Best Practices

1. **Include all flows in PRD** - More explicit = better extraction
2. **Use consistent screen names** - "Login" not "Sign In" / "Log In"
3. **Describe transitions clearly** - "User navigates to X" not "goes to X"
4. **Define entry points** - Which screens are accessible from where

## Handling Missing Information

When PRD lacks explicit navigation:

1. Generator infers from screen names (Login → Home pattern)
2. Groups related screens (List → Detail)
3. Marks as `inferred` type for manual review
4. Designer should verify and adjust

## Manual Adjustments

After generation, review `Screen_Flow.md`:

1. Remove incorrect transitions
2. Add missing transitions
3. Change transition types if needed
4. Update action descriptions

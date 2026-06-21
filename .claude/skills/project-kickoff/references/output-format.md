# Output Format Specification

## File Structure

XLSX file with 3 sheets:

### Sheet 1: Project Overview

| Table        | Rows | Content                                                                            |
|--------------|------|------------------------------------------------------------------------------------|
| OVERVIEW     | 5    | Project Name, PM, Objective, Usecase, Reference App                                |
| USER SEGMENT | 6    | Age, Relationship, Region, Income, Core Need, Core Emotion                         |
| SAMPLE APP   | 6    | Competitor apps with descriptions                                                  |
| DESIGN STYLE | 6    | Persona, Primary Style, Color Palette, Typography, UI Elements, Micro-interactions |

### Sheet 2: Scope & MVP

| Table        | Content                                                 |
|--------------|---------------------------------------------------------|
| SCOPE        | Features with Priority dropdown (Must have / Nice have) |
| OUT OF SCOPE | Items excluded from MVP with reasons                    |

### Sheet 3: Timeline

| Phase           | Output                     |
|-----------------|----------------------------|
| Kickoff & Align | Complete UI/UX Design      |
| Build MVP       | Dev done with all features |
| Test / Validate | Release-ready build        |
| Launch MVP      | Live on Store              |

## Styling

### Colors

| Element    | Color Code | Description                 |
|------------|------------|-----------------------------|
| Header     | #2E75B6    | Blue background, white text |
| Sub-header | #D9E2F3    | Light blue background       |
| Content    | #FFFFFF    | White background            |
| Must have  | #C6EFCE    | Green background            |
| Nice have  | #FFEB9C    | Yellow background           |

### Typography

- Header: Bold, 14pt
- Sub-header: Bold, 11pt
- Content: Regular, 11pt, wrap text enabled

### Column Widths

| Sheet   | Column A | Column B | Column C |
|---------|----------|----------|----------|
| Sheet 1 | 25       | 80       | -        |
| Sheet 2 | 30       | 60       | 15       |
| Sheet 3 | 20       | 15       | 40       |

## Default Features

Always include in SCOPE:

**Must have:**
- Remote Config - Fetch config from Firebase
- Event Tracking - Track user behavior (Firebase Analytics)
- Multiple Language - Multi-language support (VI, EN, ...)
- First Open SDK - Show ads on first app open
- Service in house - Processing service (self-hosted or API)

**Nice have:**
- Ad in app - Banner, interstitial, rewarded ads
- Subscription - Premium package (unlimited, ad-free)

## Default Out of Scope

- CMS Management - Develop after user base established
- Social Features - Not in MVP scope
- Cloud Sync - Complex, develop later

## Filename Convention

```
AAPxxx_<Idea_Name>_Kickoff.xlsx
```

Example: `AAPxxx_AI_Photo_Editor_Kickoff.xlsx`

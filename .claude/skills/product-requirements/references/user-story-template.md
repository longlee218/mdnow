# User Story Template (ADA911 Format)

## Format

Group user stories by feature domain. Use table format with 4 columns.

```
### 2.X [Feature Domain Name]

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|-------------------|
| US-010 | As a user, I want to [action] so that [benefit] | P0 | - [Criterion 1]<br>- [Criterion 2]<br>- [Criterion 3] |
| US-011 | As a user, I want to [action] so that [benefit] | P1 | - [Criterion 1]<br>- [Criterion 2] |
```

## Priority Levels

| Priority | Description |
|----------|-------------|
| P0 | Core functionality, must have for release |
| P1 | Important but not blocking release |
| P2 | Nice to have, can defer |

## ID Convention

- US-0XX: Group by feature (US-010-019 for Feature 1, US-020-029 for Feature 2, etc.)
- Allows inserting new stories without renumbering

## Acceptance Criteria Guidelines

- Use `<br>` for line breaks within table cells
- Start each criterion with `-`
- Be specific and testable
- Include happy path and edge cases
- Cover UI elements and interactions

## Example

```
### 2.1 Onboarding & First Launch

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|-------------------|
| US-001 | As a new user, I want to select my preferred language on first launch so that the app displays in my language | P0 | - Language selection screen shown on first launch only<br>- 14 languages supported<br>- Proceeds to onboarding after selection |
| US-002 | As a new user, I want to see a brief onboarding tour so that I understand the app's key features | P0 | - Onboarding carousel shown after language selection<br>- Skip button available<br>- Proceeds to Home screen after completion |

### 2.2 AI Generate

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|-------------------|
| US-020 | As a user, I want to apply AI effects to my photo so that I can create unique content | P0 | - Select photo from gallery<br>- Choose style from gallery<br>- Cloud processing with progress display<br>- Result displayed with save/share options |
```

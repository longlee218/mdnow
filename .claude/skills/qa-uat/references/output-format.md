# QA & UAT Output Format

## Document Structure

```markdown
# QA & UAT Test Cases
## Project: {Project Name}
## Code: {AAPxxx}
## Version: 1.0
## Date: {YYYY-MM-DD}

---

## 1. Test Overview

| Field | Value |
|-------|-------|
| Project | {name} |
| Code | {AAPxxx} |
| PRD Version | {version} |
| Test Scope | {list of features} |
| Environments | Android 10+, iOS 15+ |
| Prerequisites | {setup requirements} |

---

## 2. Test Cases by Feature

### 🔐 {Feature 1: Authentication}

| TC ID | Type | Scenario | Steps | Expected Result | Priority |
|-------|------|----------|-------|-----------------|----------|
| AUTH-F01 | Functional | ... | ... | ... | Critical |
| AUTH-F02 | Functional | ... | ... | ... | High |
| AUTH-U01 | UI/UX | ... | ... | ... | Medium |
| AUTH-NAV01 | Navigation | ... | ... | ... | High |
| AUTH-NET01 | Network | ... | ... | ... | High |
| AUTH-INT01 | Interrupt | ... | ... | ... | Medium |
| AUTH-LOC01 | Localization | ... | ... | ... | Medium |
| AUTH-UAT01 | UAT | ... | ... | ... | High |

### 🏠 {Feature 2: Home/Dashboard}

| TC ID | Type | Scenario | Steps | Expected Result | Priority |
|-------|------|----------|-------|-----------------|----------|
| HOME-F01 | Functional | ... | ... | ... | Critical |
| ... | ... | ... | ... | ... | ... |

### 👤 {Feature 3: Profile}
...

### 📝 {Feature N: ...}
...

---

## 3. Regression Checklist

Core features to test every release:

| ID | Feature | Test Scope | Status |
|----|---------|------------|--------|
| REG-001 | Authentication | Login, Logout, Session | ⬜ |
| REG-002 | Core Feature A | Main functionality | ⬜ |
| REG-003 | Core Feature B | Main functionality | ⬜ |
| REG-004 | Data Sync | Upload, Download | ⬜ |
| REG-005 | Push Notifications | Receive, Tap action | ⬜ |

---

## 4. UAT Scenarios

End-to-end user journeys:

| UAT ID | Scenario | User Journey | Pass Criteria | Status |
|--------|----------|--------------|---------------|--------|
| UAT-001 | First-time user | Install → Register → Onboarding → First action | Complete < 3 min | ⬜ |
| UAT-002 | Daily usage | Open → Check updates → Use core feature | Smooth < 30 sec | ⬜ |
| UAT-003 | Power user | Multiple features in one session | No crashes, data consistent | ⬜ |

---

## 5. Test Summary

| Category | Total | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Functional | X | X | X | X | X |
| UI/UX | X | X | X | X | X |
| Navigation | X | X | X | X | X |
| Network | X | X | X | X | X |
| Interrupt | X | X | X | X | X |
| Localization | X | X | X | X | X |
| Regression | X | - | - | - | - |
| UAT | X | - | - | - | - |
| **Total** | **X** | **X** | **X** | **X** | **X** |
```

## Test ID Convention

```
{FEATURE}-{TYPE}{NUMBER}

Feature prefix:
- AUTH = Authentication
- HOME = Home/Dashboard
- PROF = Profile
- SET = Settings
- {XXX} = Custom feature

Type codes:
- F = Functional
- U = UI/UX
- NAV = Navigation
- NET = Network
- INT = Interrupt
- LOC = Localization
- REG = Regression
- UAT = UAT

Examples:
- AUTH-F01 = Authentication Functional test 01
- HOME-NET03 = Home Network test 03
- PROF-UAT01 = Profile UAT test 01
```

## Priority Levels

| Priority | Description | Must fix before |
|----------|-------------|-----------------|
| Critical | App crash, data loss, security | Release |
| High | Core feature broken | Release |
| Medium | Feature works but has issues | Next sprint |
| Low | Minor issues, cosmetic | Backlog |

## Test Types Detail

### Functional
- Happy path (normal usage)
- Input validation
- Business logic
- Error handling

### UI/UX (Basic)
- Color scheme matches design
- Layout structure correct
- Text readable
- Touch targets adequate size

### Navigation
- Screen transitions correct
- Back button behavior
- Deep links work
- Tab/bottom nav state

### Network
- Offline mode handling
- Slow network (loading states)
- Network switch (WiFi ↔ Mobile)
- Timeout/retry behavior

### Interrupt
- Incoming call during action
- Push notification received
- App background → foreground
- Low battery warning
- Screen rotation

### Localization
- All text translated
- No text overflow/truncation
- Date/time format correct
- Currency format correct
- RTL layout (if applicable)

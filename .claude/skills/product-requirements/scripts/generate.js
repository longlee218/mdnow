#!/usr/bin/env node
/**
 * PRD Generator - Product Requirements Document
 * Format: ADA911 standard (11 sections + appendix)
 *
 * Usage:
 *   node generate.js --name "Product Name" --code "AAPxxx" --description "..." --screens "Screen1,Screen2"
 *   node generate.js --name "..." --code "..." --versions '[{"version":1,"features":[...]},...]' --targetVersion 1
 */

const fs = require('fs');
const path = require('path');

function parseArgs() {
  const args = process.argv.slice(2);
  const result = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].replace(/^--/, '');
      result[key] = args[i + 1] || '';
      i++;
    }
  }
  return result;
}

function sanitizeFilename(str) {
  return str.replace(/[^a-zA-Z0-9\- ]/g, '').replace(/\s+/g, '-');
}

function today() {
  return new Date().toISOString().split('T')[0];
}

function generatePRD(input) {
  const { name, code, description, platform = 'Android' } = input;
  const screens = input.screens ? input.screens.split(',').map(s => s.trim()) : ['Home', 'Detail', 'Settings'];
  const features = input.features ? input.features.split(',').map(f => f.trim()) : [];

  let versions = [];
  const targetVersion = parseInt(input.targetVersion) || 1;
  if (input.versions) {
    try { versions = JSON.parse(input.versions); } catch (e) { /* ignore */ }
  }

  const targetVer = versions.find(v => v.version === targetVersion);
  const targetFeatures = targetVer ? (targetVer.features || []) : [];
  const otherVersions = versions.filter(v => v.version !== targetVersion);

  // --- Section generators ---

  const userStoriesSection = generateUserStories(screens);
  const featureSpecsSection = generateFeatureSpecs(features, targetFeatures);
  const screenFlowsSection = generateScreenFlows(screens);
  const uiSpecsSection = generateUISpecs(screens);
  const remoteConfigSection = generateRemoteConfig(features);
  const nfrSection = generateNFR(platform);
  const apiSection = generateAPISpecs();
  const dataModelsSection = generateDataModels();
  const analyticsSection = generateAnalyticsEvents();
  const releaseSection = generateReleasePlan(targetVersion, targetFeatures, otherVersions, code);
  const appendixSection = generateAppendix(screens, platform);

  // --- Scope summary ---
  const featureNames = targetFeatures.length > 0
    ? targetFeatures.map(f => `- ${f.name}`).join('\n')
    : features.length > 0
      ? features.map(f => `- ${f}`).join('\n')
      : '- [List features here]';

  const prd = `# Product Requirements Document (PRD)

**Project Name:** ${name}
**Document ID:** ${code}-PRD
**Version:** ${targetVersion}.0
**Date:** ${today()}
**Status:** Draft
**Platform:** ${platform}

---

## Table of Contents

1. [Overview](#1-overview)
2. [User Stories](#2-user-stories)
3. [Feature Specifications](#3-feature-specifications)
4. [Screen Flows & Navigation](#4-screen-flows--navigation)
5. [UI Specifications](#5-ui-specifications)
6. [Remote Configuration](#6-remote-configuration)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [API Specifications](#8-api-specifications)
9. [Data Models](#9-data-models)
10. [Analytics Events](#10-analytics-events)
11. [Release Plan](#11-release-plan)

---

## 1. Overview

### 1.1 Product Vision

${description}

### 1.2 Scope

The app ships with **[N] active features** across [N] flows.

**Features:**
${featureNames}

### 1.3 Assumptions

- Users have ${platform === 'Android' ? 'Android 7.0+ (API 24+)' : 'iOS 16+'} smartphones
- Minimum 2GB RAM for on-device processing
- Internet connection required for cloud features
- [Add project-specific assumptions]

---

${userStoriesSection}

---

${featureSpecsSection}

---

${screenFlowsSection}

---

${uiSpecsSection}

---

${remoteConfigSection}

---

${nfrSection}

---

${apiSection}

---

${dataModelsSection}

---

${analyticsSection}

---

${releaseSection}

---

${appendixSection}

---

**Document Owner**: Product Team
**Last Review**: ${today()}
**Next Review**: [+30 days]
`;

  return prd;
}

// --- Section: User Stories ---

function generateUserStories(screens) {
  const stories = screens.map((screen, idx) => {
    const id = String((idx + 1) * 10).padStart(3, '0');
    return `### 2.${idx + 1} ${screen}

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|-------------------|
| US-${id} | As a user, I want to [action in ${screen}] so that [benefit] | P0 | - [Criterion 1]<br>- [Criterion 2]<br>- [Criterion 3] |`;
  }).join('\n\n');

  return `## 2. User Stories

${stories}`;
}

// --- Section: Feature Specifications ---

function generateFeatureSpecs(featureNames, targetFeatures) {
  const featureList = targetFeatures.length > 0 ? targetFeatures : featureNames.map(f => ({ name: f }));

  if (featureList.length === 0) {
    return `## 3. Feature Specifications

### 3.1 F1 -- [Feature Name]

| Property | Detail |
|----------|--------|
| ID | \`feature_id\` |
| Processing | Local / Cloud |
| Premium | Yes / No |
| Input | [Input description] |
| Output | [Output description] |`;
  }

  const specs = featureList.map((f, idx) => {
    const fName = typeof f === 'string' ? f : f.name;
    return `### 3.${idx + 1} F${idx + 1} -- ${fName}

| Property | Detail |
|----------|--------|
| ID | \`${fName.toLowerCase().replace(/\s+/g, '_')}\` |
| Processing | [Local / Cloud] |
| Premium | [Yes / No] |
| Input | [Input description] |
| Output | [Output description] |

| Component | Description |
|-----------|-------------|
| [Component 1] | [Description] |
| [Component 2] | [Description] |`;
  }).join('\n\n');

  return `## 3. Feature Specifications

### 3.0 Overview

All features follow a common flow pattern:

\`\`\`
[Configure] --> [Process] --> [Display result]
\`\`\`

${specs}`;
}

// --- Section: Screen Flows & Navigation ---

function generateScreenFlows(screens) {
  const activityMap = screens.map((s, idx) => {
    return `| ${idx + 1} | \`${s.replace(/\s+/g, '')}Screen\` | \`presentation.${s.toLowerCase().replace(/\s+/g, '')}\` | ${s} |`;
  }).join('\n');

  const navFlow = screens.map(s => `[${s}]`).join(' → ');

  return `## 4. Screen Flows & Navigation

### 4.1 Activity Map

All screens use [UI framework].

| # | Screen | Package Path | Description |
|---|--------|-------------|-------------|
${activityMap}

### 4.2 App Navigation Structure

\`\`\`
App Launch
    |
    +--> [Splash]
           |
           +--> First Launch: [Onboarding] --> [Home]
           |
           +--> Returning User: --> [Home]
                                       |
           +---------------------------+
           |
      [Main Tabs / Screens]
           |
      [Feature Screens]
\`\`\`

### 4.3 Key User Flows

#### Flow 1: [Primary Flow Name]

\`\`\`
${navFlow}
  --> [END]
\`\`\`

#### Flow 2: [Secondary Flow Name]

\`\`\`
[Screen A]
  --> [Screen B]
  --> [Screen C]
  --> [END]
\`\`\``;
}

// --- Section: UI Specifications ---

function generateUISpecs(screens) {
  const screenLayouts = screens.slice(0, 3).map((s, idx) => {
    return `### 5.${idx + 5} ${s} Screen Layout

\`\`\`
+------------------------------------------+
|  [<]          ${s.padEnd(20)}    [Action] |
+------------------------------------------+
|                                          |
|   [Main content area]                    |
|                                          |
|   [Components / Cards / Lists]           |
|                                          |
+------------------------------------------+
|   [Bottom Navigation / Actions]          |
+------------------------------------------+
\`\`\``;
  }).join('\n\n');

  return `## 5. UI Specifications

### 5.1 Design System

- **UI Framework:** [Jetpack Compose / SwiftUI / React Native]
- **Theme:** [Theme description]
- **Architecture:** [MVI / MVVM / Clean]

### 5.2 Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| PrimaryBg | #[hex] | Primary background |
| SecondaryBg | #[hex] | Secondary background |
| Surface | #FFFFFF | Cards |
| PrimaryAccent | #[hex] | Primary accent/CTA |
| SecondaryAccent | #[hex] | Secondary accent |
| PrimaryText | #[hex] | Primary text |
| SecondaryText | #[hex] | Secondary text |
| Divider | #[hex] | Dividers |
| Success | #22C55E | Success states |
| Error | #EF4444 | Error states |

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

### 5.4 Typography

| Style | Font | Size | Weight |
|-------|------|------|--------|
| displayLarge | [Font] | 32sp | Normal |
| headlineLarge | [Font] | 28sp | Normal |
| headlineMedium | [Font] | 24sp | Normal |
| titleLarge | [Font] | 22sp | SemiBold |
| titleMedium | [Font] | 18sp | Medium |
| bodyLarge | [Font] | 16sp | Normal |
| bodyMedium | [Font] | 14sp | Normal |
| bodySmall | [Font] | 12sp | Normal |
| labelLarge | [Font] | 14sp | Medium |
| labelMedium | [Font] | 12sp | Medium |

${screenLayouts}`;
}

// --- Section: Remote Configuration ---

function generateRemoteConfig(features) {
  const featureFlags = features.length > 0
    ? features.map(f => {
        const key = `feature_${f.toLowerCase().replace(/\s+/g, '_')}_enabled`;
        return `| \`${key}\` | Boolean | true | Enable/disable ${f} |`;
      }).join('\n')
    : '| `feature_[name]_enabled` | Boolean | true | Enable/disable [feature] |';

  return `## 6. Remote Configuration

### 6.1 Remote Config Overview

Remote configuration via Firebase Remote Config allows modification of app behavior, feature flags, and content without requiring an app update.

### 6.2 Feature Flags

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
${featureFlags}

### 6.3 Monetization Config

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| \`ads_per_action\` | Integer | 1 | Ads required per action |
| \`daily_free_limit\` | Integer | 3 | Free actions per day |
| \`show_native_ad\` | Boolean | true | Show native ad on screens |

### 6.4 Processing Config

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| \`processing_timeout_free\` | Integer | 120 | Timeout for free users (seconds) |
| \`processing_timeout_premium\` | Integer | 300 | Timeout for premium users (seconds) |
| \`retry_count\` | Integer | 2 | Number of retries on failure |`;
}

// --- Section: Non-Functional Requirements ---

function generateNFR(platform) {
  const compatTable = platform === 'Android'
    ? `| Property | Requirement |
|----------|-------------|
| Platform | Android only |
| Min Android Version | Android 7.0 (API 24)+ |
| Target SDK | 36 |
| Compile SDK | 36 |
| Min RAM | 2GB |
| Min Storage | 200MB (app) + space for media |
| Screen sizes | Phone form factors |
| Orientation | Portrait only |`
    : `| Property | Requirement |
|----------|-------------|
| Platform | iOS only |
| Min iOS Version | iOS 16+ |
| Min RAM | 2GB |
| Min Storage | 200MB (app) + space for media |
| Screen sizes | iPhone form factors |
| Orientation | Portrait only |`;

  return `## 7. Non-Functional Requirements

### 7.1 Performance

| Requirement | Target |
|-------------|--------|
| App cold start time | <3 seconds |
| App warm start time | <1 second |
| Screen navigation | <300ms |
| Cloud processing | <2 minutes |
| Media upload | <5 seconds |
| Image loading | <2 seconds |
| UI frame rate | 60fps |
| Memory usage | <300MB during processing |

### 7.2 Compatibility

${compatTable}

### 7.3 Security

| Requirement | Implementation |
|-------------|---------------|
| API Communication | HTTPS/TLS for all API calls |
| Media Upload | Uploaded via presigned URL, encrypted in transit |
| Privacy Compliance | Privacy policy and terms accessible from Settings |
| Local Storage | [SharedPreferences/UserDefaults] for config, [Room/CoreData] for records |
| Build Security | [ProGuard/R8 / App Store] obfuscation in release builds |

### 7.4 Reliability & Availability

| Requirement | Target |
|-------------|--------|
| API Uptime | 99.9% |
| Crash-free sessions | >99.5% |
| Processing success rate | >95% |
| Offline capability | [Define offline features] |
| Graceful degradation | Clear error messages; retry mechanism |

### 7.5 Localization

| Requirement | Implementation |
|-------------|---------------|
| Languages Supported | [Number] ([list language codes]) |
| String Resources | All user-facing strings in resource files |
| RTL Support | [Yes / No] |
| Date/Time Formats | Locale-aware formatting |`;
}

// --- Section: API Specifications ---

function generateAPISpecs() {
  return `## 8. API Specifications

### 8.1 API Overview

| Service | Base URL | Method |
|---------|---------|--------|
| [Service 1] | \`api.example.com/v1/...\` | GET/POST |
| [Service 2] | \`api.example.com/v1/...\` | POST |

### 8.2 [Endpoint 1 Name]

\`\`\`
[METHOD] /api/v1/[endpoint]

Request Body:
{
  "param1": "value1",
  "param2": "value2"
}

Response:
{
  "statusCode": 200,
  "message": "success",
  "data": {
    "key": "value"
  }
}
\`\`\`

### 8.3 Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid parameters |
| 401 | Unauthorized |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Service unavailable |`;
}

// --- Section: Data Models ---

function generateDataModels() {
  return `## 9. Data Models

### 9.1 [Primary Model]

\`\`\`kotlin
@Serializable
data class [ModelName](
    val id: String,
    val name: String,
    // Add fields
)
\`\`\`

### 9.2 [State Model]

\`\`\`kotlin
data class [ScreenState](
    val isLoading: Boolean = true,
    val data: List<[Model]> = emptyList(),
    val error: String? = null
) : MviViewState
\`\`\`

### 9.3 [Navigation / Destination]

\`\`\`kotlin
sealed interface Destination : NavKey {
    data object Home : Destination
    data object Settings : Destination
    // Add destinations
}
\`\`\``;
}

// --- Section: Analytics Events ---

function generateAnalyticsEvents() {
  return `## 10. Analytics Events

### 10.1 App Lifecycle Events

| Event Name | Trigger | Key Properties |
|------------|---------|---------------|
| \`app_launched\` | App opened | \`source\`, \`session_number\` |
| \`onboarding_started\` | Onboarding begins | \`is_first_launch\` |
| \`onboarding_completed\` | Onboarding finished | \`screens_viewed\`, \`skipped\` |

### 10.2 Navigation Events

| Event Name | Trigger | Key Properties |
|------------|---------|---------------|
| \`screen_viewed\` | Screen displayed | \`screen_name\` |
| \`tab_changed\` | Tab switched | \`from_tab\`, \`to_tab\` |
| \`feature_tapped\` | Feature item tapped | \`feature_id\` |

### 10.3 Core Feature Events

| Event Name | Trigger | Key Properties |
|------------|---------|---------------|
| \`action_started\` | Primary action initiated | \`feature_id\`, \`params\` |
| \`action_completed\` | Primary action succeeded | \`feature_id\`, \`duration_ms\` |
| \`action_failed\` | Primary action failed | \`feature_id\`, \`error_type\` |

### 10.4 Export & Sharing Events

| Event Name | Trigger | Key Properties |
|------------|---------|---------------|
| \`result_viewed\` | Result screen displayed | \`feature_id\` |
| \`content_saved\` | Content saved to device | \`feature_id\`, \`file_size_kb\` |
| \`content_shared\` | Share action initiated | \`feature_id\` |

### 10.5 Monetization Events

| Event Name | Trigger | Key Properties |
|------------|---------|---------------|
| \`paywall_shown\` | Subscription screen displayed | \`placement\` |
| \`subscription_started\` | Purchase initiated | \`plan\` |
| \`subscription_completed\` | Purchase confirmed | \`plan\`, \`transaction_id\` |
| \`ad_impression\` | Ad displayed | \`ad_type\` |`;
}

// --- Section: Release Plan ---

function generateReleasePlan(targetVersion, targetFeatures, otherVersions, code) {
  const futureSection = otherVersions.length > 0
    ? `### 11.2 Next Release (v${otherVersions[0].version}.0) -- Planned

#### Potential Features
${(otherVersions[0].features || []).map(f => `- ${f.name}${f.desc ? ` (${f.desc})` : ''}`).join('\n') || '- [TBD]'}

#### Improvements
- Performance optimizations based on v${targetVersion}.0 analytics
- UI refinements based on user feedback
`
    : `### 11.2 Next Release -- Planned

#### Potential Features
- [Feature 1]
- [Feature 2]

#### Improvements
- Performance optimizations based on v${targetVersion}.0 analytics
- UI refinements based on user feedback
`;

  return `## 11. Release Plan

### 11.1 Current Release (v${targetVersion}.0)

#### Features Included
${targetFeatures.length > 0
    ? targetFeatures.map(f => `- ${f.name}`).join('\n')
    : '- [List features included in this release]'}

#### Quality Gates
- All P0 user stories pass acceptance criteria
- Crash-free rate >99.5%
- Performance targets met
- Store review compliance verified
- Privacy policy and terms of service finalized

${futureSection}
### 11.3 Version History

| Version | Date | Changes |
|---------|------|---------|
| ${targetVersion}.0 | ${today()} | Initial PRD |`;
}

// --- Section: Appendix ---

function generateAppendix(screens, platform) {
  const screenFiles = screens.map(s => {
    const pkg = s.toLowerCase().replace(/\s+/g, '');
    return `├── app/.../${pkg}/${s.replace(/\s+/g, '')}Screen.kt`;
  }).join('\n');

  return `## Appendix

### A.1 Key Files Reference

\`\`\`
Core Screens:
${screenFiles}

Design System:
├── core/designsystem/theme/Color.kt
├── core/designsystem/theme/Type.kt
├── core/designsystem/theme/Spacing.kt
└── core/designsystem/res/values/strings.xml

Navigation:
├── app/.../navigation/AppNavigation.kt
└── app/.../navigation/destination/Destination.kt
\`\`\`

### A.2 Third-Party Integrations

| SDK | Version | Purpose |
|-----|---------|---------|
| [SDK 1] | [version] | [purpose] |
| [SDK 2] | [version] | [purpose] |

### A.3 Build Configuration

| Property | Value |
|----------|-------|
| Application ID | \`[package.id]\` |
| Min SDK | [min] |
| Target SDK | [target] |
| Compile SDK | [compile] |
| Build Types | debug, release |`;
}

// --- CLI ---

const args = parseArgs();

if (!args.name || !args.code) {
  console.log(`
PRD Generator (ADA911 format)

Usage: node generate.js --name "Product Name" --code "AAPxxx" [options]

Required:
  --name        Product name
  --code        Product code (AAPxxx)

Optional:
  --description Product description
  --screens     Comma-separated screen list
  --features    Comma-separated feature list
  --platform    Platform (default: Android)
  --output      Output directory (default: ./)
  --versions    JSON array of versions from kickoff
  --targetVersion  Version to focus on (default: 1/MVP)

Example:
  node generate.js --name "AI Family Archive" --code "AAP857" \\
    --description "AI photo restoration app" \\
    --screens "Home,Pick Photo,Prepare,Loading,Result,History,Settings" \\
    --targetVersion 1
`);
  process.exit(1);
}

const prd = generatePRD(args);
const outputDir = args.output || process.cwd();
const targetVer = parseInt(args.targetVersion) || 1;
const filename = `${args.code}_${sanitizeFilename(args.name)}_PRD.md`;
const filepath = path.join(outputDir, filename);

fs.writeFileSync(filepath, prd);

console.log(`\u2705 PRD created: ${filepath}`);
console.log(`\ud83d\udccc Focus: Version ${targetVer}${targetVer === 1 ? ' (MVP)' : ''}`);
console.log(`\ud83d\udcc4 Sections: 11 + Appendix (ADA911 format)`);
console.log(`\n\u26a0\ufe0f  This is a TEMPLATE. Agent should fill in detailed content.`);

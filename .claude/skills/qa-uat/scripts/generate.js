#!/usr/bin/env node
/**
 * QA & UAT Document Generator
 * Generates test cases from PRD for mobile app projects
 */

const fs = require('fs');
const path = require('path');

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const params = {};
  
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      const value = args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true;
      params[key] = value;
      if (value !== true) i++;
    }
  }
  
  return params;
}

// Extract features from PRD content
function extractFeatures(prdContent) {
  const features = [];
  
  // Look for ## headers that indicate features/screens
  const featurePattern = /^##\s+(?:\d+\.\s+)?(.+?)(?:\s*\(.*\))?$/gm;
  let match;
  
  while ((match = featurePattern.exec(prdContent)) !== null) {
    const name = match[1].trim();
    // Skip common non-feature headers
    if (!['Overview', 'Introduction', 'Summary', 'Revision History', 'Table of Contents', 'References'].includes(name)) {
      features.push({
        name: name,
        prefix: generatePrefix(name)
      });
    }
  }
  
  // If no features found, create default structure
  if (features.length === 0) {
    features.push(
      { name: 'Authentication', prefix: 'AUTH' },
      { name: 'Home', prefix: 'HOME' },
      { name: 'Main Feature', prefix: 'MAIN' },
      { name: 'Settings', prefix: 'SET' }
    );
  }
  
  return features;
}

// Generate prefix from feature name
function generatePrefix(name) {
  const prefixMap = {
    'authentication': 'AUTH',
    'login': 'AUTH',
    'register': 'AUTH',
    'sign up': 'AUTH',
    'home': 'HOME',
    'dashboard': 'HOME',
    'profile': 'PROF',
    'settings': 'SET',
    'search': 'SRCH',
    'detail': 'DTL',
    'list': 'LIST',
    'payment': 'PAY',
    'checkout': 'PAY',
    'notification': 'NOTI',
    'chat': 'CHAT',
    'message': 'MSG',
    'upload': 'UPL',
    'download': 'DWN',
    'share': 'SHR',
    'favorite': 'FAV',
    'bookmark': 'BMK',
    'history': 'HIST',
    'onboarding': 'ONB',
    'splash': 'SPL'
  };
  
  const lower = name.toLowerCase();
  for (const [key, prefix] of Object.entries(prefixMap)) {
    if (lower.includes(key)) return prefix;
  }
  
  // Generate from first letters
  return name.split(/\s+/).map(w => w[0]).join('').toUpperCase().slice(0, 4);
}

// Generate test cases for a feature
function generateTestCases(feature) {
  const { name, prefix } = feature;
  const testCases = [];
  let counter = { F: 1, U: 1, NAV: 1, NET: 1, INT: 1, LOC: 1, UAT: 1 };
  
  // Functional tests
  testCases.push({
    id: `${prefix}-F${String(counter.F++).padStart(2, '0')}`,
    type: 'Functional',
    scenario: `${name} - Happy path`,
    steps: `1. Navigate to ${name}\n2. Perform main action\n3. Verify result`,
    expected: `${name} works as expected`,
    priority: 'Critical'
  });
  
  testCases.push({
    id: `${prefix}-F${String(counter.F++).padStart(2, '0')}`,
    type: 'Functional',
    scenario: `${name} - Input validation`,
    steps: `1. Enter invalid data\n2. Submit`,
    expected: 'Show validation error message',
    priority: 'High'
  });
  
  testCases.push({
    id: `${prefix}-F${String(counter.F++).padStart(2, '0')}`,
    type: 'Functional',
    scenario: `${name} - Error handling`,
    steps: `1. Trigger error condition\n2. Observe behavior`,
    expected: 'Show user-friendly error, no crash',
    priority: 'High'
  });
  
  // UI/UX tests
  testCases.push({
    id: `${prefix}-U${String(counter.U++).padStart(2, '0')}`,
    type: 'UI/UX',
    scenario: `${name} - Layout structure`,
    steps: `1. Open ${name} screen\n2. Verify layout`,
    expected: 'Layout matches design, elements aligned',
    priority: 'Medium'
  });
  
  testCases.push({
    id: `${prefix}-U${String(counter.U++).padStart(2, '0')}`,
    type: 'UI/UX',
    scenario: `${name} - Color scheme`,
    steps: `1. Check colors in light mode\n2. Check colors in dark mode`,
    expected: 'Colors match design system',
    priority: 'Medium'
  });
  
  // Navigation tests
  testCases.push({
    id: `${prefix}-NAV${String(counter.NAV++).padStart(2, '0')}`,
    type: 'Navigation',
    scenario: `${name} - Screen transition`,
    steps: `1. Navigate to ${name}\n2. Tap back`,
    expected: 'Correct screen transition, back works',
    priority: 'High'
  });
  
  testCases.push({
    id: `${prefix}-NAV${String(counter.NAV++).padStart(2, '0')}`,
    type: 'Navigation',
    scenario: `${name} - Deep link`,
    steps: `1. Open deep link to ${name}\n2. Verify screen`,
    expected: 'Opens correct screen with data',
    priority: 'Medium'
  });
  
  // Network tests
  testCases.push({
    id: `${prefix}-NET${String(counter.NET++).padStart(2, '0')}`,
    type: 'Network',
    scenario: `${name} - Offline mode`,
    steps: `1. Turn off network\n2. Access ${name}`,
    expected: 'Show offline message or cached data',
    priority: 'High'
  });
  
  testCases.push({
    id: `${prefix}-NET${String(counter.NET++).padStart(2, '0')}`,
    type: 'Network',
    scenario: `${name} - Slow network`,
    steps: `1. Simulate slow network\n2. Perform action`,
    expected: 'Show loading state, no timeout crash',
    priority: 'Medium'
  });
  
  // Interrupt tests
  testCases.push({
    id: `${prefix}-INT${String(counter.INT++).padStart(2, '0')}`,
    type: 'Interrupt',
    scenario: `${name} - Incoming call`,
    steps: `1. Start action in ${name}\n2. Receive call\n3. Return to app`,
    expected: 'State preserved, no data loss',
    priority: 'Medium'
  });
  
  testCases.push({
    id: `${prefix}-INT${String(counter.INT++).padStart(2, '0')}`,
    type: 'Interrupt',
    scenario: `${name} - Background/Foreground`,
    steps: `1. Open ${name}\n2. Go to background\n3. Return`,
    expected: 'Screen state preserved',
    priority: 'Medium'
  });
  
  // Localization tests
  testCases.push({
    id: `${prefix}-LOC${String(counter.LOC++).padStart(2, '0')}`,
    type: 'Localization',
    scenario: `${name} - Text translation`,
    steps: `1. Change language\n2. Open ${name}`,
    expected: 'All text translated, no overflow',
    priority: 'Medium'
  });
  
  // UAT
  testCases.push({
    id: `${prefix}-UAT${String(counter.UAT++).padStart(2, '0')}`,
    type: 'UAT',
    scenario: `${name} - User journey`,
    steps: `Complete typical user flow in ${name}`,
    expected: 'Smooth experience, task completed easily',
    priority: 'High'
  });
  
  return testCases;
}

// Get feature emoji
function getFeatureEmoji(name) {
  const emojiMap = {
    'auth': '🔐',
    'login': '🔐',
    'register': '📝',
    'home': '🏠',
    'dashboard': '📊',
    'profile': '👤',
    'settings': '⚙️',
    'search': '🔍',
    'payment': '💳',
    'notification': '🔔',
    'chat': '💬',
    'message': '✉️',
    'upload': '📤',
    'download': '📥',
    'share': '🔗',
    'favorite': '❤️',
    'history': '📜',
    'list': '📋',
    'detail': '📄'
  };
  
  const lower = name.toLowerCase();
  for (const [key, emoji] of Object.entries(emojiMap)) {
    if (lower.includes(key)) return emoji;
  }
  return '📱';
}

// Generate markdown document
function generateDocument(params, features) {
  const { name, code } = params;
  const date = new Date().toISOString().split('T')[0];
  
  let md = `# QA & UAT Test Cases

## Project: ${name}
## Code: ${code}
## Version: 1.0
## Date: ${date}

---

## 1. Test Overview

| Field | Value |
|-------|-------|
| Project | ${name} |
| Code | ${code} |
| PRD Version | 1.0 |
| Test Scope | ${features.map(f => f.name).join(', ')} |
| Environments | Android 10+, iOS 15+ |
| Prerequisites | Test account, test data |

---

## 2. Test Cases by Feature

`;

  // Generate test cases for each feature
  let totalTests = { Functional: 0, 'UI/UX': 0, Navigation: 0, Network: 0, Interrupt: 0, Localization: 0, UAT: 0 };
  let totalByPriority = { Critical: 0, High: 0, Medium: 0, Low: 0 };
  
  for (const feature of features) {
    const emoji = getFeatureEmoji(feature.name);
    const testCases = generateTestCases(feature);
    
    md += `### ${emoji} ${feature.name}\n\n`;
    md += `| TC ID | Type | Scenario | Steps | Expected Result | Priority |\n`;
    md += `|-------|------|----------|-------|-----------------|----------|\n`;
    
    for (const tc of testCases) {
      const steps = tc.steps.replace(/\n/g, '<br>');
      md += `| ${tc.id} | ${tc.type} | ${tc.scenario} | ${steps} | ${tc.expected} | ${tc.priority} |\n`;
      
      totalTests[tc.type] = (totalTests[tc.type] || 0) + 1;
      totalByPriority[tc.priority] = (totalByPriority[tc.priority] || 0) + 1;
    }
    
    md += `\n`;
  }

  // Regression checklist
  md += `---

## 3. Regression Checklist

Core features to test every release:

| ID | Feature | Test Scope | Status |
|----|---------|------------|--------|
`;

  features.forEach((feature, index) => {
    md += `| REG-${String(index + 1).padStart(3, '0')} | ${feature.name} | Core functionality | ⬜ |\n`;
  });

  // UAT Scenarios
  md += `
---

## 4. UAT Scenarios

End-to-end user journeys:

| UAT ID | Scenario | User Journey | Pass Criteria | Status |
|--------|----------|--------------|---------------|--------|
| UAT-E2E-001 | First-time user | Install → Register → Onboarding → First action | Complete < 3 min | ⬜ |
| UAT-E2E-002 | Returning user | Open → Login → Use main feature | Complete < 1 min | ⬜ |
| UAT-E2E-003 | Daily usage | Open → Check updates → Perform actions → Close | Smooth experience | ⬜ |
| UAT-E2E-004 | Power user | Multiple features in one session | No crashes, data consistent | ⬜ |
| UAT-E2E-005 | Offline user | Use app without network | Graceful degradation | ⬜ |

---

## 5. Remote Config Test Cases

Test cases for feature flags and remote configuration:

### 🎛️ Feature Flags

| TC ID | Type | Scenario | Steps | Expected Result | Priority |
|-------|------|----------|-------|-----------------|----------|
| RC-F01 | Remote Config | Feature flag ON | 1. Set feature_enabled = true<br>2. Restart app<br>3. Navigate to feature | Feature visible and functional | Critical |
| RC-F02 | Remote Config | Feature flag OFF | 1. Set feature_enabled = false<br>2. Restart app<br>3. Navigate to feature | Feature hidden from UI, no access | Critical |
| RC-F03 | Remote Config | Flag change while app running | 1. Open app<br>2. Change flag remotely<br>3. Refresh/navigate | Feature state updates accordingly | High |
| RC-F04 | Remote Config | Invalid flag value | 1. Set feature_enabled = "invalid"<br>2. Restart app | App uses default value, no crash | High |
| RC-F05 | Remote Config | Flag fetch failure | 1. Block remote config endpoint<br>2. Start app | App uses cached/default values | High |

### 🔢 Configuration Values

| TC ID | Type | Scenario | Steps | Expected Result | Priority |
|-------|------|----------|-------|-----------------|----------|
| RC-V01 | Remote Config | Max limit value | 1. Set max_per_day = 5<br>2. Perform action 5 times<br>3. Try 6th time | Show limit reached message | High |
| RC-V02 | Remote Config | Zero limit | 1. Set max_per_day = 0<br>2. Try to perform action | Feature disabled, show message | High |
| RC-V03 | Remote Config | High limit | 1. Set max_per_day = 1000<br>2. Perform actions | No limit message, normal operation | Medium |
| RC-V04 | Remote Config | Timeout value | 1. Set timeout = 5 seconds<br>2. Trigger long operation | Operation times out at 5s | Medium |
| RC-V05 | Remote Config | API URL change | 1. Change api_base_url<br>2. Restart app<br>3. Make API call | App uses new URL | Critical |

### 🔄 A/B Testing

| TC ID | Type | Scenario | Steps | Expected Result | Priority |
|-------|------|----------|-------|-----------------|----------|
| RC-AB01 | Remote Config | A/B variant control | 1. Set ab_variant = "control"<br>2. Open feature | Show original/control version | High |
| RC-AB02 | Remote Config | A/B variant A | 1. Set ab_variant = "variant_a"<br>2. Open feature | Show variant A changes | High |
| RC-AB03 | Remote Config | A/B variant switch | 1. Start with control<br>2. Switch to variant_a<br>3. Refresh | UI updates to variant A | Medium |

### ⚠️ Force Update

| TC ID | Type | Scenario | Steps | Expected Result | Priority |
|-------|------|----------|-------|-----------------|----------|
| RC-FU01 | Remote Config | Force update required | 1. Set min_app_version > current<br>2. Open app | Show force update dialog, block app | Critical |
| RC-FU02 | Remote Config | Version meets minimum | 1. Set min_app_version <= current<br>2. Open app | App works normally | High |
| RC-FU03 | Remote Config | Update dialog actions | 1. Trigger force update<br>2. Tap "Update" | Navigate to app store | High |

---

## 6. Test Summary

| Category | Total | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
`;

  const grandTotal = Object.values(totalTests).reduce((a, b) => a + b, 0);
  const remoteConfigTests = 16; // Total RC tests added above
  
  for (const [type, count] of Object.entries(totalTests)) {
    if (count > 0) {
      const critical = type === 'Functional' ? Math.ceil(count / 3) : 0;
      const high = type === 'Functional' || type === 'Navigation' || type === 'Network' ? Math.ceil(count / 3) : Math.ceil(count / 4);
      const medium = count - critical - high;
      md += `| ${type} | ${count} | ${critical} | ${high} | ${medium} | 0 |\n`;
    }
  }
  
  md += `| Remote Config | ${remoteConfigTests} | 4 | 8 | 4 | 0 |\n`;
  md += `| Regression | ${features.length} | - | - | - | - |\n`;
  md += `| UAT (E2E) | 5 | - | - | - | - |\n`;
  md += `| **Total** | **${grandTotal + remoteConfigTests + features.length + 5}** | - | - | - | - |\n`;

  md += `
---

## 7. Test Environment

### Devices
- Android: Pixel 6 (Android 13), Samsung Galaxy S21 (Android 12)
- iOS: iPhone 14 (iOS 17), iPhone 12 (iOS 16)

### Network Conditions
- WiFi (stable)
- 4G/LTE (mobile data)
- 3G (slow network simulation)
- Offline (airplane mode)

### Test Data
- Test accounts provided separately
- Test data seeded in staging environment

---

*Generated by QA & UAT Skill*
`;

  return md;
}

// Main function
function main() {
  const params = parseArgs();
  
  // Validate required params
  if (!params.name || !params.code) {
    console.error('Usage: node generate.js --name "Project Name" --code "AAPxxx" --prd "./PRD.md"');
    console.error('Required: --name, --code');
    console.error('Optional: --prd (path to PRD file), --output (output directory)');
    process.exit(1);
  }
  
  // Read PRD if provided
  let features = [];
  if (params.prd && fs.existsSync(params.prd)) {
    const prdContent = fs.readFileSync(params.prd, 'utf8');
    features = extractFeatures(prdContent);
    console.log(`📄 Read PRD: ${params.prd}`);
    console.log(`📋 Extracted ${features.length} features`);
  } else {
    // Default features if no PRD
    features = [
      { name: 'Authentication', prefix: 'AUTH' },
      { name: 'Home', prefix: 'HOME' },
      { name: 'Main Feature', prefix: 'MAIN' },
      { name: 'Profile', prefix: 'PROF' },
      { name: 'Settings', prefix: 'SET' }
    ];
    console.log('⚠️  No PRD provided, using default features');
  }
  
  // Generate document
  const markdown = generateDocument(params, features);
  
  // Write output
  const outputDir = params.output || '.';
  const safeName = params.name.replace(/[^a-zA-Z0-9]/g, '_');
  const filename = `${params.code}_${safeName}_QA_UAT.md`;
  const outputPath = path.join(outputDir, filename);
  
  fs.writeFileSync(outputPath, markdown);
  console.log(`✅ Generated: ${outputPath}`);
  
  // Summary
  console.log(`\n📊 Summary:`);
  console.log(`   Features: ${features.length}`);
  console.log(`   Test categories: 9 (Functional, UI/UX, Navigation, Network, Interrupt, Localization, Remote Config, Regression, UAT)`);
}

main();

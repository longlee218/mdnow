#!/usr/bin/env node
/**
 * Screen Blueprint Generator (Step 1)
 * Generates Screen Layouts, Component Specs, and Navigation Flow from PRD
 */

const fs = require('fs');
const path = require('path');

// Parse CLI args
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

// Extract project info from PRD
function extractProjectInfo(prdContent) {
  const nameMatch = prdContent.match(/\*\*(.+?)\s*\(([A-Z]{3}\d{3})\)\*\*/);
  const descMatch = prdContent.match(/## \*\*1\.1 Product Description\*\*\s*\n\n(.+?)(?=\n\n##|\n\n\*\*)/s);
  
  return {
    name: nameMatch ? nameMatch[1].trim() : 'Unknown Project',
    code: nameMatch ? nameMatch[2] : 'AAP000',
    description: descMatch ? descMatch[1].trim() : ''
  };
}

// System screens to exclude from wireframe (common/reusable screens)
const EXCLUDED_SCREENS = [
  'onboarding', 'welcome', 'intro', 'tutorial', 'walkthrough',
  'login', 'signin', 'sign in', 'sign-in',
  'register', 'signup', 'sign up', 'sign-up', 'registration',
  'auth', 'authentication', 'forgot password', 'reset password',
  'profile', 'account', 'my account', 'user profile',
  'settings', 'preferences', 'config', 'configuration',
  'splash', 'loading'
];

// Check if screen should be excluded
function isExcludedScreen(screenName) {
  const name = screenName.toLowerCase().trim();
  return EXCLUDED_SCREENS.some(excluded => 
    name === excluded || 
    name.includes(excluded) ||
    excluded.includes(name)
  );
}

// Extract screens from PRD (excluding system screens)
function extractScreens(prdContent, includeAll = false) {
  let screens = [];
  
  // Look for UI Checklist sections
  const screenPattern = /## \*\*(.+?) Screen - UI Checklist\*\*/g;
  let match;
  while ((match = screenPattern.exec(prdContent)) !== null) {
    screens.push(match[1].trim());
  }
  
  // Fallback: extract from User Stories
  if (screens.length === 0) {
    const usPattern = /### \*\*US-\d+: (.+?)\*\*/g;
    while ((match = usPattern.exec(prdContent)) !== null) {
      const screen = match[1].trim();
      if (!screens.includes(screen)) screens.push(screen);
    }
  }
  
  // Fallback: extract from Main Flow
  if (screens.length === 0) {
    const flowMatch = prdContent.match(/## \*\*1\.4 Main User Flow\*\*\s*\n\n\*\*(.+?)\*\*/);
    if (flowMatch) {
      screens.push(...flowMatch[1].split('→').map(s => s.trim()));
    }
  }
  
  // Default screens if none found
  if (screens.length === 0) {
    screens = ['Home', 'Detail'];
  }
  
  // Filter out system/common screens unless includeAll is true
  if (!includeAll) {
    const filtered = screens.filter(s => !isExcludedScreen(s));
    // If all screens were filtered, keep at least core screens
    if (filtered.length === 0) {
      console.log(`⚠️  All screens were system screens. Keeping original list.`);
      return screens;
    }
    
    const excluded = screens.filter(s => isExcludedScreen(s));
    if (excluded.length > 0) {
      console.log(`🚫 Excluded system screens: ${excluded.join(', ')}`);
    }
    return filtered;
  }
  
  return screens;
}

// Extract navigation flows from PRD
function extractNavigationFlows(prdContent, screens) {
  const flows = [];
  const transitions = [];
  
  // 1. Extract from Main User Flow
  const mainFlowMatch = prdContent.match(/## \*\*1\.4 Main User Flow\*\*\s*\n\n\*\*(.+?)\*\*/s);
  if (mainFlowMatch) {
    const flowSteps = mainFlowMatch[1].split('→').map(s => s.trim());
    flows.push({
      name: 'Main Flow',
      type: 'primary',
      steps: flowSteps
    });
    
    // Generate transitions from main flow
    for (let i = 0; i < flowSteps.length - 1; i++) {
      transitions.push({
        from: flowSteps[i],
        to: flowSteps[i + 1],
        action: 'Next step',
        type: 'primary'
      });
    }
  }
  
  // 2. Extract from User Stories (acceptance criteria often mention navigation)
  const usPattern = /### \*\*US-\d+: (.+?)\*\*[\s\S]*?(?=### \*\*US-|\n## \*\*|\n---|\Z)/g;
  let usMatch;
  while ((usMatch = usPattern.exec(prdContent)) !== null) {
    const storyContent = usMatch[0];
    const storyScreen = usMatch[1].trim();
    
    // Look for navigation patterns in acceptance criteria
    const navPatterns = [
      /(?:navigate|go|redirect|move|tap|click|press).+?(?:to|into|toward)\s+(?:the\s+)?["']?([A-Za-z\s]+?)(?:["'\s,\.]|screen|page)/gi,
      /(?:open|show|display|present)\s+(?:the\s+)?["']?([A-Za-z\s]+?)(?:["'\s,\.]|screen|page)/gi,
      /(?:back to|return to)\s+(?:the\s+)?["']?([A-Za-z\s]+?)(?:["'\s,\.]|screen|page)/gi
    ];
    
    navPatterns.forEach(pattern => {
      let navMatch;
      while ((navMatch = pattern.exec(storyContent)) !== null) {
        const targetScreen = navMatch[1].trim();
        // Find matching screen
        const matchedScreen = screens.find(s => 
          s.toLowerCase().includes(targetScreen.toLowerCase()) ||
          targetScreen.toLowerCase().includes(s.toLowerCase())
        );
        
        if (matchedScreen && matchedScreen !== storyScreen) {
          const existing = transitions.find(t => 
            t.from === storyScreen && t.to === matchedScreen
          );
          if (!existing) {
            transitions.push({
              from: storyScreen,
              to: matchedScreen,
              action: navMatch[0].substring(0, 30).trim(),
              type: 'user-action'
            });
          }
        }
      }
    });
  }
  
  // 3. Extract from Feature descriptions
  const featurePattern = /### \*\*F-\d+: (.+?)\*\*[\s\S]*?(?=### \*\*F-|\n## \*\*|\Z)/g;
  let featMatch;
  while ((featMatch = featurePattern.exec(prdContent)) !== null) {
    const featureContent = featMatch[0];
    
    // Look for screen mentions
    screens.forEach(screen => {
      if (featureContent.toLowerCase().includes(screen.toLowerCase())) {
        // Check for transitions in feature
        const otherScreens = screens.filter(s => s !== screen);
        otherScreens.forEach(otherScreen => {
          if (featureContent.toLowerCase().includes(otherScreen.toLowerCase())) {
            const existing = transitions.find(t => 
              (t.from === screen && t.to === otherScreen) ||
              (t.from === otherScreen && t.to === screen)
            );
            if (!existing) {
              transitions.push({
                from: screen,
                to: otherScreen,
                action: 'Feature interaction',
                type: 'feature'
              });
            }
          }
        });
      }
    });
  }
  
  // 4. Infer common navigation patterns
  const inferredTransitions = inferNavigationPatterns(screens);
  inferredTransitions.forEach(inferred => {
    const existing = transitions.find(t => t.from === inferred.from && t.to === inferred.to);
    if (!existing) {
      transitions.push(inferred);
    }
  });
  
  return { flows, transitions };
}

// Infer common navigation patterns based on screen names
function inferNavigationPatterns(screens) {
  const transitions = [];
  
  const homeScreen = screens.find(s => 
    s.toLowerCase().includes('home') || 
    s.toLowerCase().includes('dashboard') ||
    s.toLowerCase().includes('main')
  );
  
  const loginScreen = screens.find(s => 
    s.toLowerCase().includes('login') || 
    s.toLowerCase().includes('sign in')
  );
  
  const registerScreen = screens.find(s => 
    s.toLowerCase().includes('register') || 
    s.toLowerCase().includes('sign up')
  );
  
  const profileScreen = screens.find(s => 
    s.toLowerCase().includes('profile') ||
    s.toLowerCase().includes('account')
  );
  
  const settingsScreen = screens.find(s => 
    s.toLowerCase().includes('settings') ||
    s.toLowerCase().includes('config')
  );
  
  const detailScreens = screens.filter(s => 
    s.toLowerCase().includes('detail') ||
    s.toLowerCase().includes('view') ||
    s.toLowerCase().includes('result')
  );
  
  const listScreens = screens.filter(s => 
    s.toLowerCase().includes('list') ||
    s.toLowerCase().includes('search') ||
    s.toLowerCase().includes('browse')
  );
  
  // Login → Home
  if (loginScreen && homeScreen) {
    transitions.push({ from: loginScreen, to: homeScreen, action: 'Successful login', type: 'inferred' });
  }
  
  // Login ↔ Register
  if (loginScreen && registerScreen) {
    transitions.push({ from: loginScreen, to: registerScreen, action: 'Create account', type: 'inferred' });
    transitions.push({ from: registerScreen, to: loginScreen, action: 'Already have account', type: 'inferred' });
  }
  
  // Register → Home
  if (registerScreen && homeScreen) {
    transitions.push({ from: registerScreen, to: homeScreen, action: 'Successful registration', type: 'inferred' });
  }
  
  // Home → Profile
  if (homeScreen && profileScreen) {
    transitions.push({ from: homeScreen, to: profileScreen, action: 'View profile', type: 'inferred' });
  }
  
  // Profile → Settings
  if (profileScreen && settingsScreen) {
    transitions.push({ from: profileScreen, to: settingsScreen, action: 'Open settings', type: 'inferred' });
  }
  
  // Home → List screens
  if (homeScreen) {
    listScreens.forEach(listScreen => {
      transitions.push({ from: homeScreen, to: listScreen, action: 'Browse items', type: 'inferred' });
    });
  }
  
  // List → Detail screens
  listScreens.forEach(listScreen => {
    detailScreens.forEach(detailScreen => {
      transitions.push({ from: listScreen, to: detailScreen, action: 'Select item', type: 'inferred' });
    });
  });
  
  // Home → Detail (if no list)
  if (homeScreen && detailScreens.length > 0 && listScreens.length === 0) {
    detailScreens.forEach(detailScreen => {
      transitions.push({ from: homeScreen, to: detailScreen, action: 'Select item', type: 'inferred' });
    });
  }
  
  return transitions;
}

// Extract UI specifications from PRD
function extractUISpecs(prdContent) {
  const specs = {
    theme: 'light',
    primaryColor: '#3b82f6',
    hasBottomNav: true,
    hasFAB: false,
    hasSearch: true,
    components: []
  };
  
  // Look for UI Specifications section
  const uiSpecMatch = prdContent.match(/## \*\*5\. UI Specifications[\s\S]*?(?=## \*\*6\.|\Z)/);
  if (uiSpecMatch) {
    const uiContent = uiSpecMatch[0].toLowerCase();
    
    if (uiContent.includes('dark')) specs.theme = 'dark';
    if (uiContent.includes('fab') || uiContent.includes('floating action')) specs.hasFAB = true;
    if (uiContent.includes('bottom nav')) specs.hasBottomNav = true;
    
    // Extract color if specified
    const colorMatch = uiContent.match(/primary.+?#([a-f0-9]{6})/i);
    if (colorMatch) specs.primaryColor = '#' + colorMatch[1];
  }
  
  return specs;
}

// Determine layout pattern based on screen name
function getLayoutPattern(screenName, uiSpecs) {
  const name = screenName.toLowerCase();
  
  if (name.includes('home') || name.includes('dashboard')) {
    return {
      header: ['AppBar with logo', 'Search icon'],
      body: ['Banner/Carousel', 'Content grid or list'],
      footer: uiSpecs.hasBottomNav ? ['BottomNav (4-5 tabs)'] : ['None']
    };
  }
  if (name.includes('login') || name.includes('register') || name.includes('auth')) {
    return {
      header: ['Logo centered'],
      body: ['Input fields', 'Action buttons'],
      footer: ['Alternative actions (Forgot password, Sign up)']
    };
  }
  if (name.includes('detail') || name.includes('view') || name.includes('result')) {
    return {
      header: ['AppBar with back button', 'Title', 'Action icons'],
      body: ['Hero image/content', 'Details section', 'Related items'],
      footer: ['Action buttons (CTA)']
    };
  }
  if (name.includes('list') || name.includes('search') || name.includes('browse')) {
    return {
      header: ['AppBar', 'Search bar', 'Filter chips'],
      body: ['Scrollable list/grid'],
      footer: uiSpecs.hasBottomNav ? ['BottomNav'] : ['None']
    };
  }
  if (name.includes('profile') || name.includes('account')) {
    return {
      header: ['AppBar with settings icon'],
      body: ['Avatar', 'User info', 'Menu list'],
      footer: uiSpecs.hasBottomNav ? ['BottomNav'] : ['None']
    };
  }
  if (name.includes('settings') || name.includes('config')) {
    return {
      header: ['AppBar with back button', 'Title'],
      body: ['Settings list with toggles'],
      footer: ['None']
    };
  }
  if (name.includes('loading') || name.includes('process')) {
    return {
      header: ['None'],
      body: ['Loading animation', 'Progress indicator', 'Status text'],
      footer: ['Cancel button (optional)']
    };
  }
  if (name.includes('pick') || name.includes('select') || name.includes('choose')) {
    return {
      header: ['AppBar with back button', 'Title'],
      body: ['Selection grid/list', 'Preview area'],
      footer: ['Confirm button']
    };
  }
  if (name.includes('history')) {
    return {
      header: ['AppBar with back button', 'Title', 'Filter'],
      body: ['Timeline/list of items'],
      footer: uiSpecs.hasBottomNav ? ['BottomNav'] : ['None']
    };
  }
  
  // Default
  return {
    header: ['AppBar'],
    body: ['Main content'],
    footer: uiSpecs.hasBottomNav ? ['BottomNav'] : ['Action buttons']
  };
}

// Generate components for a screen
function generateComponents(screenName, layout) {
  const components = [];
  let id = 1;
  
  // Header components
  if (layout.header.some(h => h.includes('AppBar'))) {
    components.push({ id: id++, type: 'AppBar', position: 'Top', content: screenName, action: 'Navigation' });
  }
  if (layout.header.some(h => h.includes('Search'))) {
    components.push({ id: id++, type: 'IconButton', position: 'Top-right', content: 'Search icon', action: 'Open search' });
  }
  if (layout.header.some(h => h.includes('back'))) {
    components.push({ id: id++, type: 'IconButton', position: 'Top-left', content: 'Back arrow', action: 'Navigate back' });
  }
  if (layout.header.some(h => h.includes('Logo'))) {
    components.push({ id: id++, type: 'Image', position: 'Top-center', content: 'App logo', action: 'None' });
  }
  
  // Body components
  if (layout.body.some(b => b.includes('Banner') || b.includes('Carousel'))) {
    components.push({ id: id++, type: 'Carousel', position: 'Below header', content: 'Promotional banners', action: 'Auto-scroll, tap to view' });
  }
  if (layout.body.some(b => b.includes('grid'))) {
    components.push({ id: id++, type: 'Grid', position: 'Center', content: 'Item cards (2 columns)', action: 'Tap → Detail screen' });
  }
  if (layout.body.some(b => b.includes('list'))) {
    components.push({ id: id++, type: 'List', position: 'Center', content: 'Scrollable items', action: 'Tap → Detail/Action' });
  }
  if (layout.body.some(b => b.includes('Input'))) {
    components.push({ id: id++, type: 'TextField', position: 'Center', content: 'Input field', action: 'Text input' });
    components.push({ id: id++, type: 'TextField', position: 'Center', content: 'Input field', action: 'Text input' });
  }
  if (layout.body.some(b => b.includes('Avatar'))) {
    components.push({ id: id++, type: 'Avatar', position: 'Top-center', content: 'User photo', action: 'Tap to change' });
  }
  if (layout.body.some(b => b.includes('Loading') || b.includes('Progress'))) {
    components.push({ id: id++, type: 'ProgressIndicator', position: 'Center', content: 'Loading animation', action: 'None' });
  }
  if (layout.body.some(b => b.includes('Hero') || b.includes('Preview'))) {
    components.push({ id: id++, type: 'Image', position: 'Top-center', content: 'Hero image', action: 'Tap to enlarge' });
  }
  if (layout.body.some(b => b.includes('Details') || b.includes('Info'))) {
    components.push({ id: id++, type: 'Text', position: 'Below hero', content: 'Details text', action: 'None' });
  }
  if (layout.body.some(b => b.includes('Selection'))) {
    components.push({ id: id++, type: 'Grid', position: 'Center', content: 'Selectable items', action: 'Tap to select' });
  }
  if (layout.body.some(b => b.includes('Timeline'))) {
    components.push({ id: id++, type: 'List', position: 'Center', content: 'History items with date', action: 'Tap → Detail' });
  }
  if (layout.body.some(b => b.includes('Menu'))) {
    components.push({ id: id++, type: 'List', position: 'Center', content: 'Menu items', action: 'Tap → Navigate' });
  }
  
  // Footer components
  if (layout.footer.some(f => f.includes('BottomNav'))) {
    components.push({ id: id++, type: 'BottomNav', position: 'Bottom', content: 'Tab icons (Home, Search, Profile)', action: 'Tab navigation' });
  }
  if (layout.footer.some(f => f.includes('Action') || f.includes('CTA') || f.includes('Confirm'))) {
    components.push({ id: id++, type: 'Button', position: 'Bottom', content: 'Primary action', action: 'Submit/Continue' });
  }
  if (layout.footer.some(f => f.includes('Alternative'))) {
    components.push({ id: id++, type: 'TextButton', position: 'Bottom', content: 'Secondary action', action: 'Navigate' });
  }
  
  return components;
}

// Generate Screen Layouts markdown
function generateScreenLayouts(projectInfo, screens, uiSpecs) {
  let md = `# Screen Layouts

## Project: ${projectInfo.name}
## Code: ${projectInfo.code}
## Date: ${new Date().toISOString().split('T')[0]}

---

`;

  for (const screen of screens) {
    const layout = getLayoutPattern(screen, uiSpecs);
    
    md += `## ${screen} Screen

### Layout Structure

| Section | Components |
|---------|------------|
| **Header** | ${layout.header.join(', ')} |
| **Body** | ${layout.body.join(', ')} |
| **Footer** | ${layout.footer.join(', ')} |

### Visual Layout

\`\`\`
┌─────────────────────────┐
│ ${(layout.header[0] || 'Header').padEnd(23)} │  ← Header
├─────────────────────────┤
│                         │
│ ${(layout.body[0] || 'Body').padEnd(23)} │  ← Body
│                         │
├─────────────────────────┤
│ ${(layout.footer[0] || 'Footer').padEnd(23)} │  ← Footer
└─────────────────────────┘
\`\`\`

---

`;
  }

  return md;
}

// Generate Component Specs markdown
function generateComponentSpecs(projectInfo, screens, uiSpecs) {
  let md = `# Component Specifications

## Project: ${projectInfo.name}
## Code: ${projectInfo.code}
## Date: ${new Date().toISOString().split('T')[0]}

---

`;

  let totalComponents = 0;

  for (const screen of screens) {
    const layout = getLayoutPattern(screen, uiSpecs);
    const components = generateComponents(screen, layout);
    totalComponents += components.length;
    
    md += `## ${screen} Screen

| ID | Type | Position | Content | Action |
|----|------|----------|---------|--------|
`;
    
    for (const comp of components) {
      md += `| ${comp.id} | ${comp.type} | ${comp.position} | ${comp.content} | ${comp.action} |\n`;
    }
    
    md += `\n---\n\n`;
  }

  md += `## Summary

- **Total Screens**: ${screens.length}
- **Total Components**: ${totalComponents}
`;

  return md;
}

// Generate Navigation Flow markdown
function generateNavigationFlow(projectInfo, screens, navigation) {
  let md = `# Screen Navigation Flow

## Project: ${projectInfo.name}
## Code: ${projectInfo.code}
## Date: ${new Date().toISOString().split('T')[0]}

---

## User Flows

`;

  // Document user flows
  if (navigation.flows.length > 0) {
    navigation.flows.forEach((flow, idx) => {
      md += `### ${flow.name}
**Type:** ${flow.type}
**Steps:** ${flow.steps.join(' → ')}

`;
    });
  } else {
    md += `_No explicit flows defined in PRD_

`;
  }

  md += `---

## Screen Transitions

| # | From Screen | To Screen | Trigger/Action | Type |
|---|-------------|-----------|----------------|------|
`;

  navigation.transitions.forEach((trans, idx) => {
    md += `| ${idx + 1} | ${trans.from} | ${trans.to} | ${trans.action} | ${trans.type} |\n`;
  });

  md += `
---

## Navigation Map (ASCII)

\`\`\`
`;

  // Generate ASCII navigation map
  const screenMap = generateASCIINavigationMap(screens, navigation.transitions);
  md += screenMap;

  md += `
\`\`\`

---

## Screen Relationships

`;

  // Group transitions by source screen
  const screenRelations = {};
  screens.forEach(screen => {
    screenRelations[screen] = {
      navigatesTo: [],
      receivesFrom: []
    };
  });

  navigation.transitions.forEach(trans => {
    if (screenRelations[trans.from]) {
      screenRelations[trans.from].navigatesTo.push({ screen: trans.to, action: trans.action });
    }
    if (screenRelations[trans.to]) {
      screenRelations[trans.to].receivesFrom.push({ screen: trans.from, action: trans.action });
    }
  });

  screens.forEach(screen => {
    const rel = screenRelations[screen];
    md += `### ${screen}
- **Navigates to:** ${rel.navigatesTo.length > 0 ? rel.navigatesTo.map(r => `${r.screen} (${r.action})`).join(', ') : '_None_'}
- **Receives from:** ${rel.receivesFrom.length > 0 ? rel.receivesFrom.map(r => `${r.screen} (${r.action})`).join(', ') : '_Entry point_'}

`;
  });

  md += `---

## Summary

- **Total Screens**: ${screens.length}
- **Total Transitions**: ${navigation.transitions.length}
- **Primary Flows**: ${navigation.flows.filter(f => f.type === 'primary').length}
`;

  return md;
}

// Generate ASCII navigation map
function generateASCIINavigationMap(screens, transitions) {
  // Find entry point (screen with no incoming transitions or login/home)
  const incomingCount = {};
  screens.forEach(s => incomingCount[s] = 0);
  transitions.forEach(t => {
    if (incomingCount[t.to] !== undefined) incomingCount[t.to]++;
  });
  
  const entryPoint = screens.find(s => 
    s.toLowerCase().includes('login') || s.toLowerCase().includes('splash')
  ) || screens.find(s => incomingCount[s] === 0) || screens[0];
  
  const homeScreen = screens.find(s => 
    s.toLowerCase().includes('home') || s.toLowerCase().includes('dashboard')
  );
  
  let map = '';
  
  // Simple hierarchical representation
  map += `                    ┌─────────────────┐\n`;
  map += `                    │  ${(entryPoint || 'Entry').padEnd(13)} │\n`;
  map += `                    └────────┬────────┘\n`;
  map += `                             │\n`;
  map += `                             ▼\n`;
  
  if (homeScreen && homeScreen !== entryPoint) {
    map += `                    ┌─────────────────┐\n`;
    map += `                    │  ${homeScreen.padEnd(13)} │\n`;
    map += `                    └────────┬────────┘\n`;
    map += `                             │\n`;
    
    // Find screens navigable from home
    const fromHome = transitions.filter(t => t.from === homeScreen).map(t => t.to);
    if (fromHome.length > 0) {
      const displayScreens = fromHome.slice(0, 4);
      const width = displayScreens.length;
      
      // Draw branching
      if (width > 1) {
        const spacing = '         ';
        map += `           ┌─────${spacing.repeat(Math.max(0, width - 2))}──┴──${spacing.repeat(Math.max(0, width - 2))}─────┐\n`;
        map += `           │${spacing.repeat(width - 1)}          ${spacing.repeat(Math.max(0, width - 2))}│\n`;
        map += `           ▼${spacing.repeat(width - 1)}          ${spacing.repeat(Math.max(0, width - 2))}▼\n`;
      } else {
        map += `                             │\n`;
        map += `                             ▼\n`;
      }
      
      // Draw connected screens
      displayScreens.forEach((screen, idx) => {
        const padding = idx === 0 ? '  ' : (idx === displayScreens.length - 1 ? '                              ' : '              ');
        map += `${padding}┌─────────────────┐`;
      });
      map += '\n';
      
      displayScreens.forEach((screen, idx) => {
        const padding = idx === 0 ? '  ' : (idx === displayScreens.length - 1 ? '                              ' : '              ');
        map += `${padding}│  ${screen.substring(0, 13).padEnd(13)} │`;
      });
      map += '\n';
      
      displayScreens.forEach((screen, idx) => {
        const padding = idx === 0 ? '  ' : (idx === displayScreens.length - 1 ? '                              ' : '              ');
        map += `${padding}└─────────────────┘`;
      });
      map += '\n';
      
      if (fromHome.length > 4) {
        map += `\n                    ... and ${fromHome.length - 4} more screens\n`;
      }
    }
  }
  
  return map;
}

// Main
function main() {
  const params = parseArgs();
  
  if (!params.prd) {
    console.log(`
Screen Blueprint Generator (Step 1)

Usage: node generate-blueprint.js --prd "./PRD.md" [options]

Required:
  --prd       Path to PRD file

Optional:
  --output    Output directory (default: ./)
  --all       Include all screens (don't exclude system screens)

Excluded by default:
  Onboarding, Login, Register, Profile, Settings, Splash

Output Files:
  - {CODE}_Screen_Layouts.md    - Layout structure per screen
  - {CODE}_Component_Specs.md   - Component specifications
  - {CODE}_Screen_Flow.md       - Navigation flow & relationships

Example:
  node generate-blueprint.js --prd "./AAP001_Product_PRD.md" --output "./designs/"
  node generate-blueprint.js --prd "./PRD.md" --all   # Include all screens
`);
    process.exit(1);
  }
  
  if (!fs.existsSync(params.prd)) {
    console.error(`❌ PRD file not found: ${params.prd}`);
    process.exit(1);
  }
  
  const includeAll = params.all === true;
  const prdContent = fs.readFileSync(params.prd, 'utf8');
  const projectInfo = extractProjectInfo(prdContent);
  const screens = extractScreens(prdContent, includeAll);
  const uiSpecs = extractUISpecs(prdContent);
  const navigation = extractNavigationFlows(prdContent, screens);
  
  console.log(`📄 Reading PRD: ${params.prd}`);
  console.log(`📱 Project: ${projectInfo.name} (${projectInfo.code})`);
  console.log(`🖼️  Screens: ${screens.join(', ')}`);
  console.log(`🔗 Transitions: ${navigation.transitions.length}`);
  
  const outputDir = params.output || '.';
  
  // Generate Screen Layouts
  const layoutsContent = generateScreenLayouts(projectInfo, screens, uiSpecs);
  const layoutsPath = path.join(outputDir, `${projectInfo.code}_Screen_Layouts.md`);
  fs.writeFileSync(layoutsPath, layoutsContent);
  console.log(`✅ Generated: ${layoutsPath}`);
  
  // Generate Component Specs
  const specsContent = generateComponentSpecs(projectInfo, screens, uiSpecs);
  const specsPath = path.join(outputDir, `${projectInfo.code}_Component_Specs.md`);
  fs.writeFileSync(specsPath, specsContent);
  console.log(`✅ Generated: ${specsPath}`);
  
  // Generate Navigation Flow
  const flowContent = generateNavigationFlow(projectInfo, screens, navigation);
  const flowPath = path.join(outputDir, `${projectInfo.code}_Screen_Flow.md`);
  fs.writeFileSync(flowPath, flowContent);
  console.log(`✅ Generated: ${flowPath}`);
  
  console.log(`\n📊 Blueprint Summary:`);
  console.log(`   Screens: ${screens.length}`);
  console.log(`   Transitions: ${navigation.transitions.length}`);
  console.log(`   Files: Screen_Layouts.md, Component_Specs.md, Screen_Flow.md`);
  console.log(`\n⏳ Next: Review blueprint, then run generate-wireframe.js`);
}

main();

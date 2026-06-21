#!/usr/bin/env node
/**
 * Wireframe Generator (Step 2)
 * Creates Pencil wireframe file from Screen Blueprint with Navigation Flow
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

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

// Extract project info from layouts file
function extractProjectInfo(layoutsContent) {
  const nameMatch = layoutsContent.match(/## Project: (.+)/);
  const codeMatch = layoutsContent.match(/## Code: ([A-Za-z0-9_]+)/);

  return {
    name: nameMatch ? nameMatch[1].trim() : 'Unknown Project',
    code: codeMatch ? codeMatch[1] : 'AAP000'
  };
}

// Extract screens from layouts file
function extractScreens(layoutsContent) {
  const screens = [];
  // Match patterns:
  // 1. "## S-XX: Name Screen"
  // 2. "## S-XX: Name Panel (Editor Sub-panel)"
  // 3. "## S-XX: Name (Modal)"
  // 4. "## S-XX: Name — Nice Have"
  // 5. Legacy: "## Name Screen\n\n### Layout Structure"
  const screenPattern = /^## (S-\d+: [^\n]+)/gm;
  const legacyPattern = /^## ([A-Z][^\n]+?(?:Screen|Panel|Sheet|Dialog|Modal|Browser))\s*\n\n### Layout Structure/gm;
  let match;

  // Try S-XX pattern first
  while ((match = screenPattern.exec(layoutsContent)) !== null) {
    let screenName = match[1].trim();
    // Remove trailing markers like "(Nice Have)", "(Modal)", "(Editor Sub-panel)", "(Bottom Sheet)"
    screenName = screenName.replace(/\s*\([^)]*\)\s*/g, '').trim();
    // Remove trailing dash notes like "— Nice Have"
    screenName = screenName.replace(/\s*—.*$/, '').trim();

    // Extract the section content until next ## heading or end
    const sectionStart = match.index;
    const restContent = layoutsContent.slice(sectionStart + match[0].length);
    const nextSection = restContent.search(/\n## /);
    const sectionContent = nextSection >= 0
      ? layoutsContent.slice(sectionStart, sectionStart + match[0].length + nextSection)
      : layoutsContent.slice(sectionStart);

    // Extract layout structure - try multiple section name patterns
    let header = 'None', body = 'Content', footer = 'None';

    const headerMatch = sectionContent.match(/\|\s*\*\*(?:Header|StatusBar)\*\*\s*\|\s*(.+?)\s*\|/);
    const bodyMatch = sectionContent.match(/\|\s*\*\*Body\*\*\s*\|\s*(.+?)\s*\|/);
    const panelHeaderMatch = sectionContent.match(/\|\s*\*\*Panel Header\*\*\s*\|\s*(.+?)\s*\|/);
    const footerMatch = sectionContent.match(/\|\s*\*\*Footer\*\*\s*\|\s*(.+?)\s*\|/);

    if (headerMatch) header = headerMatch[1].trim();
    if (panelHeaderMatch) header = panelHeaderMatch[1].trim();
    if (bodyMatch) body = bodyMatch[1].trim();
    if (footerMatch) footer = footerMatch[1].trim();

    // SubHeader enriches body
    const subHeaderMatch = sectionContent.match(/\|\s*\*\*SubHeader\*\*\s*\|\s*(.+?)\s*\|/);
    if (subHeaderMatch) body = subHeaderMatch[1].trim() + ', ' + body;

    screens.push({
      name: screenName,
      header,
      body,
      footer
    });
  }

  // Fallback: try legacy pattern if no S-XX screens found
  if (screens.length === 0) {
    while ((match = legacyPattern.exec(layoutsContent)) !== null) {
      const screenName = match[1].trim();
      const sectionStart = match.index;
      const restContent = layoutsContent.slice(sectionStart + match[0].length);
      const nextSection = restContent.search(/\n## /);
      const sectionContent = nextSection >= 0
        ? layoutsContent.slice(sectionStart, sectionStart + match[0].length + nextSection)
        : layoutsContent.slice(sectionStart);

      let header = 'AppBar', body = 'Content', footer = 'BottomNav';
      const layoutMatch = sectionContent.match(
        /\| \*\*Header\*\* \| (.+?) \|\n\| \*\*Body\*\* \| (.+?) \|\n\| \*\*Footer\*\* \| (.+?) \|/
      );
      if (layoutMatch) {
        header = layoutMatch[1];
        body = layoutMatch[2];
        footer = layoutMatch[3];
      }

      screens.push({ name: screenName, header, body, footer });
    }
  }

  return screens;
}

// Extract navigation transitions from flow file
function extractNavigationFlow(flowContent) {
  const transitions = [];
  
  if (!flowContent) return transitions;
  
  // Parse transitions table
  const tableMatch = flowContent.match(/## Screen Transitions[\s\S]*?\|.*?\|.*?\|.*?\|.*?\|.*?\|([\s\S]*?)(?=\n---|\n## |$)/);
  if (tableMatch) {
    const rows = tableMatch[1].split('\n').filter(row => row.trim().startsWith('|'));
    
    rows.forEach(row => {
      const cells = row.split('|').map(c => c.trim()).filter(c => c);
      if (cells.length >= 4 && !cells[0].includes('-')) {
        transitions.push({
          from: cells[1],
          to: cells[2],
          action: cells[3],
          type: cells[4] || 'user-action'
        });
      }
    });
  }
  
  return transitions;
}

// Resolve a flow transition name to a screen position key
// Flow names: "Splash", "Home", "Photo Picker", "Template Selection", etc.
// Position keys: "S-01: Splash Screen", "S-03: Home Screen", etc.
function resolveScreenName(name, positionKeys) {
  // Exact match
  if (positionKeys.includes(name)) return name;

  const nameLower = name.toLowerCase().trim();

  // Try matching by substring (flow name is contained in position key)
  for (const key of positionKeys) {
    const keyLower = key.toLowerCase();
    // Strip S-XX: prefix and "Screen/Panel/Sheet/Dialog" suffix for matching
    const stripped = keyLower.replace(/^s-\d+:\s*/, '').replace(/\s*(screen|panel|sheet|dialog|modal|browser)\s*$/i, '').trim();
    if (stripped === nameLower) return key;
    if (keyLower.includes(nameLower)) return key;
    if (nameLower.includes(stripped) && stripped.length > 3) return key;
  }

  return null;
}

// Calculate screen positions in a grid layout
function calculateScreenPositions(screens, config) {
  const { screenWidth, screenHeight, gap, screensPerRow, startX, startY } = config;
  const positions = {};
  
  screens.forEach((screen, index) => {
    const col = index % screensPerRow;
    const row = Math.floor(index / screensPerRow);
    
    positions[screen.name] = {
      x: startX + col * (screenWidth + gap),
      y: startY + row * (screenHeight + gap + 40), // +40 for title
      width: screenWidth,
      height: screenHeight,
      centerX: startX + col * (screenWidth + gap) + screenWidth / 2,
      centerY: startY + row * (screenHeight + gap + 40) + screenHeight / 2
    };
  });
  
  return positions;
}

// Generate arrow path between two screens
function generateArrowPath(from, to, positions, allTransitions) {
  const positionKeys = Object.keys(positions);
  const resolvedFrom = resolveScreenName(from, positionKeys);
  const resolvedTo = resolveScreenName(to, positionKeys);

  const fromPos = resolvedFrom ? positions[resolvedFrom] : null;
  const toPos = resolvedTo ? positions[resolvedTo] : null;

  if (!fromPos || !toPos) return null;
  if (resolvedFrom === resolvedTo) return null;
  
  // Determine arrow direction and connection points
  const dx = toPos.centerX - fromPos.centerX;
  const dy = toPos.centerY - fromPos.centerY;
  
  let startX, startY, endX, endY;
  let controlPoint1X, controlPoint1Y, controlPoint2X, controlPoint2Y;
  
  // Check if there's a reverse transition (bidirectional)
  const hasReverse = allTransitions.some(t => t.from === to && t.to === from);
  const offset = hasReverse ? 15 : 0;
  
  if (Math.abs(dx) > Math.abs(dy)) {
    // Horizontal connection
    if (dx > 0) {
      // Left to right
      startX = fromPos.x + fromPos.width;
      startY = fromPos.centerY - offset;
      endX = toPos.x;
      endY = toPos.centerY - offset;
    } else {
      // Right to left
      startX = fromPos.x;
      startY = fromPos.centerY + offset;
      endX = toPos.x + toPos.width;
      endY = toPos.centerY + offset;
    }
    
    // Curved path for horizontal
    const midX = (startX + endX) / 2;
    controlPoint1X = midX;
    controlPoint1Y = startY;
    controlPoint2X = midX;
    controlPoint2Y = endY;
  } else {
    // Vertical connection
    if (dy > 0) {
      // Top to bottom
      startX = fromPos.centerX - offset;
      startY = fromPos.y + fromPos.height;
      endX = toPos.centerX - offset;
      endY = toPos.y;
    } else {
      // Bottom to top
      startX = fromPos.centerX + offset;
      startY = fromPos.y;
      endX = toPos.centerX + offset;
      endY = toPos.y + toPos.height;
    }
    
    // Curved path for vertical
    const midY = (startY + endY) / 2;
    controlPoint1X = startX;
    controlPoint1Y = midY;
    controlPoint2X = endX;
    controlPoint2Y = midY;
  }
  
  return {
    startX, startY,
    endX, endY,
    controlPoint1X, controlPoint1Y,
    controlPoint2X, controlPoint2Y
  };
}

// Generate SVG arrow marker and filters
function generateArrowMarker() {
  return `
    <defs>
      <marker id="arrowhead" markerWidth="10" markerHeight="7" 
              refX="9" refY="3.5" orient="auto" fill="#6366f1">
        <polygon points="0 0, 10 3.5, 0 7" />
      </marker>
      <marker id="arrowhead-primary" markerWidth="10" markerHeight="7" 
              refX="9" refY="3.5" orient="auto" fill="#22c55e">
        <polygon points="0 0, 10 3.5, 0 7" />
      </marker>
      <!-- Shadow filters for elevation -->
      <filter id="shadow1" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.15"/>
      </filter>
      <filter id="shadow2" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="2" stdDeviation="4" flood-opacity="0.2"/>
      </filter>
      <filter id="shadow3" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.25"/>
      </filter>
    </defs>`;
}

// Generate Design System panel
function generateDesignSystem(x, y, projectInfo) {
  const panelWidth = 420;
  const panelHeight = 740;
  
  // Design tokens - extracted from PRD or use defaults
  const colors = {
    primary: '#6C5CE7',
    primaryDark: '#5A4BD1',
    secondary: '#FF6B6B',
    success: '#22C55E',
    warning: '#F59E0B',
    error: '#EF4444',
    background: '#FFFFFF',
    surface: '#F5F5F5',
    textPrimary: '#1A1A1A',
    textSecondary: '#757575',
    border: '#E0E0E0'
  };
  
  let svg = `
    <!-- Design System Panel -->
    <g id="design-system">
      <!-- Panel background -->
      <rect x="${x}" y="${y}" width="${panelWidth}" height="${panelHeight}" 
            fill="#ffffff" stroke="#e5e7eb" stroke-width="2" rx="12"/>
      
      <!-- Title -->
      <text x="${x + 20}" y="${y + 35}" font-family="Arial" font-size="18" font-weight="bold" fill="#111827">
        Design System
      </text>
      <text x="${x + 20}" y="${y + 55}" font-family="Arial" font-size="12" fill="#6b7280">
        ${projectInfo.name} (${projectInfo.code})
      </text>
      
      <!-- Divider -->
      <line x1="${x + 20}" y1="${y + 70}" x2="${x + panelWidth - 20}" y2="${y + 70}" stroke="#e5e7eb" stroke-width="1"/>
      
      <!-- Design Style Section -->
      <text x="${x + 20}" y="${y + 95}" font-family="Arial" font-size="14" font-weight="bold" fill="#111827">
        Design Style
      </text>
      
      <!-- Design System row -->
      <text x="${x + 20}" y="${y + 118}" font-family="Arial" font-size="11" fill="#6b7280">Design System:</text>
      <rect x="${x + 110}" y="${y + 103}" width="90" height="24" fill="${colors.primary}" rx="12"/>
      <text x="${x + 130}" y="${y + 119}" font-family="Arial" font-size="11" font-weight="bold" fill="#ffffff">Material 3</text>
      
      <rect x="${x + 208}" y="${y + 103}" width="50" height="24" fill="none" stroke="${colors.border}" stroke-width="1" rx="12"/>
      <text x="${x + 220}" y="${y + 119}" font-family="Arial" font-size="11" fill="#6b7280">iOS</text>
      
      <!-- Primary Style row -->
      <text x="${x + 20}" y="${y + 145}" font-family="Arial" font-size="11" fill="#6b7280">Primary Style:</text>
      <rect x="${x + 110}" y="${y + 130}" width="280" height="24" fill="#f3f4f6" stroke="${colors.border}" stroke-width="1" rx="6"/>
      <text x="${x + 120}" y="${y + 146}" font-family="Arial" font-size="11" font-weight="bold" fill="#374151">Minimalistic + Professional / Geometric</text>
      
      <!-- Style properties -->
      <text x="${x + 20}" y="${y + 172}" font-family="Arial" font-size="10" fill="#6b7280">
        Corners: Rounded (8dp) · Elevation: 2-8dp · Icons: Outlined · Animations: Subtle
      </text>
      
      <!-- Divider -->
      <line x1="${x + 20}" y1="${y + 185}" x2="${x + panelWidth - 20}" y2="${y + 185}" stroke="#e5e7eb" stroke-width="1"/>
      
      <!-- Colors Section -->
      <text x="${x + 20}" y="${y + 210}" font-family="Arial" font-size="14" font-weight="bold" fill="#111827">
        Colors
      </text>
      
      <!-- Primary colors row -->
      <rect x="${x + 20}" y="${y + 225}" width="40" height="40" fill="${colors.primary}" rx="6"/>
      <text x="${x + 25}" y="${y + 280}" font-family="Arial" font-size="9" fill="#6b7280">Primary</text>
      
      <rect x="${x + 70}" y="${y + 225}" width="40" height="40" fill="${colors.secondary}" rx="6"/>
      <text x="${x + 70}" y="${y + 280}" font-family="Arial" font-size="9" fill="#6b7280">Secondary</text>
      
      <rect x="${x + 120}" y="${y + 225}" width="40" height="40" fill="${colors.success}" rx="6"/>
      <text x="${x + 125}" y="${y + 280}" font-family="Arial" font-size="9" fill="#6b7280">Success</text>
      
      <rect x="${x + 170}" y="${y + 225}" width="40" height="40" fill="${colors.warning}" rx="6"/>
      <text x="${x + 172}" y="${y + 280}" font-family="Arial" font-size="9" fill="#6b7280">Warning</text>
      
      <rect x="${x + 220}" y="${y + 225}" width="40" height="40" fill="${colors.error}" rx="6"/>
      <text x="${x + 230}" y="${y + 280}" font-family="Arial" font-size="9" fill="#6b7280">Error</text>
      
      <!-- Neutral colors row -->
      <rect x="${x + 280}" y="${y + 225}" width="40" height="40" fill="${colors.surface}" stroke="${colors.border}" rx="6"/>
      <text x="${x + 282}" y="${y + 280}" font-family="Arial" font-size="9" fill="#6b7280">Surface</text>
      
      <rect x="${x + 330}" y="${y + 225}" width="40" height="40" fill="${colors.textPrimary}" rx="6"/>
      <text x="${x + 342}" y="${y + 280}" font-family="Arial" font-size="9" fill="#6b7280">Text</text>
      
      <!-- Typography Section -->
      <text x="${x + 20}" y="${y + 315}" font-family="Arial" font-size="14" font-weight="bold" fill="#111827">
        Typography
      </text>
      
      <text x="${x + 20}" y="${y + 343}" font-family="Arial" font-size="24" font-weight="bold" fill="#111827">
        Heading 1 (24sp)
      </text>
      <text x="${x + 20}" y="${y + 367}" font-family="Arial" font-size="18" font-weight="bold" fill="#111827">
        Heading 2 (18sp)
      </text>
      <text x="${x + 20}" y="${y + 389}" font-family="Arial" font-size="16" fill="#111827">
        Body text (16sp)
      </text>
      <text x="${x + 20}" y="${y + 409}" font-family="Arial" font-size="14" fill="#6b7280">
        Secondary text (14sp)
      </text>
      <text x="${x + 20}" y="${y + 427}" font-family="Arial" font-size="12" fill="#6b7280">
        Caption text (12sp)
      </text>
      
      <!-- Spacing Section -->
      <text x="${x + 20}" y="${y + 460}" font-family="Arial" font-size="14" font-weight="bold" fill="#111827">
        Spacing Scale
      </text>
      
      <!-- Spacing blocks -->
      <rect x="${x + 20}" y="${y + 475}" width="4" height="16" fill="${colors.primary}" rx="1"/>
      <text x="${x + 30}" y="${y + 487}" font-family="Arial" font-size="10" fill="#6b7280">4dp (xs)</text>
      
      <rect x="${x + 90}" y="${y + 475}" width="8" height="16" fill="${colors.primary}" rx="1"/>
      <text x="${x + 104}" y="${y + 487}" font-family="Arial" font-size="10" fill="#6b7280">8dp (sm)</text>
      
      <rect x="${x + 165}" y="${y + 475}" width="16" height="16" fill="${colors.primary}" rx="2"/>
      <text x="${x + 186}" y="${y + 487}" font-family="Arial" font-size="10" fill="#6b7280">16dp (md)</text>
      
      <rect x="${x + 250}" y="${y + 475}" width="24" height="16" fill="${colors.primary}" rx="2"/>
      <text x="${x + 280}" y="${y + 487}" font-family="Arial" font-size="10" fill="#6b7280">24dp (lg)</text>
      
      <rect x="${x + 340}" y="${y + 475}" width="32" height="16" fill="${colors.primary}" rx="2"/>
      <text x="${x + 378}" y="${y + 487}" font-family="Arial" font-size="10" fill="#6b7280">32dp</text>
      
      <!-- Elevation Section -->
      <text x="${x + 20}" y="${y + 520}" font-family="Arial" font-size="14" font-weight="bold" fill="#111827">
        Elevation / Shadows
      </text>
      
      <!-- Elevation samples -->
      <g filter="url(#shadow1)">
        <rect x="${x + 20}" y="${y + 535}" width="60" height="40" fill="#ffffff" rx="8"/>
      </g>
      <text x="${x + 35}" y="${y + 590}" font-family="Arial" font-size="9" fill="#6b7280">Level 1</text>
      
      <g filter="url(#shadow2)">
        <rect x="${x + 100}" y="${y + 533}" width="60" height="44" fill="#ffffff" rx="8"/>
      </g>
      <text x="${x + 115}" y="${y + 590}" font-family="Arial" font-size="9" fill="#6b7280">Level 2</text>
      
      <g filter="url(#shadow3)">
        <rect x="${x + 180}" y="${y + 530}" width="60" height="50" fill="#ffffff" rx="8"/>
      </g>
      <text x="${x + 195}" y="${y + 590}" font-family="Arial" font-size="9" fill="#6b7280">Level 3</text>
      
      <!-- Elevation note -->
      <text x="${x + 260}" y="${y + 560}" font-family="Arial" font-size="10" fill="#6b7280">Cards: Level 1</text>
      <text x="${x + 260}" y="${y + 575}" font-family="Arial" font-size="10" fill="#6b7280">FAB: Level 3</text>
      <text x="${x + 260}" y="${y + 590}" font-family="Arial" font-size="10" fill="#6b7280">Modal: Level 3</text>
      
      <!-- Components Section -->
      <text x="${x + 20}" y="${y + 620}" font-family="Arial" font-size="14" font-weight="bold" fill="#111827">
        Components
      </text>
      
      <!-- Button samples -->
      <rect x="${x + 20}" y="${y + 635}" width="100" height="36" fill="${colors.primary}" rx="8"/>
      <text x="${x + 45}" y="${y + 658}" font-family="Arial" font-size="12" font-weight="bold" fill="#ffffff">Primary</text>
      
      <rect x="${x + 130}" y="${y + 635}" width="100" height="36" fill="none" stroke="${colors.primary}" stroke-width="2" rx="8"/>
      <text x="${x + 148}" y="${y + 658}" font-family="Arial" font-size="12" font-weight="bold" fill="${colors.primary}">Secondary</text>
      
      <text x="${x + 250}" y="${y + 658}" font-family="Arial" font-size="12" font-weight="bold" fill="${colors.primary}">Text Button</text>
      
      <!-- Input sample -->
      <rect x="${x + 20}" y="${y + 680}" width="180" height="32" fill="#ffffff" stroke="${colors.border}" stroke-width="1" rx="8"/>
      <text x="${x + 32}" y="${y + 701}" font-family="Arial" font-size="12" fill="#9ca3af">Input placeholder...</text>
      
      <!-- Corner radius info -->
      <text x="${x + 220}" y="${y + 695}" font-family="Arial" font-size="10" fill="#6b7280">Radius: 8dp</text>
      <text x="${x + 300}" y="${y + 695}" font-family="Arial" font-size="10" fill="#6b7280">Border: 1dp</text>
      <text x="${x + 220}" y="${y + 710}" font-family="Arial" font-size="10" fill="#6b7280">Height: 48dp</text>
      <text x="${x + 300}" y="${y + 710}" font-family="Arial" font-size="10" fill="#6b7280">Padding: 16dp</text>
    </g>`;
  
  return { svg, height: panelHeight };
}

// Generate Pencil XML content with navigation flow
function generatePencilXML(projectInfo, screens, transitions) {
  // Dynamically calculate layout based on screen count
  const screenCount = screens.length;
  const screensPerRow = screenCount <= 9 ? 4 : screenCount <= 16 ? 5 : 6;
  const screenWidth = 220;
  const screenHeight = 450;
  const gap = 100;
  const startX = 80;
  const startY = 100;
  const pageWidth = startX + screensPerRow * (screenWidth + gap) + 500; // +500 for design system panel
  
  const config = { screenWidth, screenHeight, gap, screensPerRow, startX, startY };
  const positions = calculateScreenPositions(screens, config);
  
  let shapesXml = generateArrowMarker();
  
  // Draw navigation arrows first (behind screens)
  shapesXml += '\n    <!-- Navigation Flow Arrows -->\n';
  transitions.forEach((trans, idx) => {
    const arrow = generateArrowPath(trans.from, trans.to, positions, transitions);
    if (arrow) {
      const isPrimary = trans.type === 'primary';
      const strokeColor = isPrimary ? '#22c55e' : '#6366f1';
      const strokeWidth = isPrimary ? 3 : 2;
      const markerId = isPrimary ? 'arrowhead-primary' : 'arrowhead';
      const dashArray = trans.type === 'inferred' ? 'stroke-dasharray="5,5"' : '';
      
      shapesXml += `
    <g id="arrow_${idx}" class="navigation-arrow">
      <path d="M ${arrow.startX} ${arrow.startY} 
               C ${arrow.controlPoint1X} ${arrow.controlPoint1Y}, 
                 ${arrow.controlPoint2X} ${arrow.controlPoint2Y}, 
                 ${arrow.endX} ${arrow.endY}"
            fill="none" stroke="${strokeColor}" stroke-width="${strokeWidth}" 
            marker-end="url(#${markerId})" ${dashArray}/>
    </g>`;
    }
  });
  
  // Draw screens
  shapesXml += '\n\n    <!-- Screen Wireframes -->\n';
  screens.forEach((screen, index) => {
    const pos = positions[screen.name];
    const x = pos.x;
    const y = pos.y;
    
    // Phone frame
    shapesXml += `
    <g id="screen_${index}_frame">
      <rect x="${x}" y="${y}" width="${screenWidth}" height="${screenHeight}" 
            fill="#ffffff" stroke="#333333" stroke-width="2" rx="16" ry="16"/>
      <text x="${x + screenWidth/2}" y="${y - 10}" text-anchor="middle" 
            font-family="Arial" font-size="14" font-weight="bold" fill="#333333">${screen.name}</text>
    </g>`;
    
    // Status bar
    shapesXml += `
    <g id="screen_${index}_statusbar">
      <rect x="${x + 8}" y="${y + 8}" width="${screenWidth - 16}" height="20" 
            fill="#f5f5f5" stroke="none"/>
      <text x="${x + 20}" y="${y + 22}" font-family="Arial" font-size="10" fill="#666">9:41</text>
      <text x="${x + screenWidth - 30}" y="${y + 22}" font-family="Arial" font-size="10" fill="#666">100%</text>
    </g>`;
    
    // Header
    if (!screen.header.includes('None')) {
      shapesXml += `
    <g id="screen_${index}_header">
      <rect x="${x + 8}" y="${y + 32}" width="${screenWidth - 16}" height="50" 
            fill="#6C5CE7" stroke="none" rx="0"/>
      <text x="${x + 20}" y="${y + 62}" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">
        ${screen.name.substring(0, 15)}
      </text>
    </g>`;
    
      // Back button if applicable
      if (screen.header.includes('back')) {
        shapesXml += `
    <g id="screen_${index}_back">
      <text x="${x + 16}" y="${y + 62}" font-family="Arial" font-size="16" fill="#ffffff">←</text>
    </g>`;
      }
    }
    
    // Body placeholder
    const bodyY = y + 90;
    const bodyHeight = screenHeight - 160;
    shapesXml += `
    <g id="screen_${index}_body">
      <rect x="${x + 8}" y="${bodyY}" width="${screenWidth - 16}" height="${bodyHeight}" 
            fill="#fafafa" stroke="#e5e5e5" stroke-width="1"/>`;
    
    // Body content based on type
    if (screen.body.includes('list') || screen.body.includes('Menu')) {
      // List items
      for (let i = 0; i < 4; i++) {
        shapesXml += `
      <rect x="${x + 16}" y="${bodyY + 10 + i * 50}" width="${screenWidth - 32}" height="40" 
            fill="#ffffff" stroke="#e5e5e5" rx="4"/>`;
      }
    } else if (screen.body.includes('grid') || screen.body.includes('Grid')) {
      // Grid items
      for (let row = 0; row < 2; row++) {
        for (let col = 0; col < 2; col++) {
          shapesXml += `
      <rect x="${x + 16 + col * 95}" y="${bodyY + 10 + row * 100}" width="85" height="90" 
            fill="#ffffff" stroke="#e5e5e5" rx="4"/>`;
        }
      }
    } else if (screen.body.includes('Input') || screen.body.includes('fields')) {
      // Input fields
      for (let i = 0; i < 3; i++) {
        shapesXml += `
      <rect x="${x + 16}" y="${bodyY + 20 + i * 60}" width="${screenWidth - 32}" height="44" 
            fill="#ffffff" stroke="#d1d5db" rx="4"/>`;
      }
    } else if (screen.body.includes('Avatar')) {
      // Profile layout
      shapesXml += `
      <circle cx="${x + screenWidth/2}" cy="${bodyY + 60}" r="40" fill="#e5e5e5" stroke="#d1d5db"/>
      <rect x="${x + 30}" y="${bodyY + 120}" width="${screenWidth - 60}" height="20" fill="#e5e5e5" rx="4"/>`;
    } else if (screen.body.includes('Hero') || screen.body.includes('Carousel')) {
      // Hero/Banner
      shapesXml += `
      <rect x="${x + 16}" y="${bodyY + 10}" width="${screenWidth - 32}" height="120" 
            fill="#e5e5e5" stroke="#d1d5db" rx="4"/>`;
    }
    
    shapesXml += `
    </g>`;
    
    // Footer
    if (!screen.footer.includes('None')) {
      shapesXml += `
    <g id="screen_${index}_footer">
      <rect x="${x + 8}" y="${y + screenHeight - 60}" width="${screenWidth - 16}" height="52" 
            fill="#ffffff" stroke="#e5e5e5" stroke-width="1"/>`;
      
      if (screen.footer.includes('BottomNav')) {
        // Bottom nav tabs
        for (let i = 0; i < 4; i++) {
          shapesXml += `
      <circle cx="${x + 35 + i * 50}" cy="${y + screenHeight - 34}" r="12" fill="#e5e5e5"/>`;
        }
      } else if (screen.footer.includes('Action') || screen.footer.includes('CTA') || screen.footer.includes('Confirm')) {
        // Action button
        shapesXml += `
      <rect x="${x + 16}" y="${y + screenHeight - 52}" width="${screenWidth - 32}" height="36" 
            fill="#6C5CE7" stroke="none" rx="4"/>
      <text x="${x + screenWidth/2}" y="${y + screenHeight - 28}" text-anchor="middle" 
            font-family="Arial" font-size="12" fill="#ffffff">Action</text>`;
      }
      
      shapesXml += `
    </g>`;
    }
  });
  
  // Calculate positions for legend and design system
  const totalRows = Math.ceil(screens.length / screensPerRow);
  const screensEndY = startY + totalRows * (screenHeight + gap + 40);
  const legendY = screensEndY + 40;
  
  // Add legend
  shapesXml += `
    
    <!-- Legend -->
    <g id="legend">
      <text x="80" y="${legendY}" font-family="Arial" font-size="14" font-weight="bold" fill="#333">Navigation Legend:</text>
      
      <line x1="80" y1="${legendY + 20}" x2="130" y2="${legendY + 20}" 
            stroke="#22c55e" stroke-width="3" marker-end="url(#arrowhead-primary)"/>
      <text x="145" y="${legendY + 25}" font-family="Arial" font-size="12" fill="#333">Primary Flow</text>
      
      <line x1="280" y1="${legendY + 20}" x2="330" y2="${legendY + 20}" 
            stroke="#6366f1" stroke-width="2" marker-end="url(#arrowhead)"/>
      <text x="345" y="${legendY + 25}" font-family="Arial" font-size="12" fill="#333">User Action</text>
      
      <line x1="480" y1="${legendY + 20}" x2="530" y2="${legendY + 20}" 
            stroke="#6366f1" stroke-width="2" stroke-dasharray="5,5" marker-end="url(#arrowhead)"/>
      <text x="545" y="${legendY + 25}" font-family="Arial" font-size="12" fill="#333">Inferred</text>
    </g>`;
  
  // Add Design System panel (positioned to the right of screens)
  const designSystemX = startX + screensPerRow * (screenWidth + gap) + 40;
  const designSystemY = startY;
  const designSystem = generateDesignSystem(designSystemX, designSystemY, projectInfo);
  shapesXml += designSystem.svg;
  
  // Calculate document height
  const docHeight = Math.max(legendY + 80, designSystemY + designSystem.height + 40);
  
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="http://www.evolus.vn/Namespace/Pencil">
  <Properties>
    <Property name="title">${projectInfo.name} Wireframe</Property>
    <Property name="version">1.0</Property>
  </Properties>
  <Pages>
    <Page name="Wireframe with Navigation">
      <Properties>
        <Property name="width">${pageWidth}</Property>
        <Property name="height">${docHeight}</Property>
      </Properties>
      <Content>
        <svg xmlns="http://www.w3.org/2000/svg" width="${pageWidth}" height="${docHeight}">
          ${shapesXml}
        </svg>
      </Content>
    </Page>
  </Pages>
</Document>`;
  
  return xml;
}

// Check if Pencil is installed
function isPencilInstalled() {
  try {
    if (fs.existsSync('/Applications/Pencil.app')) return true;
    if (fs.existsSync(path.join(process.env.HOME, 'Applications/Pencil.app'))) return true;
    
    const result = execSync('mdfind -name "Pencil.app" -onlyin /Applications 2>/dev/null || true', { encoding: 'utf8' });
    return result.includes('Pencil.app');
  } catch {
    return false;
  }
}

// Open Pencil app
function openPencil(filePath) {
  try {
    execSync(`open -a Pencil "${filePath}"`, { encoding: 'utf8' });
    return true;
  } catch {
    return false;
  }
}

// Main
function main() {
  const params = parseArgs();
  
  if (!params.layouts) {
    console.log(`
Wireframe Generator (Step 2) - Pencil with Navigation Flow & Design System

Usage: node generate-wireframe.js --layouts "./Screen_Layouts.md" [options]

Required:
  --layouts     Path to Screen_Layouts.md file

Optional:
  --flow        Path to Screen_Flow.md file (for navigation arrows)
  --components  Path to Component_Specs.md file (for reference)
  --output      Output directory (default: ./)

Features:
  - Detailed screen wireframes (layout, components, states)
  - Visual navigation flow with arrows between screens
  - Design System panel (colors, typography, spacing, components)
  - Legend showing flow types (primary, user action, inferred)

Example:
  node generate-wireframe.js \\
    --layouts "./AAP001_Screen_Layouts.md" \\
    --flow "./AAP001_Screen_Flow.md" \\
    --output "./designs/"
`);
    process.exit(1);
  }
  
  if (!fs.existsSync(params.layouts)) {
    console.error(`❌ Layouts file not found: ${params.layouts}`);
    process.exit(1);
  }
  
  // Check Pencil
  if (!isPencilInstalled()) {
    console.log(`
⚠️  Pencil app not installed.

Please install from: https://pencil.evolus.vn/Downloads.html

After installing, run this command again.
`);
    process.exit(1);
  }
  
  const layoutsContent = fs.readFileSync(params.layouts, 'utf8');
  const projectInfo = extractProjectInfo(layoutsContent);
  const screens = extractScreens(layoutsContent);
  
  // Load navigation flow if provided
  let transitions = [];
  if (params.flow && fs.existsSync(params.flow)) {
    const flowContent = fs.readFileSync(params.flow, 'utf8');
    transitions = extractNavigationFlow(flowContent);
    console.log(`🔗 Flow file: ${params.flow}`);
    console.log(`   Transitions: ${transitions.length}`);
  } else {
    // Try to auto-detect flow file
    const autoFlowPath = params.layouts.replace('_Screen_Layouts.md', '_Screen_Flow.md');
    if (fs.existsSync(autoFlowPath)) {
      const flowContent = fs.readFileSync(autoFlowPath, 'utf8');
      transitions = extractNavigationFlow(flowContent);
      console.log(`🔗 Auto-detected flow: ${autoFlowPath}`);
      console.log(`   Transitions: ${transitions.length}`);
    } else {
      console.log(`⚠️  No flow file found. Wireframe will not include navigation arrows.`);
      console.log(`   Generate with: node generate-blueprint.js --prd <PRD file>`);
    }
  }
  
  console.log(`📄 Reading Blueprint: ${params.layouts}`);
  console.log(`📱 Project: ${projectInfo.name} (${projectInfo.code})`);
  console.log(`🖼️  Screens: ${screens.map(s => s.name).join(', ')}`);
  
  const outputDir = params.output || '.';
  
  // Generate Pencil XML with navigation and design system
  const pencilXml = generatePencilXML(projectInfo, screens, transitions);
  
  // Save as .ep file
  const wireframePath = path.join(outputDir, `${projectInfo.code}_Wireframe.ep`);
  fs.writeFileSync(wireframePath, pencilXml);
  console.log(`✅ Generated: ${wireframePath}`);
  
  // Open Pencil
  console.log(`\n🎨 Opening Pencil...`);
  if (openPencil(wireframePath)) {
    console.log(`✅ Pencil opened with wireframe file`);
  } else {
    console.log(`⚠️  Could not open Pencil automatically.`);
    console.log(`   Please open manually: ${wireframePath}`);
  }
  
  console.log(`\n📊 Wireframe Summary:`);
  console.log(`   Screens: ${screens.length}`);
  console.log(`   Navigation Arrows: ${transitions.length}`);
  console.log(`   Design System: Included ✓`);
  console.log(`   File: ${wireframePath}`);
}

main();

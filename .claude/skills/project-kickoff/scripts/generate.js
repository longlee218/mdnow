#!/usr/bin/env node
/**
 * BA Agent - Project Kickoff Generator
 * 
 * Usage:
 *   node generate.js --idea "App Name" --usecase "Description" --target "User segment"
 *   node generate.js --idea "..." --usecase "..." --target "..." --apps "App1:Desc1,App2:Desc2" --features "F1:D1:Must have,F2:D2:Nice have"
 */

const ExcelJS = require('exceljs');
const path = require('path');

// ==================== PERSONA MAPPING ====================
const PERSONA_STYLES = {
  'P1': { name: 'Memory', description: 'Users who want to preserve and cherish memories', primaryStyle: 'Minimalistic + Dreamy/Soft', colorPalette: 'Warm (cream, beige, soft blue), accent rose/gold', typography: 'Serif headline, light body', keyUIElement: 'Photo frame, album, candle illustration', microInteractions: 'Gentle fade, soft bounce', keywords: ['memory', 'family', 'photo', 'album', 'ký ức', 'gia đình', 'hoài niệm', 'kỷ niệm'] },
  'P2': { name: 'Professional', description: 'Professional users, work-focused', primaryStyle: 'Minimalistic + Professional', colorPalette: 'Cool (white, gray, blue), accent brand color', typography: 'Clean sans-serif (Inter, Roboto)', keyUIElement: 'Card, badge, stat counter', microInteractions: 'Smooth slide, highlight glow', keywords: ['professional', 'business', 'work', 'productivity', 'công việc', 'chuyên nghiệp'] },
  'P3': { name: 'Gen Z', description: 'Young, dynamic users', primaryStyle: 'Pop Art + Minimalistic + Liquid', colorPalette: 'Bright (pink, cyan, yellow), high contrast', typography: 'Rounded sans-serif (Poppins)', keyUIElement: 'Large tap button, progress bar', microInteractions: 'Satisfying bounce, confetti, heart', keywords: ['gen z', 'young', 'fun', 'social', 'trẻ', 'vui', 'trend', 'tiktok'] },
  'P4': { name: 'Anime/Gaming', description: 'Anime and gaming enthusiasts', primaryStyle: 'Futuristic + Pop Art + Cosmic/Cyberpunk', colorPalette: 'Dark + neon (cyan, magenta, purple)', typography: 'Bold geometric sans', keyUIElement: 'Neon border, gradient button', microInteractions: 'Neon glow, pulse animation', keywords: ['anime', 'gaming', 'game', 'cyberpunk', 'neon', 'futuristic'] },
  'P5': { name: 'Beauty', description: 'Beauty and skincare enthusiasts', primaryStyle: 'Minimalistic + Glassmorphic + Neumorphic', colorPalette: 'Soft palette (pastel pink, mint, lilac), white', typography: 'Elegant thin sans (Poppins, DM Sans)', keyUIElement: 'Glassmorphic card, slider', microInteractions: 'Smooth glide, soft reflection', keywords: ['beauty', 'makeup', 'selfie', 'skin', 'làm đẹp', 'skincare', 'filter'] },
  'P6': { name: 'Creator', description: 'Content creators, influencers', primaryStyle: 'Minimalistic + Professional/Geometric', colorPalette: 'Neutral (white, gray, dark gray), accent color', typography: 'Clean sans, bold CTA', keyUIElement: 'Tab, preset chip, timeline', microInteractions: 'Fast slide, ripple effect', keywords: ['creator', 'video', 'edit', 'content', 'influencer', 'youtube', 'reels'] },
  'P7': { name: 'Designer', description: 'Designers, creative professionals', primaryStyle: 'Minimalistic + Geometric + Futuristic (Dark)', colorPalette: 'Dark mode (near-black, dark gray), neon accent', typography: 'Professional sans, icon-heavy', keyUIElement: 'Slider, color picker, grid', microInteractions: 'Smooth transition, color feedback', keywords: ['design', 'creative', 'art', 'graphic', 'thiết kế', 'color', 'palette', 'interior', 'real estate'] }
};

// ==================== DEFAULT FEATURES ====================
// Story Point scale: 0.5=tiny, 1=small, 2=medium, 3=large
// MVP Structure:
//   - Must have: 21 SP (Core ~8 + System 13)
//   - Nice have: ~4 SP (optional)
//   - Total MVP: 21-25 SP
// Default features (System/Monetization): 13 points - always Must have
const DEFAULT_FEATURES = [
  { name: 'First Open SDK', desc: 'Show ads on first app open', priority: 'Must have', storyPoints: 3 },
  { name: 'Ad in app', desc: 'Banner, interstitial, rewarded ads', priority: 'Must have', storyPoints: 3 },
  { name: 'Subscription', desc: 'Premium package (unlimited, ad-free)', priority: 'Must have', storyPoints: 1 },
  { name: 'Remote Config', desc: 'Fetch config from Firebase', priority: 'Must have', storyPoints: 1 },
  { name: 'Event Tracking', desc: 'Track user behavior (Firebase Analytics)', priority: 'Must have', storyPoints: 1 },
  { name: 'Multiple Language', desc: 'Multi-language support (VI, EN, ...)', priority: 'Must have', storyPoints: 1 },
  { name: 'Service in house', desc: 'Processing service (self-hosted or API)', priority: 'Must have', storyPoints: 1 },
  { name: 'Report', desc: 'Report inappropriate results', priority: 'Must have', storyPoints: 1 },
  { name: 'Dev VIP Toggle', desc: 'Fake VIP account toggle in Settings (appDev only, IS_DEV=true)', priority: 'Must have', storyPoints: 1 },
];

// Version limits
// Each version: 25 SP total
//   - Must have: 21 SP (core features)
//   - Nice have: 4 SP (optional enhancements, flexible 0-4 SP)
const MUST_HAVE_POINTS = 21;
const NICE_HAVE_POINTS = 4;
const MAX_STORY_POINTS_PER_VERSION = MUST_HAVE_POINTS + NICE_HAVE_POINTS; // 25 SP

// ==================== HELPERS ====================
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

function parseApps(appsStr) {
  if (!appsStr) return null;
  return appsStr.split(',').map(app => {
    const [name, ...descParts] = app.split(':');
    return [name.trim(), descParts.join(':').trim() || 'Reference app'];
  });
}

function parseFeatures(featuresStr) {
  if (!featuresStr) return [];
  return featuresStr.split(',').map(f => {
    const parts = f.split(':');
    return {
      name: parts[0]?.trim() || 'Feature',
      desc: parts[1]?.trim() || '',
      priority: parts[2]?.trim() || 'Must have',
      storyPoints: parseFloat(parts[3]) || 1 // default 1 (small) if not specified
    };
  });
}

// Group features into versions based on story points
// Each version: Must have (21 SP) + Nice have (4 SP) = 25 SP max
function planVersions(features) {
  const versions = [];
  let currentVersion = { 
    version: 1, 
    features: [], 
    mustHaveFeatures: [],
    niceHaveFeatures: [],
    totalPoints: 0,
    mustHavePoints: 0,
    niceHavePoints: 0
  };
  
  // Separate Must have and Nice have features
  const mustHaveFeatures = features.filter(f => f.priority === 'Must have');
  const niceHaveFeatures = features.filter(f => f.priority !== 'Must have');
  
  // Sort each group by story points (smaller first for better packing)
  mustHaveFeatures.sort((a, b) => a.storyPoints - b.storyPoints);
  niceHaveFeatures.sort((a, b) => a.storyPoints - b.storyPoints);
  
  // First, allocate Must have features (21 SP per version)
  for (const feature of mustHaveFeatures) {
    if (currentVersion.mustHavePoints + feature.storyPoints > MUST_HAVE_POINTS) {
      // Start new version
      if (currentVersion.features.length > 0) {
        versions.push(currentVersion);
      }
      currentVersion = { 
        version: versions.length + 1, 
        features: [feature],
        mustHaveFeatures: [feature],
        niceHaveFeatures: [],
        totalPoints: feature.storyPoints,
        mustHavePoints: feature.storyPoints,
        niceHavePoints: 0
      };
    } else {
      currentVersion.features.push(feature);
      currentVersion.mustHaveFeatures.push(feature);
      currentVersion.totalPoints += feature.storyPoints;
      currentVersion.mustHavePoints += feature.storyPoints;
    }
  }
  
  // Then, allocate Nice have features to versions (4 SP per version)
  let niceHaveIdx = 0;
  for (let i = 0; i < versions.length; i++) {
    while (niceHaveIdx < niceHaveFeatures.length) {
      const feature = niceHaveFeatures[niceHaveIdx];
      if (versions[i].niceHavePoints + feature.storyPoints <= NICE_HAVE_POINTS) {
        versions[i].features.push(feature);
        versions[i].niceHaveFeatures.push(feature);
        versions[i].totalPoints += feature.storyPoints;
        versions[i].niceHavePoints += feature.storyPoints;
        niceHaveIdx++;
      } else {
        break;
      }
    }
  }
  
  // Add remaining Nice have to current version
  while (niceHaveIdx < niceHaveFeatures.length) {
    const feature = niceHaveFeatures[niceHaveIdx];
    if (currentVersion.niceHavePoints + feature.storyPoints <= NICE_HAVE_POINTS) {
      currentVersion.features.push(feature);
      currentVersion.niceHaveFeatures.push(feature);
      currentVersion.totalPoints += feature.storyPoints;
      currentVersion.niceHavePoints += feature.storyPoints;
      niceHaveIdx++;
    } else {
      // Start new version for remaining nice-to-have
      if (currentVersion.features.length > 0) {
        versions.push(currentVersion);
      }
      currentVersion = { 
        version: versions.length + 1, 
        features: [feature],
        mustHaveFeatures: [],
        niceHaveFeatures: [feature],
        totalPoints: feature.storyPoints,
        mustHavePoints: 0,
        niceHavePoints: feature.storyPoints
      };
      niceHaveIdx++;
    }
  }
  
  // Add last version
  if (currentVersion.features.length > 0 && !versions.includes(currentVersion)) {
    versions.push(currentVersion);
  }
  
  return versions;
}

function detectPersona(input) {
  const text = `${input.idea} ${input.usecase} ${input.target}`.toLowerCase();
  let bestMatch = 'P1';
  let maxScore = 0;
  for (const [key, persona] of Object.entries(PERSONA_STYLES)) {
    let score = persona.keywords.filter(kw => text.includes(kw.toLowerCase())).length;
    if (score > maxScore) { maxScore = score; bestMatch = key; }
  }
  return bestMatch;
}

function extractAgeRange(text) {
  const match = text.match(/(\d{1,2})\s*[-–‑]\s*(\d{1,2})/);
  return match ? `${match[1]}-${match[2]}` : '18-45';
}

function formatDate(d) {
  return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
}

function sanitizeFilename(str) {
  return str.replace(/[^a-zA-Z0-9\u00C0-\u024F\u1E00-\u1EFF ]/g, '').replace(/\s+/g, '_').substring(0, 50);
}

// ==================== MAIN ====================
async function generate(input) {
  const today = new Date();
  const persona = input.persona || detectPersona(input);
  const personaStyle = PERSONA_STYLES[persona];

  // Parse apps and features from input
  const sampleApps = parseApps(input.apps) || [
    ['App 1', 'Reference app description 1'],
    ['App 2', 'Reference app description 2'],
    ['App 3', 'Reference app description 3'],
    ['App 4', 'Reference app description 4'],
    ['App 5', 'Reference app description 5'],
    ['App 6', 'Reference app description 6'],
  ];
  
  const customFeatures = parseFeatures(input.features);
  const defaultNames = DEFAULT_FEATURES.map(f => f.name.toLowerCase());
  const filteredCustom = customFeatures.filter(f => !defaultNames.includes(f.name.toLowerCase()));
  const allFeatures = [...filteredCustom, ...DEFAULT_FEATURES];

  const workbook = new ExcelJS.Workbook();
  workbook.creator = 'BA Agent';

  // Styles
  const headerStyle = {
    font: { bold: true, size: 14, color: { argb: 'FFFFFFFF' } },
    fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF2E75B6' } },
    alignment: { horizontal: 'center', vertical: 'middle' },
    border: { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } }
  };
  const subHeaderStyle = {
    font: { bold: true, size: 11 },
    fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFD9E2F3' } },
    alignment: { horizontal: 'left', vertical: 'middle' },
    border: { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } }
  };
  const cellStyle = {
    fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFFFFFF' } },
    alignment: { vertical: 'middle', wrapText: true },
    border: { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } }
  };

  // ========== SHEET 1: Project Overview ==========
  const ws1 = workbook.addWorksheet('1. Project Overview');
  ws1.columns = [{ width: 25 }, { width: 80 }];
  let row = 1;

  // OVERVIEW
  ws1.mergeCells(`A${row}:B${row}`);
  ws1.getCell(`A${row}`).value = 'OVERVIEW';
  ws1.getCell(`A${row}`).style = headerStyle;
  ws1.getRow(row).height = 25;
  row++;
  ws1.getCell(`A${row}`).value = 'Item';
  ws1.getCell(`B${row}`).value = 'Content';
  ws1.getRow(row).eachCell(c => c.style = subHeaderStyle);

  // Reference App: use first sample app (highest rated) or fallback to search
  const topApp = sampleApps[0] ? sampleApps[0][0] : input.idea;
  const referenceAppLink = input.refapp || `https://play.google.com/store/search?q=${encodeURIComponent(topApp)}`;
  
  [
    ['Project Name', `AAPxxx - ${input.idea}`],
    ['PM in charge', input.pm || 'Phùng Khánh Duy'],
    ['Objective', 'Build IAA product'],
    ['Main Usecase', input.usecase],
    ['Reference App', referenceAppLink],
  ].forEach(([a, b]) => {
    row++;
    ws1.getCell(`A${row}`).value = a;
    ws1.getCell(`B${row}`).value = b;
    ws1.getRow(row).eachCell(c => c.style = cellStyle);
  });

  // USER SEGMENT
  row += 2;
  ws1.mergeCells(`A${row}:B${row}`);
  ws1.getCell(`A${row}`).value = 'USER SEGMENT';
  ws1.getCell(`A${row}`).style = headerStyle;
  ws1.getRow(row).height = 25;
  row++;
  ws1.getCell(`A${row}`).value = 'Factor';
  ws1.getCell(`B${row}`).value = 'Description';
  ws1.getRow(row).eachCell(c => c.style = subHeaderStyle);

  [
    ['Age', extractAgeRange(input.target)],
    ['Relationship', input.relationship || 'Individual'],
    ['Region', input.region || 'India'],
    ['Income', 'Middle – upper middle'],
    ['Core Need', input.coreNeed || input.usecase],
    ['Core Emotion', input.coreEmotion || 'Curious, excited'],
  ].forEach(([a, b]) => {
    row++;
    ws1.getCell(`A${row}`).value = a;
    ws1.getCell(`B${row}`).value = b;
    ws1.getRow(row).eachCell(c => c.style = cellStyle);
  });

  // SAMPLE APP
  row += 2;
  ws1.mergeCells(`A${row}:B${row}`);
  ws1.getCell(`A${row}`).value = 'SAMPLE APP';
  ws1.getCell(`A${row}`).style = headerStyle;
  ws1.getRow(row).height = 25;
  row++;
  ws1.getCell(`A${row}`).value = 'App';
  ws1.getCell(`B${row}`).value = 'Description';
  ws1.getRow(row).eachCell(c => c.style = subHeaderStyle);

  sampleApps.forEach(([a, b]) => {
    row++;
    ws1.getCell(`A${row}`).value = a;
    ws1.getCell(`B${row}`).value = b;
    ws1.getRow(row).eachCell(c => c.style = cellStyle);
  });

  // DESIGN STYLE
  row += 2;
  ws1.mergeCells(`A${row}:B${row}`);
  ws1.getCell(`A${row}`).value = 'DESIGN STYLE';
  ws1.getCell(`A${row}`).style = headerStyle;
  ws1.getRow(row).height = 25;
  row++;
  ws1.getCell(`A${row}`).value = 'Factor';
  ws1.getCell(`B${row}`).value = 'Description';
  ws1.getRow(row).eachCell(c => c.style = subHeaderStyle);

  [
    ['Persona', `${persona} (${personaStyle.name}) - ${personaStyle.description}`],
    ['Primary Style', personaStyle.primaryStyle],
    ['Color Palette', personaStyle.colorPalette],
    ['Typography', personaStyle.typography],
    ['Key UI Element', personaStyle.keyUIElement],
    ['Micro-interactions', personaStyle.microInteractions],
  ].forEach(([a, b]) => {
    row++;
    ws1.getCell(`A${row}`).value = a;
    ws1.getCell(`B${row}`).value = b;
    ws1.getRow(row).eachCell(c => c.style = cellStyle);
  });

  // ========== SHEET 2: Scope & MVP ==========
  const ws2 = workbook.addWorksheet('2. Scope & MVP');
  ws2.columns = [{ width: 30 }, { width: 50 }, { width: 15 }, { width: 12 }];
  row = 1;

  // Plan versions based on story points
  const versions = planVersions(allFeatures);
  const totalPoints = allFeatures.reduce((sum, f) => sum + (f.storyPoints || 5), 0);

  // SCOPE TABLE
  ws2.mergeCells(`A${row}:D${row}`);
  ws2.getCell(`A${row}`).value = 'FEATURE SCOPE';
  ws2.getCell(`A${row}`).style = headerStyle;
  ws2.getRow(row).height = 25;
  row++;
  ['Feature', 'Description', 'Priority', 'Story Points'].forEach((v, i) => {
    ws2.getCell(`${String.fromCharCode(65 + i)}${row}`).value = v;
  });
  ws2.getRow(row).eachCell(c => c.style = subHeaderStyle);

  allFeatures.forEach(({ name, desc, priority, storyPoints }) => {
    row++;
    ws2.getCell(`A${row}`).value = name;
    ws2.getCell(`B${row}`).value = desc;
    ws2.getCell(`C${row}`).value = priority;
    ws2.getCell(`D${row}`).value = storyPoints || 5;
    ws2.getRow(row).eachCell(c => c.style = cellStyle);
    ws2.getCell(`C${row}`).dataValidation = {
      type: 'list', allowBlank: false, formulae: ['"Must have,Nice have"']
    };
    ws2.getCell(`C${row}`).fill = {
      type: 'pattern', pattern: 'solid',
      fgColor: { argb: priority === 'Must have' ? 'FFC6EFCE' : 'FFFFEB9C' }
    };
    ws2.getCell(`D${row}`).alignment = { horizontal: 'center' };
  });

  // Total row
  row++;
  ws2.getCell(`A${row}`).value = 'TOTAL';
  ws2.getCell(`A${row}`).font = { bold: true };
  ws2.mergeCells(`B${row}:C${row}`);
  ws2.getCell(`D${row}`).value = totalPoints;
  ws2.getCell(`D${row}`).font = { bold: true };
  ws2.getCell(`D${row}`).alignment = { horizontal: 'center' };
  ws2.getRow(row).eachCell(c => { c.style = { ...cellStyle }; c.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFD9E2F3' } }; });

  // VERSION ROADMAP - Each version gets its own table with Must have / Nice have separation
  versions.forEach((ver, idx) => {
    row += 2;
    ws2.mergeCells(`A${row}:D${row}`);
    const versionTitle = idx === 0 
      ? `VERSION 1 (MVP) - Must have: ${ver.mustHavePoints || 0} SP | Nice have: ${ver.niceHavePoints || 0} SP | Total: ${ver.totalPoints} SP`
      : `VERSION ${ver.version} - Must have: ${ver.mustHavePoints || 0} SP | Nice have: ${ver.niceHavePoints || 0} SP | Total: ${ver.totalPoints} SP`;
    ws2.getCell(`A${row}`).value = versionTitle;
    ws2.getCell(`A${row}`).style = headerStyle;
    ws2.getRow(row).height = 25;
    
    // Must Have section
    const mustHaveFeatures = ver.mustHaveFeatures || ver.features.filter(f => f.priority === 'Must have');
    if (mustHaveFeatures.length > 0) {
      row++;
      ws2.mergeCells(`A${row}:D${row}`);
      ws2.getCell(`A${row}`).value = `Must Have (${ver.mustHavePoints || mustHaveFeatures.reduce((s, f) => s + (f.storyPoints || 1), 0)} SP)`;
      ws2.getCell(`A${row}`).style = { ...subHeaderStyle, fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFC6EFCE' } } };
      
      row++;
      ['Feature', 'Description', '', 'Story Points'].forEach((v, i) => {
        ws2.getCell(`${String.fromCharCode(65 + i)}${row}`).value = v;
      });
      ws2.getRow(row).eachCell(c => c.style = subHeaderStyle);
      
      mustHaveFeatures.forEach(f => {
        row++;
        ws2.getCell(`A${row}`).value = f.name;
        ws2.getCell(`B${row}`).value = f.desc;
        ws2.mergeCells(`B${row}:C${row}`);
        ws2.getCell(`D${row}`).value = f.storyPoints || 5;
        ws2.getRow(row).eachCell(c => c.style = cellStyle);
        ws2.getCell(`D${row}`).alignment = { horizontal: 'center' };
      });
    }
    
    // Nice Have section
    const niceHaveFeatures = ver.niceHaveFeatures || ver.features.filter(f => f.priority !== 'Must have');
    if (niceHaveFeatures.length > 0) {
      row++;
      ws2.mergeCells(`A${row}:D${row}`);
      ws2.getCell(`A${row}`).value = `Nice Have (${ver.niceHavePoints || niceHaveFeatures.reduce((s, f) => s + (f.storyPoints || 1), 0)} SP)`;
      ws2.getCell(`A${row}`).style = { ...subHeaderStyle, fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFFEB9C' } } };
      
      row++;
      ['Feature', 'Description', '', 'Story Points'].forEach((v, i) => {
        ws2.getCell(`${String.fromCharCode(65 + i)}${row}`).value = v;
      });
      ws2.getRow(row).eachCell(c => c.style = subHeaderStyle);
      
      niceHaveFeatures.forEach(f => {
        row++;
        ws2.getCell(`A${row}`).value = f.name;
        ws2.getCell(`B${row}`).value = f.desc;
        ws2.mergeCells(`B${row}:C${row}`);
        ws2.getCell(`D${row}`).value = f.storyPoints || 5;
        ws2.getRow(row).eachCell(c => c.style = cellStyle);
        ws2.getCell(`D${row}`).alignment = { horizontal: 'center' };
      });
    }
    
    // Subtotal row for this version
    row++;
    ws2.getCell(`A${row}`).value = 'Version Subtotal';
    ws2.getCell(`A${row}`).font = { bold: true };
    ws2.mergeCells(`B${row}:C${row}`);
    ws2.getCell(`D${row}`).value = ver.totalPoints;
    ws2.getCell(`D${row}`).font = { bold: true };
    ws2.getCell(`D${row}`).alignment = { horizontal: 'center' };
    ws2.getRow(row).eachCell(c => { 
      c.style = { ...cellStyle }; 
      c.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE2EFDA' } }; 
    });
  });

  // OUT OF SCOPE
  row += 2;
  ws2.mergeCells(`A${row}:D${row}`);
  ws2.getCell(`A${row}`).value = 'OUT OF SCOPE';
  ws2.getCell(`A${row}`).style = headerStyle;
  ws2.getRow(row).height = 25;
  row++;
  ws2.getCell(`A${row}`).value = 'Item';
  ws2.getCell(`B${row}`).value = 'Reason';
  ws2.mergeCells(`B${row}:D${row}`);
  ws2.getRow(row).eachCell(c => c.style = subHeaderStyle);

  [
    ['CMS Management', 'Develop after user base established'],
    ['Social Features', 'Not in MVP scope'],
    ['Cloud Sync', 'Complex, develop later'],
  ].forEach(([a, b]) => {
    row++;
    ws2.getCell(`A${row}`).value = a;
    ws2.getCell(`B${row}`).value = b;
    ws2.mergeCells(`B${row}:D${row}`);
    ws2.getRow(row).eachCell(c => c.style = cellStyle);
  });

  // ========== SHEET 3: Timeline ==========
  const ws3 = workbook.addWorksheet('3. Timeline');
  ws3.columns = [{ width: 20 }, { width: 15 }, { width: 40 }];
  row = 1;

  ws3.mergeCells(`A${row}:C${row}`);
  ws3.getCell(`A${row}`).value = 'TIMELINE';
  ws3.getCell(`A${row}`).style = headerStyle;
  ws3.getRow(row).height = 25;
  row++;
  ['Phase', 'Date', 'Output'].forEach((v, i) => {
    ws3.getCell(`${String.fromCharCode(65 + i)}${row}`).value = v;
  });
  ws3.getRow(row).eachCell(c => c.style = subHeaderStyle);

  const testDate = new Date(today); testDate.setDate(testDate.getDate() + 2);
  const launchDate = new Date(testDate); launchDate.setDate(launchDate.getDate() + 2);

  [
    ['Kickoff & Align', formatDate(today), 'Complete UI/UX Design'],
    ['Build MVP', formatDate(today), 'Dev done with all features'],
    ['Test / Validate', formatDate(testDate), 'Release-ready build'],
    ['Launch MVP', formatDate(launchDate), 'Live on Store'],
  ].forEach(([a, b, c]) => {
    row++;
    ws3.getCell(`A${row}`).value = a;
    ws3.getCell(`B${row}`).value = b;
    ws3.getCell(`C${row}`).value = c;
    ws3.getRow(row).eachCell(c => c.style = cellStyle);
  });

  // Save XLSX
  const outputDir = input.output || process.cwd();
  const baseFilename = `AAPxxx_${sanitizeFilename(input.idea)}_Kickoff`;
  const xlsxPath = path.join(outputDir, `${baseFilename}.xlsx`);
  await workbook.xlsx.writeFile(xlsxPath);

  // Generate Markdown
  const fs = require('fs');
  const mdTestDate = new Date(today); mdTestDate.setDate(mdTestDate.getDate() + 2);
  const mdLaunchDate = new Date(mdTestDate); mdLaunchDate.setDate(mdLaunchDate.getDate() + 2);
  
  const overviewData = [
    ['Project Name', `AAPxxx - ${input.idea}`],
    ['PM in charge', input.pm || 'Phùng Khánh Duy'],
    ['Objective', 'Build IAA product'],
    ['Main Usecase', input.usecase],
    ['Reference App', referenceAppLink],
  ];
  
  const userSegmentData = [
    ['Age', extractAgeRange(input.target)],
    ['Relationship', input.relationship || 'Individual'],
    ['Region', input.region || 'India'],
    ['Income', 'Middle – upper middle'],
    ['Core Need', input.coreNeed || input.usecase],
    ['Core Emotion', input.coreEmotion || 'Curious, excited'],
  ];
  
  const designStyleData = [
    ['Persona', `${persona} (${personaStyle.name}) - ${personaStyle.description}`],
    ['Primary Style', personaStyle.primaryStyle],
    ['Color Palette', personaStyle.colorPalette],
    ['Typography', personaStyle.typography],
    ['Key UI Element', personaStyle.keyUIElement],
    ['Micro-interactions', personaStyle.microInteractions],
  ];
  
  const outOfScopeData = [
    ['CMS Management', 'Develop after user base established'],
    ['Social Features', 'Not in MVP scope'],
    ['Cloud Sync', 'Complex, develop later'],
  ];
  
  const timelineData = [
    ['Kickoff & Align', formatDate(today), 'Complete UI/UX Design'],
    ['Build MVP', formatDate(today), 'Dev done with all features'],
    ['Test / Validate', formatDate(mdTestDate), 'Release-ready build'],
    ['Launch MVP', formatDate(mdLaunchDate), 'Live on Store'],
  ];

  const md = `# Project Kickoff: ${input.idea}

## 1. Project Overview

### OVERVIEW
| Item | Content |
|------|---------|
${overviewData.map(([a, b]) => `| ${a} | ${b} |`).join('\n')}

### USER SEGMENT
| Factor | Description |
|--------|-------------|
${userSegmentData.map(([a, b]) => `| ${a} | ${b} |`).join('\n')}

### SAMPLE APP
| App | Description |
|-----|-------------|
${sampleApps.map(([a, b]) => `| ${a} | ${b} |`).join('\n')}

### DESIGN STYLE
| Factor | Description |
|--------|-------------|
${designStyleData.map(([a, b]) => `| ${a} | ${b} |`).join('\n')}

---

## 2. Scope & MVP

### FEATURE SCOPE
| Feature | Description | Priority | Story Points |
|---------|-------------|----------|--------------|
${allFeatures.map(({ name, desc, priority, storyPoints }) => `| ${name} | ${desc} | ${priority} | ${storyPoints || 5} |`).join('\n')}
| **TOTAL** | | | **${allFeatures.reduce((sum, f) => sum + (f.storyPoints || 5), 0)}** |

### VERSION ROADMAP

> **Structure:** Each version = 25 SP max (Must have: 21 SP + Nice have: 4 SP)
> 
> **Summary:** ${versions.length} version(s) planned | Total: ${allFeatures.reduce((sum, f) => sum + (f.storyPoints || 5), 0)} Story Points

${versions.map((ver, idx) => `
---

### ${idx === 0 ? 'VERSION 1 (MVP)' : `VERSION ${ver.version}`}

| Category | Story Points |
|----------|--------------|
| Must have | ${ver.mustHavePoints || 0} SP |
| Nice have | ${ver.niceHavePoints || 0} SP |
| **Total** | **${ver.totalPoints} SP** |

#### Must Have Features (${ver.mustHavePoints || 0} SP)

| Feature | Description | Story Points |
|---------|-------------|--------------|
${(ver.mustHaveFeatures || ver.features.filter(f => f.priority === 'Must have')).map(f => `| ${f.name} | ${f.desc} | ${f.storyPoints || 5} |`).join('\n') || '| — | No must-have features | — |'}

#### Nice Have Features (${ver.niceHavePoints || 0} SP)

| Feature | Description | Story Points |
|---------|-------------|--------------|
${(ver.niceHaveFeatures || ver.features.filter(f => f.priority !== 'Must have')).map(f => `| ${f.name} | ${f.desc} | ${f.storyPoints || 5} |`).join('\n') || '| — | No nice-have features | — |'}`).join('\n')}

### OUT OF SCOPE
| Item | Reason |
|------|--------|
${outOfScopeData.map(([a, b]) => `| ${a} | ${b} |`).join('\n')}

---

## 3. Timeline

| Phase | Date | Output |
|-------|------|--------|
${timelineData.map(([a, b, c]) => `| ${a} | ${b} | ${c} |`).join('\n')}
`;

  const mdPath = path.join(outputDir, `${baseFilename}.md`);
  fs.writeFileSync(mdPath, md);

  console.log(`✅ Files created:`);
  console.log(`   📊 ${xlsxPath}`);
  console.log(`   📄 ${mdPath}`);
  console.log(`🎭 Persona: ${persona} (${personaStyle.name})`);
  console.log(`📱 Sample Apps: ${sampleApps.length}`);
  console.log(`⚙️ Features: ${allFeatures.length} (${customFeatures.length} custom + ${DEFAULT_FEATURES.length} default)`);
  console.log(`📊 Story Points: ${totalPoints} total → ${versions.length} version(s)`);
  
  return { xlsx: xlsxPath, md: mdPath };
}

// ==================== CLI ====================
const args = parseArgs();

if (!args.idea && !args.usecase) {
  console.log(`
Usage: node generate.js --idea "App Name" [--usecase "Description"] [--target "User segment"]

Required (at least one):
  --idea      Product name
  --usecase   Main usecase

Optional (will use defaults if not provided):
  --target    Target users (default: "Users 18-45")
  --apps      Sample apps "App1:Desc1,App2:Desc2,App3:Desc3"
  --features  Features "Name1:Desc1:Must have,Name2:Desc2:Nice have"
  --persona   Force persona P1-P7
  --pm        PM name
  --refapp    Reference app store link
  --output    Output directory
`);
  process.exit(1);
}

// Auto-fill missing fields
if (!args.idea) args.idea = 'AI App';
if (!args.usecase) args.usecase = args.idea;
if (!args.target) args.target = 'Users 18-45';

generate(args).catch(e => { console.error('❌', e.message); process.exit(1); });

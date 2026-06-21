#!/usr/bin/env node
/**
 * Translate XLSX content to English
 * Reads xlsx file, finds Vietnamese text, outputs what needs translation
 * 
 * Usage: node translate.js --file "path/to/file.xlsx"
 */

const ExcelJS = require('exceljs');
const path = require('path');

// Vietnamese character detection regex
const VIETNAMESE_REGEX = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]/;

// Common Vietnamese phrases -> English translations
const TRANSLATIONS = {
  // Overview
  'Tổng quan dự án': 'Project Overview',
  'TỔNG QUAN': 'OVERVIEW',
  'Hạng mục': 'Item',
  'Nội dung': 'Content',
  'Tên dự án': 'Project Name',
  'PM phụ trách': 'PM in charge',
  'Mục tiêu': 'Objective',
  'Usecase chính': 'Main Usecase',
  'App tham khảo': 'Reference App',
  'Xây dựng sản phẩm IAA': 'Build IAA product',
  
  // User Segment
  'Yếu tố': 'Factor',
  'Mô tả': 'Description',
  'Cá nhân': 'Individual',
  'Việt Nam, Đông Nam Á': 'Vietnam, Southeast Asia',
  'Trung bình – khá': 'Middle – upper middle',
  'Tò mò, hứng thú': 'Curious, excited',
  
  // Sample App
  'Mô tả app tham khảo': 'Reference app description',
  'App tham khảo 1': 'Reference app 1',
  'App tham khảo 2': 'Reference app 2',
  'App tham khảo 3': 'Reference app 3',
  'App tham khảo 4': 'Reference app 4',
  'App tham khảo 5': 'Reference app 5',
  'App tham khảo 6': 'Reference app 6',
  
  // Scope
  'Phạm vi & MVP': 'Scope & MVP',
  'PHẠM VI': 'SCOPE',
  'Tính năng': 'Feature',
  'Ưu tiên': 'Priority',
  'Lấy config từ Firebase': 'Fetch config from Firebase',
  'Tracking user behavior (Firebase Analytics)': 'Track user behavior (Firebase Analytics)',
  'Hỗ trợ đa ngôn ngữ (VI, EN, ...)': 'Multi-language support (VI, EN, ...)',
  'Hiển thị quảng cáo khi mở app lần đầu': 'Show ads on first app open',
  'Gói premium (không giới hạn, không ads)': 'Premium package (unlimited, ad-free)',
  'Service xử lý (self-hosted hoặc API)': 'Processing service (self-hosted or API)',
  
  // Out of Scope
  'Lý do': 'Reason',
  'CMS quản lý': 'CMS Management',
  'Phát triển sau khi có user base': 'Develop after user base established',
  'Không nằm trong MVP': 'Not in MVP scope',
  'Phức tạp, phát triển sau': 'Complex, develop later',
  
  // Timeline
  'Giai đoạn': 'Phase',
  'Thời gian': 'Date',
  'UI/UX Design hoàn chỉnh': 'Complete UI/UX Design',
  'Bản dev done đủ các feature': 'Dev done with all features',
  'Bản sẵn sàng để release': 'Release-ready build',
  'Bản trên Store': 'Live on Store',
  
  // Persona descriptions
  'Người dùng muốn lưu giữ và hoài niệm ký ức': 'Users who want to preserve and cherish memories',
  'Người dùng chuyên nghiệp, công việc': 'Professional users, work-focused',
  'Người dùng trẻ, năng động': 'Young, dynamic users',
  'Người dùng yêu thích anime, gaming': 'Anime and gaming enthusiasts',
  'Người dùng quan tâm làm đẹp': 'Beauty and skincare enthusiasts',
  'Designer, creative professional': 'Designers, creative professionals',
};

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

function containsVietnamese(text) {
  if (typeof text !== 'string') return false;
  return VIETNAMESE_REGEX.test(text);
}

function translateText(text) {
  if (typeof text !== 'string') return text;
  
  // Direct translation lookup
  if (TRANSLATIONS[text]) {
    return TRANSLATIONS[text];
  }
  
  // Partial replacements
  let result = text;
  for (const [vi, en] of Object.entries(TRANSLATIONS)) {
    if (result.includes(vi)) {
      result = result.replace(vi, en);
    }
  }
  
  return result;
}

async function translateFile(filePath) {
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.readFile(filePath);
  
  let totalCells = 0;
  let vietnameseCells = 0;
  let translatedCells = 0;
  const untranslated = [];
  
  workbook.eachSheet((worksheet, sheetId) => {
    // Translate sheet name
    if (containsVietnamese(worksheet.name)) {
      const newName = translateText(worksheet.name);
      if (newName !== worksheet.name) {
        console.log(`📄 Sheet "${worksheet.name}" → "${newName}"`);
        worksheet.name = newName;
      }
    }
    
    worksheet.eachRow((row, rowNumber) => {
      row.eachCell((cell, colNumber) => {
        totalCells++;
        const value = cell.value;
        
        if (typeof value === 'string' && containsVietnamese(value)) {
          vietnameseCells++;
          const translated = translateText(value);
          
          if (translated !== value && !containsVietnamese(translated)) {
            cell.value = translated;
            translatedCells++;
            console.log(`✅ [${worksheet.name}!${cell.address}] "${value}" → "${translated}"`);
          } else if (containsVietnamese(translated)) {
            untranslated.push({
              sheet: worksheet.name,
              cell: cell.address,
              value: value
            });
          }
        }
      });
    });
  });
  
  // Save file
  await workbook.xlsx.writeFile(filePath);
  
  console.log('\n' + '='.repeat(50));
  console.log(`📊 SUMMARY`);
  console.log(`   Total cells: ${totalCells}`);
  console.log(`   Vietnamese found: ${vietnameseCells}`);
  console.log(`   Auto-translated: ${translatedCells}`);
  console.log(`   Untranslated: ${untranslated.length}`);
  
  if (untranslated.length > 0) {
    console.log('\n⚠️ NEEDS MANUAL TRANSLATION:');
    untranslated.forEach(({ sheet, cell, value }) => {
      console.log(`   [${sheet}!${cell}] "${value}"`);
    });
  } else {
    console.log('\n✅ All content is now in English!');
  }
  
  return { totalCells, vietnameseCells, translatedCells, untranslated };
}

// CLI
const args = parseArgs();

if (!args.file) {
  console.log(`
Usage: node translate.js --file "path/to/file.xlsx"

This script:
1. Reads the XLSX file
2. Finds Vietnamese text
3. Translates to English using built-in dictionary
4. Saves the file
5. Reports any untranslated text
`);
  process.exit(1);
}

translateFile(args.file)
  .then(result => {
    if (result.untranslated.length > 0) {
      process.exit(2); // Partial success
    }
  })
  .catch(e => {
    console.error('❌', e.message);
    process.exit(1);
  });

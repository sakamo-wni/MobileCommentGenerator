// Script to compare locations between CSV and regions.ts

import { LOCATION_COORDINATES } from './shared/src/config/regions';
import { LOCATION_CONFIG } from './shared/src/config/constants';
import * as fs from 'fs';
import * as path from 'path';

type LocationName = keyof typeof LOCATION_COORDINATES;

// Function to read CSV and extract location names
function readCSVLocations(csvPath: string): string[] {
  try {
    const csvContent = fs.readFileSync(csvPath, 'utf-8');
    const lines = csvContent.split('\n').filter(line => line.trim());
    // Skip header line
    const locations = lines.slice(1).map(line => {
      const columns = line.split(',');
      return columns[0]?.trim();
    }).filter(Boolean);
    return locations;
  } catch (error) {
    console.error(`❌ CSVファイルの読み込みエラー: ${error}`);
    return [];
  }
}

// Main comparison function
function compareLocations() {
  // Read locations from CSV
  const csvPath = path.join(__dirname, 'src/data/location_coordinates.csv');
  const csvLocations = readCSVLocations(csvPath);
  
  // Get locations from regions.ts
  const regionsLocations = Object.keys(LOCATION_COORDINATES) as LocationName[];
  
  // Find locations in CSV but not in regions.ts
  const missingInRegions = csvLocations.filter(loc => !regionsLocations.includes(loc as LocationName));
  
  // Find locations in regions.ts but not in CSV
  const missingInCSV = regionsLocations.filter(loc => !csvLocations.includes(loc));
  
  console.log(`CSVの地点数: ${csvLocations.length}`);
  console.log(`regions.tsの地点数: ${regionsLocations.length}`);
  console.log(`期待される地点数: ${LOCATION_CONFIG.EXPECTED_COUNT}`);
  
  // Check if counts match expected
  const csvCountMismatch = csvLocations.length !== LOCATION_CONFIG.EXPECTED_COUNT;
  const tsCountMismatch = regionsLocations.length !== LOCATION_CONFIG.EXPECTED_COUNT;
  
  if (csvCountMismatch) {
    console.log(`\n⚠️  CSVの地点数が期待値と異なります: ${csvLocations.length} (期待値: ${LOCATION_CONFIG.EXPECTED_COUNT})`);
  }
  
  if (tsCountMismatch) {
    console.log(`\n⚠️  regions.tsの地点数が期待値と異なります: ${regionsLocations.length} (期待値: ${LOCATION_CONFIG.EXPECTED_COUNT})`);
  }
  
  if (missingInRegions.length > 0) {
    console.log(`\n❌ 検証失敗: CSV内の ${missingInRegions.length} 地点が regions.ts に存在しません`);
    missingInRegions.forEach(loc => console.log(`- ${loc}`));
  }
  
  if (missingInCSV.length > 0) {
    console.log(`\n❌ 検証失敗: regions.ts内の ${missingInCSV.length} 地点が CSV に存在しません`);
    missingInCSV.forEach(loc => console.log(`- ${loc}`));
  }
  
  if (missingInRegions.length === 0 && missingInCSV.length === 0 && !csvCountMismatch && !tsCountMismatch) {
    console.log('\n✅ 検証成功: CSVとregions.tsの全地点が同期されています');
  }
  
  // Return exit code based on validation result
  return missingInRegions.length > 0 || missingInCSV.length > 0 ? 1 : 0;
}

// Execute if run directly
if (require.main === module) {
  const exitCode = compareLocations();
  process.exit(exitCode);
}

export { compareLocations };
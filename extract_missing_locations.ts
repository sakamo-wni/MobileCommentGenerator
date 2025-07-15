// Script to extract missing locations with their coordinates from CSV

import { LOCATION_COORDINATES } from './shared/src/config/regions';
import * as fs from 'fs';
import * as path from 'path';

type LocationName = keyof typeof LOCATION_COORDINATES;

interface LocationData {
  prefecture: string;
  latitude: number;
  longitude: number;
}

// Read and parse CSV file
function readCSVData(csvPath: string): Record<string, LocationData> {
  const csvContent = fs.readFileSync(csvPath, 'utf8');
  const lines = csvContent.trim().split('\n');
  
  // Parse CSV data (skip header)
  const csvData: Record<string, LocationData> = {};
  for (let i = 1; i < lines.length; i++) {
    const [location, prefecture, latitude, longitude] = lines[i].split(',');
    if (location && prefecture && latitude && longitude) {
      csvData[location] = {
        prefecture,
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude)
      };
    }
  }
  
  return csvData;
}

// Main function to extract missing locations
function extractMissingLocations() {
  const csvPath = path.join(__dirname, 'src/data/location_coordinates.csv');
  const csvData = readCSVData(csvPath);
  
  // Get current locations from regions.ts
  const currentLocations = Object.keys(LOCATION_COORDINATES) as LocationName[];
  
  // Find locations in CSV but not in regions.ts
  const allCSVLocations = Object.keys(csvData);
  const missingLocations = allCSVLocations.filter(loc => !currentLocations.includes(loc as LocationName));
  
  if (missingLocations.length === 0) {
    console.log('✅ 不足地点なし: CSV内の全地点がregions.tsに存在します');
    return;
  }
  
  console.log('❌ CSVに存在するがregions.tsに不足している地点:\n');
  console.log('```typescript');
  missingLocations.forEach(location => {
    const data = csvData[location];
    if (data) {
      console.log(`  '${location}': { latitude: ${data.latitude}, longitude: ${data.longitude} }, // ${data.prefecture}`);
    }
  });
  console.log('```');
  
  // Also create a summary by prefecture
  console.log('\n\n都道府県別まとめ:');
  const byPrefecture: Record<string, string[]> = {};
  missingLocations.forEach(location => {
    const data = csvData[location];
    if (data) {
      if (!byPrefecture[data.prefecture]) {
        byPrefecture[data.prefecture] = [];
      }
      byPrefecture[data.prefecture].push(location);
    }
  });
  
  Object.entries(byPrefecture).sort().forEach(([prefecture, locations]) => {
    console.log(`${prefecture}: ${locations.join(', ')}`);
  });
  
  console.log(`\n不足地点総数: ${missingLocations.length}`);
}

// Execute if run directly
if (require.main === module) {
  extractMissingLocations();
}

export { extractMissingLocations };
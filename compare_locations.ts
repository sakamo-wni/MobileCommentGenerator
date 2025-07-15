// Script to compare locations between CSV and regions.ts

import { LOCATION_COORDINATES } from './shared/src/config/regions';
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
    console.error(`Error reading CSV file: ${error}`);
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
  
  console.log(`Total locations in CSV: ${csvLocations.length}`);
  console.log(`Total locations in regions.ts: ${regionsLocations.length}`);
  
  if (missingInRegions.length > 0) {
    console.log(`\nLocations in CSV but not in regions.ts: ${missingInRegions.length}`);
    missingInRegions.forEach(loc => console.log(`- ${loc}`));
  }
  
  if (missingInCSV.length > 0) {
    console.log(`\nLocations in regions.ts but not in CSV: ${missingInCSV.length}`);
    missingInCSV.forEach(loc => console.log(`- ${loc}`));
  }
  
  if (missingInRegions.length === 0 && missingInCSV.length === 0) {
    console.log('\n✅ All locations are synchronized between CSV and regions.ts');
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
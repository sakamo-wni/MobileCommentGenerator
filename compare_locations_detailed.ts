// Detailed script to compare locations across all data sources

import { LOCATION_COORDINATES, REGIONS } from './shared/src/config/regions';
import * as fs from 'fs';
import * as path from 'path';

type LocationName = keyof typeof LOCATION_COORDINATES;

interface ComparisonResult {
  source: string;
  count: number;
  locations: string[];
}

// Read locations from various sources
function readChitenCSV(csvPath: string): string[] {
  const content = fs.readFileSync(csvPath, 'utf8');
  return content.trim().split('\n').map(line => line.trim()).filter(line => line);
}

function readLocationCoordinatesCSV(csvPath: string): string[] {
  const content = fs.readFileSync(csvPath, 'utf8');
  const lines = content.trim().split('\n');
  return lines.slice(1).map(line => line.split(',')[0]).filter(Boolean);
}

// Extract all locations from REGIONS structure
function extractLocationsFromRegions(): string[] {
  const locations: string[] = [];
  Object.values(REGIONS).forEach(region => {
    Object.values(region).forEach(prefectureLocations => {
      locations.push(...prefectureLocations);
    });
  });
  return [...new Set(locations)]; // Remove duplicates
}

// Main comparison function
function compareAllLocationSources() {
  const basePath = __dirname;
  
  // Read from TypeScript regions.ts
  const tsLocations = Object.keys(LOCATION_COORDINATES) as string[];
  const tsRegionsLocations = extractLocationsFromRegions();
  
  // Read from CSV files
  const chitenPath = path.join(basePath, 'src/data/Chiten.csv');
  const chitenLocations = readChitenCSV(chitenPath);
  
  const coordsPath = path.join(basePath, 'src/data/location_coordinates.csv');
  const coordsLocations = readLocationCoordinatesCSV(coordsPath);
  
  // Python location_selector.py regions (hardcoded for comparison)
  const pythonRegions = {
    "北海道": ["稚内", "旭川", "留萌", "札幌", "岩見沢", "倶知安", "網走", "北見", "紋別", "根室", "釧路", "帯広", "室蘭", "浦河", "函館", "江差"],
    "東北": ["青森", "むつ", "八戸", "盛岡", "宮古", "大船渡", "秋田", "横手", "仙台", "白石", "山形", "米沢", "酒田", "新庄", "福島", "小名浜", "若松"],
    "北陸": ["新潟", "長岡", "高田", "相川", "金沢", "輪島", "富山", "伏木", "福井", "敦賀"],
    "関東": ["東京", "大島", "八丈島", "父島", "横浜", "小田原", "さいたま", "熊谷", "秩父", "千葉", "銚子", "館山", "水戸", "土浦", "前橋", "みなかみ", "宇都宮", "大田原"],
    "甲信": ["長野", "松本", "飯田", "甲府", "河口湖"],
    "東海": ["名古屋", "豊橋", "静岡", "網代", "三島", "浜松", "岐阜", "高山", "津", "尾鷲"],
    "近畿": ["大阪", "神戸", "豊岡", "京都", "舞鶴", "奈良", "風屋", "大津", "彦根", "和歌山", "潮岬"],
    "中国": ["広島", "庄原", "岡山", "津山", "下関", "山口", "柳井", "萩", "松江", "浜田", "西郷", "鳥取", "米子"],
    "四国": ["松山", "新居浜", "宇和島", "高松", "徳島", "日和佐", "高知", "室戸岬", "清水"],
    "九州": ["福岡", "八幡", "飯塚", "久留米", "大分", "中津", "日田", "長崎", "佐世保", "厳原", "福江", "佐賀", "伊万里", "熊本", "阿蘇乙姫", "牛深", "宮崎", "延岡", "都城", "高千穂", "鹿児島", "鹿屋", "種子島", "名瀬", "沖永良部"],
    "沖縄": ["那覇", "名護", "久米島", "宮古島", "石垣島", "与那国島", "大東島"]
  };
  
  const pythonLocations = Object.values(pythonRegions).flat();
  
  // Convert to Sets for comparison
  const tsSet = new Set(tsLocations);
  const tsRegionsSet = new Set(tsRegionsLocations);
  const chitenSet = new Set(chitenLocations);
  const coordsSet = new Set(coordsLocations);
  const pythonSet = new Set(pythonLocations);
  
  console.log('=== Location Data Comparison ===\n');
  console.log(`TypeScript LOCATION_COORDINATES: ${tsLocations.length}`);
  console.log(`TypeScript REGIONS: ${tsRegionsLocations.length}`);
  console.log(`Chiten.csv locations: ${chitenLocations.length}`);
  console.log(`location_coordinates.csv locations: ${coordsLocations.length}`);
  console.log(`Python location_selector.py: ${pythonLocations.length}`);
  
  // Compare TypeScript sources
  const tsCoordNotInRegions = [...tsSet].filter(loc => !tsRegionsSet.has(loc));
  if (tsCoordNotInRegions.length > 0) {
    console.log('\n⚠️  Locations in LOCATION_COORDINATES but NOT in REGIONS:');
    console.log(tsCoordNotInRegions.sort().join(', '));
  }
  
  const tsRegionsNotInCoord = [...tsRegionsSet].filter(loc => !tsSet.has(loc));
  if (tsRegionsNotInCoord.length > 0) {
    console.log('\n⚠️  Locations in REGIONS but NOT in LOCATION_COORDINATES:');
    console.log(tsRegionsNotInCoord.sort().join(', '));
  }
  
  // Compare with CSV files
  const comparisons: Array<[string, Set<string>, string, Set<string>]> = [
    ['TypeScript', tsSet, 'Chiten.csv', chitenSet],
    ['TypeScript', tsSet, 'location_coordinates.csv', coordsSet],
    ['TypeScript', tsSet, 'Python location_selector.py', pythonSet],
  ];
  
  comparisons.forEach(([source1, set1, source2, set2]) => {
    const inSource1NotInSource2 = [...set1].filter(loc => !set2.has(loc));
    const inSource2NotInSource1 = [...set2].filter(loc => !set1.has(loc));
    
    if (inSource1NotInSource2.length > 0) {
      console.log(`\n=== Locations in ${source1} but NOT in ${source2} ===`);
      console.log(inSource1NotInSource2.sort().join(', '));
      console.log(`Total: ${inSource1NotInSource2.length}`);
    }
    
    if (inSource2NotInSource1.length > 0) {
      console.log(`\n=== Locations in ${source2} but NOT in ${source1} ===`);
      console.log(inSource2NotInSource1.sort().join(', '));
      console.log(`Total: ${inSource2NotInSource1.length}`);
    }
  });
  
  // Summary
  const allSynchronized = 
    tsLocations.length === chitenLocations.length &&
    tsLocations.length === coordsLocations.length &&
    tsCoordNotInRegions.length === 0 &&
    tsRegionsNotInCoord.length === 0;
  
  if (allSynchronized) {
    console.log('\n✅ All location data sources are synchronized!');
  } else {
    console.log('\n❌ Location data sources have discrepancies');
  }
  
  return allSynchronized ? 0 : 1;
}

// Execute if run directly
if (require.main === module) {
  const exitCode = compareAllLocationSources();
  process.exit(exitCode);
}

export { compareAllLocationSources };
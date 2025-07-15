// Script to extract missing locations with their coordinates from CSV

const fs = require('fs');

// Read and parse CSV file
const csvContent = fs.readFileSync('/Users/sakamo/Desktop/sandbox/MobileCommentGenerator/src/data/location_coordinates.csv', 'utf8');
const lines = csvContent.trim().split('\n');

// Parse CSV data (skip header)
const csvData = {};
for (let i = 1; i < lines.length; i++) {
  const [location, prefecture, latitude, longitude] = lines[i].split(',');
  csvData[location] = {
    prefecture,
    latitude: parseFloat(latitude),
    longitude: parseFloat(longitude)
  };
}

// Missing locations identified
const missingLocations = [
  '苫小牧', '深浦', '二戸', '一関', '古川', '石巻', '気仙沼', '相馬', '白河',
  '御前崎', '三重', '諏訪', '軽井沢', '姫路', '洲本', '呉', '福山', '池田',
  '佐伯', '人吉', '油津', '阿久根', '枕崎'
];

console.log('Missing locations with their coordinates from CSV:\n');
console.log('```typescript');
missingLocations.forEach(location => {
  const data = csvData[location];
  if (data) {
    console.log(`  '${location}': { latitude: ${data.latitude}, longitude: ${data.longitude} }, // ${data.prefecture}`);
  }
});
console.log('```');

// Also create a summary by prefecture
console.log('\n\nSummary by prefecture:');
const byPrefecture = {};
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
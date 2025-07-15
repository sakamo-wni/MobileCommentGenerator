const fs = require('fs');

// Read TypeScript file and extract location names
const tsContent = fs.readFileSync('/Users/sakamo/Desktop/sandbox/MobileCommentGenerator/shared/src/config/regions.ts', 'utf8');
const tsLocationMatches = tsContent.match(/'([^']+)':\s*\{\s*latitude:/g);
const tsLocations = tsLocationMatches ? tsLocationMatches.map(match => match.match(/'([^']+)'/)[1]) : [];

// Read CSV files
const chitenContent = fs.readFileSync('/Users/sakamo/Desktop/sandbox/MobileCommentGenerator/src/data/Chiten.csv', 'utf8');
const chitenLocations = chitenContent.trim().split('\n').map(line => line.trim()).filter(line => line);

const coordsCsvContent = fs.readFileSync('/Users/sakamo/Desktop/sandbox/MobileCommentGenerator/src/data/location_coordinates.csv', 'utf8');
const coordsLines = coordsCsvContent.trim().split('\n');
const coordsLocations = coordsLines.slice(1).map(line => line.split(',')[0]);

// Convert to Sets for comparison
const tsSet = new Set(tsLocations);
const chitenSet = new Set(chitenLocations);
const coordsSet = new Set(coordsLocations);

console.log('=== Location Data Comparison ===\n');
console.log(`TypeScript locations: ${tsLocations.length}`);
console.log(`Chiten.csv locations: ${chitenLocations.length}`);
console.log(`location_coordinates.csv locations: ${coordsLocations.length}`);

// Find locations in TypeScript but not in Chiten.csv
const tsNotInChiten = [...tsSet].filter(loc => !chitenSet.has(loc));
console.log('\n=== Locations in TypeScript but NOT in Chiten.csv ===');
if (tsNotInChiten.length > 0) {
  console.log(tsNotInChiten.sort().join(', '));
  console.log(`Total: ${tsNotInChiten.length}`);
} else {
  console.log('None - all TypeScript locations are in Chiten.csv');
}

// Find locations in Chiten.csv but not in TypeScript
const chitenNotInTs = [...chitenSet].filter(loc => !tsSet.has(loc));
console.log('\n=== Locations in Chiten.csv but NOT in TypeScript ===');
if (chitenNotInTs.length > 0) {
  console.log(chitenNotInTs.sort().join(', '));
  console.log(`Total: ${chitenNotInTs.length}`);
} else {
  console.log('None - all Chiten.csv locations are in TypeScript');
}

// Find locations in TypeScript but not in location_coordinates.csv
const tsNotInCoords = [...tsSet].filter(loc => !coordsSet.has(loc));
console.log('\n=== Locations in TypeScript but NOT in location_coordinates.csv ===');
if (tsNotInCoords.length > 0) {
  console.log(tsNotInCoords.sort().join(', '));
  console.log(`Total: ${tsNotInCoords.length}`);
} else {
  console.log('None - all TypeScript locations are in location_coordinates.csv');
}

// Check if Python region data matches TypeScript
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
const pythonSet = new Set(pythonLocations);

console.log('\n=== Python location_selector.py Region Comparison ===');
console.log(`Python locations total: ${pythonLocations.length}`);

const pythonNotInTs = [...pythonSet].filter(loc => !tsSet.has(loc));
console.log('\n=== Locations in Python but NOT in TypeScript ===');
if (pythonNotInTs.length > 0) {
  console.log(pythonNotInTs.sort().join(', '));
  console.log(`Total: ${pythonNotInTs.length}`);
} else {
  console.log('None - all Python locations are in TypeScript');
}

const tsNotInPython = [...tsSet].filter(loc => !pythonSet.has(loc));
console.log('\n=== Locations in TypeScript but NOT in Python ===');
if (tsNotInPython.length > 0) {
  console.log(tsNotInPython.sort().join(', '));
  console.log(`Total: ${tsNotInPython.length}`);
} else {
  console.log('None - all TypeScript locations are in Python');
}
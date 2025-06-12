// constants/locations.ts - Location constants and utilities

export const REGIONS = [
  '北海道',
  '東北', 
  '北陸',
  '関東',
  '甲信',
  '東海',
  '近畿',
  '中国',
  '四国',
  '九州',
  '沖縄'
]

// Area name mapping for location classification based on the new structure
const AREA_MAPPINGS: Record<string, string> = {
  // 北海道
  '稚内': '北海道',
  '旭川': '北海道',  
  '留萌': '北海道',
  '札幌': '北海道',
  '岩見沢': '北海道',
  '倶知安': '北海道',
  '網走': '北海道',
  '北見': '北海道',
  '紋別': '北海道',
  '根室': '北海道',
  '釧路': '北海道',
  '帯広': '北海道',
  '室蘭': '北海道',
  '浦河': '北海道',
  '函館': '北海道',
  '江差': '北海道',

  // 東北
  '青森': '東北',
  'むつ': '東北',
  '八戸': '東北',
  '盛岡': '東北',
  '宮古': '東北',
  '大船渡': '東北',
  '秋田': '東北',
  '横手': '東北',
  '仙台': '東北',
  '白石': '東北',
  '山形': '東北',
  '米沢': '東北',
  '酒田': '東北',
  '新庄': '東北',
  '福島': '東北',
  '小名浜': '東北',
  '若松': '東北',

  // 北陸
  '新潟': '北陸',
  '長岡': '北陸',
  '高田': '北陸',
  '相川': '北陸',
  '金沢': '北陸',
  '輪島': '北陸',
  '富山': '北陸',
  '伏木': '北陸',
  '福井': '北陸',
  '敦賀': '北陸',

  // 関東
  '東京': '関東',
  '大島': '関東',
  '八丈島': '関東',
  '父島': '関東',
  '横浜': '関東',
  '小田原': '関東',
  'さいたま': '関東',
  '熊谷': '関東',
  '秩父': '関東',
  '千葉': '関東',
  '銚子': '関東',
  '館山': '関東',
  '水戸': '関東',
  '土浦': '関東',
  '前橋': '関東',
  'みなかみ': '関東',
  '宇都宮': '関東',
  '大田原': '関東',

  // 甲信
  '長野': '甲信',
  '松本': '甲信',
  '飯田': '甲信',
  '甲府': '甲信',
  '河口湖': '甲信',

  // 東海
  '名古屋': '東海',
  '豊橋': '東海',
  '静岡': '東海',
  '網代': '東海',
  '三島': '東海',
  '浜松': '東海',
  '岐阜': '東海',
  '高山': '東海',
  '津': '東海',
  '尾鷲': '東海',

  // 近畿
  '大阪': '近畿',
  '神戸': '近畿',
  '豊岡': '近畿',
  '京都': '近畿',
  '舞鶴': '近畿',
  '奈良': '近畿',
  '風屋': '近畿',
  '大津': '近畿',
  '彦根': '近畿',
  '和歌山': '近畿',
  '潮岬': '近畿',

  // 中国
  '広島': '中国',
  '庄原': '中国',
  '岡山': '中国',
  '津山': '中国',
  '下関': '中国',
  '山口': '中国',
  '柳井': '中国',
  '萩': '中国',
  '松江': '中国',
  '浜田': '中国',
  '西郷': '中国',
  '鳥取': '中国',
  '米子': '中国',

  // 四国
  '松山': '四国',
  '新居浜': '四国',
  '宇和島': '四国',
  '高松': '四国',
  '徳島': '四国',
  '日和佐': '四国',
  '高知': '四国',
  '室戸岬': '四国',
  '清水': '四国',

  // 九州
  '福岡': '九州',
  '八幡': '九州',
  '飯塚': '九州',
  '久留米': '九州',
  '佐賀': '九州',
  '伊万里': '九州',
  '長崎': '九州',
  '佐世保': '九州',
  '厳原': '九州',
  '福江': '九州',
  '大分': '九州',
  '中津': '九州',
  '日田': '九州',
  '佐伯': '九州',
  '熊本': '九州',
  '阿蘇乙姫': '九州',
  '牛深': '九州',
  '人吉': '九州',
  '宮崎': '九州',
  '都城': '九州',
  '延岡': '九州',
  '高千穂': '九州',
  '鹿児島': '九州',
  '鹿屋': '九州',
  '種子島': '九州',
  '名瀬': '九州',

  // 沖縄
  '那覇': '沖縄',
  '名護': '沖縄',
  '久米島': '沖縄',
  '大東島': '沖縄',
  '宮古島': '沖縄',
  '石垣島': '沖縄',
  '与那国島': '沖縄'
}

/**
 * Get area name for a given location
 * @param locationName - Name of the location
 * @returns Area name or empty string if not found
 */
export const getAreaName = (locationName: string): string => {
  // Remove common suffixes for better matching
  const cleanName = locationName.replace(/[県市町村郡区]$/, '')
  
  // Try exact match first
  if (AREA_MAPPINGS[cleanName]) {
    return AREA_MAPPINGS[cleanName]
  }
  
  // Try partial match
  for (const [key, value] of Object.entries(AREA_MAPPINGS)) {
    if (cleanName.includes(key) || key.includes(cleanName)) {
      return value
    }
  }
  
  return ''
}

/**
 * Get all locations for a specific region
 * @param region - Region name
 * @returns Array of location names in that region
 */
export const getLocationsByRegion = (region: string): string[] => {
  return Object.entries(AREA_MAPPINGS)
    .filter(([_, area]) => area === region)
    .map(([location, _]) => location)
}

export default {
  REGIONS,
  getAreaName,
  getLocationsByRegion
}
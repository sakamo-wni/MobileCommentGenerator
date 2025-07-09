// 統一された地域区分と地点データ（座標情報付き）

export interface LocationData {
  name: string;
  latitude: number;
  longitude: number;
  area?: string;
  prefecture?: string;
}

// 地点座標データ
export const LOCATION_COORDINATES: Record<string, { latitude: number; longitude: number }> = {
  '稚内': { latitude: 45.4166166, longitude: 141.6771991 },
  '旭川': { latitude: 43.7627501, longitude: 142.3579263 },
  '留萌': { latitude: 43.941029, longitude: 141.6368171 },
  '札幌': { latitude: 43.0686365, longitude: 141.3509218 },
  '岩見沢': { latitude: 43.2042912, longitude: 141.759545 },
  '倶知安': { latitude: 42.9020963, longitude: 140.7451832 },
  '網走': { latitude: 44.0201193, longitude: 144.2542397 },
  '北見': { latitude: 43.8049279, longitude: 143.8972642 },
  '紋別': { latitude: 42.802866, longitude: 141.41406 },
  '根室': { latitude: 43.326823, longitude: 145.5828156 },
  '釧路': { latitude: 42.9906837, longitude: 144.3820381 },
  '帯広': { latitude: 42.9181018, longitude: 143.2020215 },
  '室蘭': { latitude: 42.3178489, longitude: 140.9757765 },
  '浦河': { latitude: 42.16833, longitude: 142.76833 },
  '函館': { latitude: 41.7737872, longitude: 140.7261884 },
  '江差': { latitude: 41.86917, longitude: 140.12750 },
  '青森': { latitude: 40.8299549, longitude: 140.7340975 },
  'むつ': { latitude: 41.0547594, longitude: 140.9426405 },
  '八戸': { latitude: 40.5093889, longitude: 141.4311833 },
  '盛岡': { latitude: 39.7014998, longitude: 141.1365544 },
  '宮古': { latitude: 39.6398721, longitude: 141.9475248 },
  '大船渡': { latitude: 39.08187, longitude: 141.70851 },
  '秋田': { latitude: 39.7168833, longitude: 140.1296657 },
  '横手': { latitude: 39.310336, longitude: 140.5604929 },
  '仙台': { latitude: 38.2598541, longitude: 140.8827459 },
  '白石': { latitude: 38.0030467, longitude: 140.6263277 },
  '山形': { latitude: 38.2484701, longitude: 140.3278031 },
  '米沢': { latitude: 37.9094604, longitude: 140.1284431 },
  '酒田': { latitude: 38.9219999, longitude: 139.8460919 },
  '新庄': { latitude: 38.76389, longitude: 140.31222 },
  '福島': { latitude: 37.7441923, longitude: 140.4674528 },
  '小名浜': { latitude: 36.94618, longitude: 140.9058 },
  '若松': { latitude: 37.48806, longitude: 139.91278 },
  '新潟': { latitude: 37.9161924, longitude: 139.0221838 },
  '長岡': { latitude: 37.4328926, longitude: 138.8513097 },
  '高田': { latitude: 37.109464, longitude: 138.254276 },
  '相川': { latitude: 38.013446, longitude: 138.24406 },
  '金沢': { latitude: 36.5610256, longitude: 136.656205 },
  '輪島': { latitude: 37.4040598, longitude: 136.8942335 },
  '富山': { latitude: 36.694064, longitude: 137.2137071 },
  '伏木': { latitude: 36.79028, longitude: 137.05500 },
  '福井': { latitude: 36.0598178, longitude: 136.221641 },
  '敦賀': { latitude: 35.654656, longitude: 136.060788 },
  '東京': { latitude: 35.6812362, longitude: 139.7671248 },
  '大島': { latitude: 34.7502771, longitude: 139.3547859 },
  '八丈島': { latitude: 33.10944, longitude: 139.78556 },
  '父島': { latitude: 27.090769, longitude: 142.18996 },
  '横浜': { latitude: 35.4477711, longitude: 139.6425194 },
  '小田原': { latitude: 35.2548464, longitude: 139.1525671 },
  'さいたま': { latitude: 35.8617292, longitude: 139.6454822 },
  '熊谷': { latitude: 36.147302, longitude: 139.3868095 },
  '秩父': { latitude: 35.9988461, longitude: 139.0850089 },
  '千葉': { latitude: 35.6050925, longitude: 140.1233935 },
  '銚子': { latitude: 35.734699, longitude: 140.8633038 },
  '館山': { latitude: 34.9827357, longitude: 139.8644477 },
  '水戸': { latitude: 36.36617, longitude: 140.471059 },
  '土浦': { latitude: 36.0787829, longitude: 140.2127123 },
  '前橋': { latitude: 36.3894796, longitude: 139.0634285 },
  'みなかみ': { latitude: 36.678931, longitude: 138.999648 },
  '宇都宮': { latitude: 36.5588848, longitude: 139.8820967 },
  '大田原': { latitude: 36.87111, longitude: 140.01639 },
  '長野': { latitude: 36.6513215, longitude: 138.1808244 },
  '松本': { latitude: 36.237603, longitude: 137.9719895 },
  '飯田': { latitude: 35.514834, longitude: 137.821533 },
  '甲府': { latitude: 35.6635113, longitude: 138.5707723 },
  '河口湖': { latitude: 35.5011111, longitude: 138.7550000 },
  '名古屋': { latitude: 35.1667146, longitude: 136.9066238 },
  '豊橋': { latitude: 34.7691802, longitude: 137.3866838 },
  '静岡': { latitude: 34.9769529, longitude: 138.3831127 },
  '網代': { latitude: 35.04699, longitude: 139.08917 },
  '三島': { latitude: 35.11814, longitude: 138.91865 },
  '浜松': { latitude: 34.703757, longitude: 137.7383511 },
  '岐阜': { latitude: 35.4232133, longitude: 136.7606141 },
  '高山': { latitude: 36.145617, longitude: 137.252151 },
  '津': { latitude: 34.7185086, longitude: 136.5055679 },
  '尾鷲': { latitude: 34.0630587, longitude: 136.1905066 },
  '彦根': { latitude: 35.2764895, longitude: 136.2411041 },
  '京都': { latitude: 35.0212466, longitude: 135.7555968 },
  '舞鶴': { latitude: 35.449495, longitude: 135.3630176 },
  '大阪': { latitude: 34.7024854, longitude: 135.4937619 },
  '神戸': { latitude: 34.6896171, longitude: 135.1956453 },
  '豊岡': { latitude: 35.541111, longitude: 134.816944 },
  '奈良': { latitude: 34.683608, longitude: 135.8048553 },
  '風屋': { latitude: 34.05806, longitude: 135.79694 },
  '和歌山': { latitude: 34.228343, longitude: 135.1636574 },
  '潮岬': { latitude: 33.45000, longitude: 135.75667 },
  '大津': { latitude: 35.0044506, longitude: 135.8686788 },
  '徳島': { latitude: 34.0584833, longitude: 134.5548274 },
  '日和佐': { latitude: 33.730347, longitude: 134.542584 },
  '高松': { latitude: 34.3493055, longitude: 134.046594 },
  '松山': { latitude: 33.8423056, longitude: 132.7656972 },
  '新居浜': { latitude: 33.96028, longitude: 133.28306 },
  '宇和島': { latitude: 33.227027, longitude: 132.5429882 },
  '高知': { latitude: 33.5597078, longitude: 133.5311114 },
  '室戸岬': { latitude: 33.25611, longitude: 134.15250 },
  '清水': { latitude: 32.78333, longitude: 132.95000 }
} as const

// 地域区分データ（シンプルなキー名を使用）
export const REGIONS = {
  '北海道': {
    '道北': ['稚内', '旭川', '留萌'],
    '道央': ['札幌', '岩見沢', '倶知安'],
    '道東': ['網走', '北見', '紋別', '根室', '釧路', '帯広'],
    '道南': ['室蘭', '浦河', '函館', '江差']
  },
  '東北': {
    '青森': ['青森', 'むつ', '八戸'],
    '岩手': ['盛岡', '宮古', '大船渡'],
    '秋田': ['秋田', '横手'],
    '宮城': ['仙台', '白石'],
    '山形': ['山形', '米沢', '酒田', '新庄'],
    '福島': ['福島', '小名浜', '若松']
  },
  '北陸': {
    '新潟': ['新潟', '長岡', '高田', '相川'],
    '石川': ['金沢', '輪島'],
    '富山': ['富山', '伏木'],
    '福井': ['福井', '敦賀']
  },
  '関東': {
    '東京': ['東京', '大島', '八丈島', '父島'],
    '神奈川': ['横浜', '小田原'],
    '埼玉': ['さいたま', '熊谷', '秩父'],
    '千葉': ['千葉', '銚子', '館山'],
    '茨城': ['水戸', '土浦'],
    '群馬': ['前橋', 'みなかみ'],
    '栃木': ['宇都宮', '大田原']
  },
  '甲信': {
    '長野': ['長野', '松本', '飯田'],
    '山梨': ['甲府', '河口湖']
  },
  '東海': {
    '愛知': ['名古屋', '豊橋'],
    '静岡': ['静岡', '網代', '三島', '浜松'],
    '岐阜': ['岐阜', '高山'],
    '三重': ['津', '尾鷲']
  },
  '近畿': {
    '滋賀': ['大津', '彦根'],
    '京都': ['京都', '舞鶴'],
    '大阪': ['大阪'],
    '兵庫': ['神戸', '豊岡'],
    '奈良': ['奈良', '風屋'],
    '和歌山': ['和歌山', '潮岬']
  },
  '四国': {
    '徳島': ['徳島', '日和佐'],
    '香川': ['高松'],
    '愛媛': ['松山', '新居浜', '宇和島'],
    '高知': ['高知', '室戸岬', '清水']
  }
} as const

// 地域の拡張キー名（Nuxt版との互換性のため）
export const REGIONS_EXTENDED_KEYS = {
  '北海道': {
    '北・東日本（道北）': REGIONS['北海道']['道北'],
    '北・東日本（道央）': REGIONS['北海道']['道央'],
    '北・東日本（道東）': REGIONS['北海道']['道東'],
    '北・東日本（道南）': REGIONS['北海道']['道南']
  },
  '東北': {
    '北・東日本（青森）': REGIONS['東北']['青森'],
    '北・東日本（岩手）': REGIONS['東北']['岩手'],
    '北・東日本（秋田）': REGIONS['東北']['秋田'],
    '北・東日本（宮城）': REGIONS['東北']['宮城'],
    '北・東日本（山形）': REGIONS['東北']['山形'],
    '北・東日本（福島）': REGIONS['東北']['福島']
  },
  '北陸': {
    '北・東日本（新潟）': REGIONS['北陸']['新潟'],
    '北・東日本（石川）': REGIONS['北陸']['石川'],
    '北・東日本（富山）': REGIONS['北陸']['富山'],
    '北・東日本（福井）': REGIONS['北陸']['福井']
  },
  '関東': {
    '北・東日本（東京）': REGIONS['関東']['東京'],
    '北・東日本（神奈川）': REGIONS['関東']['神奈川'],
    '北・東日本（埼玉）': REGIONS['関東']['埼玉'],
    '北・東日本（千葉）': REGIONS['関東']['千葉'],
    '北・東日本（茨城）': REGIONS['関東']['茨城'],
    '北・東日本（群馬）': REGIONS['関東']['群馬'],
    '北・東日本（栃木）': REGIONS['関東']['栃木']
  },
  '甲信': {
    '北・東日本（長野）': REGIONS['甲信']['長野'],
    '北・東日本（山梨）': REGIONS['甲信']['山梨']
  },
  '東海': {
    '北・東日本（愛知）': REGIONS['東海']['愛知'],
    '北・東日本（静岡）': REGIONS['東海']['静岡'],
    '北・東日本（岐阜）': REGIONS['東海']['岐阜'],
    '北・東日本（三重）': REGIONS['東海']['三重']
  },
  '近畿': {
    '西日本（滋賀）': REGIONS['近畿']['滋賀'],
    '西日本（京都）': REGIONS['近畿']['京都'],
    '西日本（大阪）': REGIONS['近畿']['大阪'],
    '西日本（兵庫）': REGIONS['近畿']['兵庫'],
    '西日本（奈良）': REGIONS['近畿']['奈良'],
    '西日本（和歌山）': REGIONS['近畿']['和歌山']
  },
  '四国': {
    '西日本（徳島）': REGIONS['四国']['徳島'],
    '西日本（香川）': REGIONS['四国']['香川'],
    '西日本（愛媛）': REGIONS['四国']['愛媛'],
    '西日本（高知）': REGIONS['四国']['高知']
  }
} as const

// ヘルパー関数：地点データを取得
export function getLocationData(name: string): LocationData | undefined {
  const coords = LOCATION_COORDINATES[name]
  if (!coords) return undefined
  
  // 都道府県を特定
  let prefecture: string | undefined
  let area: string | undefined
  
  for (const [region, prefectures] of Object.entries(REGIONS)) {
    for (const [pref, locations] of Object.entries(prefectures)) {
      if (locations.includes(name)) {
        prefecture = pref
        area = region
        break
      }
    }
    if (prefecture) break
  }
  
  return {
    name,
    latitude: coords.latitude,
    longitude: coords.longitude,
    area,
    prefecture
  }
}

// すべての地点名を取得
export function getAllLocationNames(): string[] {
  return Object.keys(LOCATION_COORDINATES)
}
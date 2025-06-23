// 地域区分による地点データ（気象庁の正式な区分に基づく）
export const REGIONS = {
  '北海道': {
    '北・東日本（道北）': ['稚内', '旭川', '留萌'],
    '北・東日本（道央）': ['札幌', '岩見沢', '倶知安'],
    '北・東日本（道東）': ['網走', '北見', '紋別', '根室', '釧路', '帯広'],
    '北・東日本（道南）': ['室蘭', '浦河', '函館', '江差']
  },
  '東北': {
    '北・東日本（青森）': ['青森', 'むつ', '八戸'],
    '北・東日本（岩手）': ['盛岡', '宮古', '大船渡'],
    '北・東日本（秋田）': ['秋田', '横手'],
    '北・東日本（宮城）': ['仙台', '白石'],
    '北・東日本（山形）': ['山形', '米沢', '酒田', '新庄'],
    '北・東日本（福島）': ['福島', '小名浜', '若松']
  },
  '北陸': {
    '北・東日本（新潟）': ['新潟', '長岡', '高田', '相川'],
    '北・東日本（石川）': ['金沢', '輪島'],
    '北・東日本（富山）': ['富山', '伏木'],
    '北・東日本（福井）': ['福井', '敦賀']
  },
  '関東': {
    '北・東日本（東京）': ['東京', '大島', '八丈島', '父島'],
    '北・東日本（神奈川）': ['横浜', '小田原'],
    '北・東日本（埼玉）': ['さいたま', '熊谷', '秩父'],
    '北・東日本（千葉）': ['千葉', '銚子', '館山'],
    '北・東日本（茨城）': ['水戸', '土浦'],
    '北・東日本（群馬）': ['前橋', 'みなかみ'],
    '北・東日本（栃木）': ['宇都宮', '大田原']
  },
  '甲信': {
    '北・東日本（長野）': ['長野', '松本', '飯田'],
    '北・東日本（山梨）': ['甲府', '河口湖']
  },
  '東海': {
    '北・東日本（愛知）': ['名古屋', '豊橋'],
    '北・東日本（静岡）': ['静岡', '網代', '三島', '浜松'],
    '北・東日本（岐阜）': ['岐阜', '高山'],
    '北・東日本（三重）': ['津', '尾鷲']
  },
  '近畿': {
    '西日本（大阪）': ['大阪'],
    '西日本（兵庫）': ['神戸', '豊岡'],
    '西日本（京都）': ['京都', '舞鶴'],
    '西日本（奈良）': ['奈良', '風屋'],
    '西日本（滋賀）': ['大津', '彦根'],
    '西日本（和歌山）': ['和歌山', '潮岬']
  },
  '中国': {
    '西日本（広島）': ['広島', '庄原'],
    '西日本（岡山）': ['岡山', '津山'],
    '西日本（山口）': ['下関', '山口', '柳井', '萩'],
    '西日本（島根）': ['松江', '浜田', '西郷'],
    '西日本（鳥取）': ['鳥取', '米子']
  },
  '四国': {
    '西日本（愛媛）': ['松山', '新居浜', '宇和島'],
    '西日本（香川）': ['高松'],
    '西日本（徳島）': ['徳島', '日和佐'],
    '西日本（高知）': ['高知', '室戸岬', '清水']
  },
  '九州': {
    '西日本（福岡）': ['福岡', '八幡', '飯塚', '久留米'],
    '西日本（佐賀）': ['佐賀', '伊万里'],
    '西日本（長崎）': ['長崎', '佐世保', '厳原', '福江'],
    '西日本（大分）': ['大分', '中津', '日田', '佐伯'],
    '西日本（熊本）': ['熊本', '阿蘇乙姫', '牛深', '人吉'],
    '西日本（宮崎）': ['宮崎', '都城', '延岡', '高千穂'],
    '西日本（鹿児島）': ['鹿児島', '鹿屋', '種子島', '名瀬']
  },
  '沖縄': {
    '西日本（沖縄）': ['那覇', '名護', '久米島', '大東島', '宮古島', '石垣島', '与那国島']
  }
}

// フラットな地点リストを取得
export function getAllLocations(): string[] {
  const locations: string[] = []
  Object.values(REGIONS).forEach(region => {
    Object.values(region).forEach(locations_list => {
      locations.push(...locations_list)
    })
  })
  return locations.sort()
}

// 地域別地点選択用のオプション
export function getRegionOptions() {
  const options: Array<{label: string, children: Array<{label: string, children: Array<{label: string, value: string}>}>}> = []
  
  Object.entries(REGIONS).forEach(([regionName, prefectures]) => {
    const prefectureOptions = Object.entries(prefectures).map(([prefName, locations]) => ({
      label: prefName,
      children: locations.map(location => ({
        label: location,
        value: location
      }))
    }))
    
    options.push({
      label: regionName,
      children: prefectureOptions
    })
  })
  
  return options
}

// 簡略化された地域名マッピング（UI用）
export const SIMPLIFIED_REGIONS = {
  '北海道': '北海道',
  '東北': '東北', 
  '北陸': '北陸',
  '関東': '関東',
  '甲信': '甲信',
  '東海': '東海',
  '近畿': '近畿',
  '中国': '中国',
  '四国': '四国',
  '九州': '九州',
  '沖縄': '沖縄'
}

// 地域ごとの地点を一括選択
export function getLocationsByRegion(regionName: string): string[] {
  const region = REGIONS[regionName as keyof typeof REGIONS]
  if (!region) return []
  
  const locations: string[] = []
  Object.values(region).forEach(locationList => {
    locations.push(...locationList)
  })
  return locations
}

// 県ごとの地点を一括選択
export function getLocationsByPrefecture(regionName: string, prefectureName: string): string[] {
  const region = REGIONS[regionName as keyof typeof REGIONS]
  if (!region) return []

  return region[prefectureName as keyof typeof region] || []
}

// 全地点を表示順で取得
export function getLocationOrder(): string[] {
  const order: string[] = []
  Object.values(REGIONS).forEach(region => {
    Object.values(region).forEach(locations => {
      order.push(...locations)
    })
  })
  return order
}

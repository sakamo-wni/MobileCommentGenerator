// 地域区分による地点データ
export const REGIONS = {
  '北海道': {
    '道北': ['稚内', '旭川', '留萌'],
    '道央': ['札幌', '岩見沢', '倶知安'],
    '道東': ['網走', '北見', '門別', '根室', '釧路', '帯広'],
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
    '大阪': ['大阪'],
    '兵庫': ['神戸', '豊岡'],
    '京都': ['京都', '舞鶴'],
    '奈良': ['奈良', '風屋'],
    '滋賀': ['大津', '彦根'],
    '和歌山': ['和歌山', '潮岬']
  },
  '中国': {
    '広島': ['広島', '庄原'],
    '岡山': ['岡山', '津山'],
    '山口': ['下関', '山口', '柳井', '萩'],
    '島根': ['松江', '浜田', '西郷'],
    '鳥取': ['鳥取', '米子']
  },
  '四国': {
    '愛媛': ['松山', '新居浜', '宇和島'],
    '香川': ['高松'],
    '徳島': ['徳島', '日和佐'],
    '高知': ['高知', '室戸岬', '清水']
  },
  '九州': {
    '福岡': ['福岡', '八幡', '飯塚', '久留米'],
    '佐賀': ['佐賀', '伊万里'],
    '長崎': ['長崎', '佐世保', '厳原', '福江'],
    '大分': ['大分', '中津', '日田', '佐伯'],
    '熊本': ['熊本', '阿蘇乙姫', '牛深', '人吉'],
    '宮崎': ['宮崎', '都城', '延岡', '高千穂'],
    '鹿児島': ['鹿児島', '鹿屋', '種子島', '名瀬']
  },
  '沖縄': {
    '沖縄': ['那覇', '名護', '久米島', '大東島', '宮古島', '石垣島', '与那国島']
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
/**
 * Location Selection Composable
 * 
 * Vue版とReact版で共通のロケーション選択ロジックを提供
 * フレームワーク依存を排除した純粋なビジネスロジック
 */

import type { Location } from '../types';

// APIクライアントの型定義
export interface LocationApiClient {
  fetchLocations: () => Promise<{ success: boolean; data?: Location[] }>;
}

export interface LocationSelectionState {
  locations: Location[];
  selectedLocations: string[];
  isLoading: boolean;
  error: string | null;
  selectedRegion: string;
}

export interface LocationSelectionActions {
  loadLocations: () => Promise<void>;
  toggleLocation: (locationName: string) => void;
  selectAllLocations: () => void;
  clearAllSelections: () => void;
  selectRegionLocations: (region: string) => void;
  setSelectedRegion: (region: string) => void;
  getFilteredLocations: () => Location[];
  getRegionLocations: (region: string) => string[];
}

// 完全なLocation Selection Logicの型
export interface LocationSelectionLogic extends LocationSelectionState, LocationSelectionActions {
  setApiClient: (client: LocationApiClient) => void;
}

// 地域定数（統一）
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
] as const;

// 地点名から地域を取得するマッピング（frontend/public/地点名.csvの全142地点）
const LOCATION_TO_REGION_MAP: Record<string, string> = {
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
  '与那国島': '沖縄',
};

/**
 * 地点名から地域名を取得
 */
export function getAreaName(locationName: string): string {
  return LOCATION_TO_REGION_MAP[locationName] || '不明';
}

/**
 * 地域ごとの地点リストを取得
 */
export function getLocationsByRegion(region: string): string[] {
  return Object.entries(LOCATION_TO_REGION_MAP)
    .filter(([_, area]) => area === region)
    .map(([location]) => location);
}

/**
 * すべての地点を取得
 */
export function getAllLocationNames(): string[] {
  return Object.keys(LOCATION_TO_REGION_MAP);
}

/**
 * CSVファイルから地点データを読み込む（フォールバック用）
 */
export async function loadLocationsFromCSV(csvUrl: string = '/地点名.csv'): Promise<Location[]> {
  try {
    const response = await fetch(csvUrl);
    const text = await response.text();
    const lines = text.split('\n').filter(line => line.trim());
    
    return lines.slice(1).map(line => {
      const [name, lat, lon] = line.split(',');
      const trimmedName = name.trim();
      return {
        id: trimmedName,
        name: trimmedName,
        prefecture: '',
        region: getAreaName(trimmedName),
        latitude: lat ? parseFloat(lat) : 0,
        longitude: lon ? parseFloat(lon) : 0,
      };
    });
  } catch (error) {
    console.error('Failed to load CSV:', error);
    throw new Error('地点データの読み込みに失敗しました');
  }
}

/**
 * Location Selection Composableを作成
 * フレームワーク非依存の純粋なロジック実装
 */
export function createLocationSelectionLogic(
  initialState: Partial<LocationSelectionState> = {}
): LocationSelectionLogic {
  // 状態の初期化
  const state: LocationSelectionState = {
    locations: [],
    selectedLocations: [],
    isLoading: false,
    error: null,
    selectedRegion: '',
    ...initialState
  };

  // メモ化用のキャッシュ
  let filteredLocationsCache: { key: string; value: Location[] } | null = null;
  let regionLocationsCache: Map<string, string[]> = new Map();

  // APIクライアント（後で注入）
  let apiClient: LocationApiClient | null = null;

  // APIクライアントを設定
  const setApiClient = (client: LocationApiClient) => {
    apiClient = client;
  };

  // 地点データを読み込む
  const loadLocations = async () => {
    // キャッシュをクリア
    filteredLocationsCache = null;
    regionLocationsCache.clear();
    
    state.isLoading = true;
    state.error = null;
    
    try {
      if (apiClient) {
        const response = await apiClient.fetchLocations();
        if (response.success && response.data) {
          state.locations = response.data;
          // デフォルトで全地点を選択
          state.selectedLocations = response.data.map(loc => loc.name);
          return;
        }
      }
      
      // APIが利用できない場合は、CSVファイルから読み込む
      const csvLocations = await loadLocationsFromCSV();
      state.locations = csvLocations;
      state.selectedLocations = csvLocations.map(loc => loc.name);
      
    } catch (err) {
      console.error('Failed to load locations:', err);
      state.error = '地点データの読み込みに失敗しました';
      
      // フォールバック: 事前定義された地点を使用
      const fallbackLocations = getAllLocationNames().map(name => ({
        id: name,
        name: name,
        prefecture: '',
        region: getAreaName(name),
        latitude: 0,
        longitude: 0,
      }));
      state.locations = fallbackLocations;
      state.selectedLocations = fallbackLocations.map(loc => loc.name);
    } finally {
      state.isLoading = false;
    }
  };

  // 地点の選択をトグル
  const toggleLocation = (locationName: string) => {
    const index = state.selectedLocations.indexOf(locationName);
    if (index > -1) {
      state.selectedLocations.splice(index, 1);
    } else {
      state.selectedLocations.push(locationName);
    }
  };

  // すべての地点を選択
  const selectAllLocations = () => {
    const filtered = getFilteredLocations();
    state.selectedLocations = filtered.map(loc => loc.name);
  };

  // すべての選択をクリア
  const clearAllSelections = () => {
    state.selectedLocations = [];
  };

  // 地域の地点を選択
  const selectRegionLocations = (region: string) => {
    const regionLocationNames = getLocationsByRegion(region);
    const allSelected = regionLocationNames.every(name => 
      state.selectedLocations.includes(name)
    );
    
    if (allSelected) {
      // すべて選択されている場合は選択解除
      state.selectedLocations = state.selectedLocations.filter(name => 
        !regionLocationNames.includes(name)
      );
    } else {
      // 選択されていない地点を追加
      const newLocations = regionLocationNames.filter(name => 
        !state.selectedLocations.includes(name)
      );
      state.selectedLocations = [...state.selectedLocations, ...newLocations];
    }
  };

  // 選択された地域を設定
  const setSelectedRegion = (region: string) => {
    state.selectedRegion = region;
  };

  // フィルタリングされた地点を取得（メモ化付き）
  const getFilteredLocations = () => {
    const cacheKey = `${state.selectedRegion}-${state.locations.length}`;
    
    // キャッシュが有効かチェック
    if (filteredLocationsCache && filteredLocationsCache.key === cacheKey) {
      return filteredLocationsCache.value;
    }
    
    // フィルタリングを実行
    let result: Location[];
    if (!state.selectedRegion) {
      result = state.locations;
    } else {
      result = state.locations.filter(location => {
        const area = location.region || getAreaName(location.name);
        return area === state.selectedRegion;
      });
    }
    
    // キャッシュを更新
    filteredLocationsCache = { key: cacheKey, value: result };
    return result;
  };

  // 地域の地点を取得（状態から）（メモ化付き）
  const getRegionLocations = (region: string) => {
    // キャッシュから取得
    if (regionLocationsCache.has(region)) {
      return regionLocationsCache.get(region)!;
    }
    
    // 計算してキャッシュに保存
    const result = state.locations
      .filter(location => {
        const area = location.region || getAreaName(location.name);
        return area === region;
      })
      .map(loc => loc.name);
    
    regionLocationsCache.set(region, result);
    return result;
  };

  return {
    // 状態
    ...state,
    
    // アクション
    loadLocations,
    toggleLocation,
    selectAllLocations,
    clearAllSelections,
    selectRegionLocations,
    setSelectedRegion,
    getFilteredLocations,
    getRegionLocations,
    setApiClient,
  };
}
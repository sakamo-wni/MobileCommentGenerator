/**
 * Location Selection Composable
 * 
 * Vue版とReact版で共通のロケーション選択ロジックを提供
 * フレームワーク依存を排除した純粋なビジネスロジック
 */

import type { Location } from '../types';
import { REGIONS as REGION_DATA, getLocationData, getAllLocationNames } from '../config/regions';

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

// 地域名の配列（UIで使用）
export const REGION_NAMES = Object.keys(REGION_DATA) as string[];

/**
 * 地点名から地域名を取得
 */
export function getAreaName(locationName: string): string {
  const locationData = getLocationData(locationName);
  return locationData?.area || '不明';
}

/**
 * 地域ごとの地点リストを取得
 */
export function getLocationsByRegion(region: string): string[] {
  const locations: string[] = [];
  const regionData = REGION_DATA as any;
  if (regionData[region]) {
    Object.values(regionData[region]).forEach((locationList: any) => {
      locations.push(...locationList);
    });
  }
  return locations;
}

/**
 * CSVファイルから地点データを読み込む（フォールバック用）
 */
export async function loadLocationsFromCSV(csvUrl: string = '/地点名.csv'): Promise<Location[]> {
  try {
    const response = await fetch(csvUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch CSV: ${response.status} ${response.statusText}`);
    }
    const text = await response.text();
    const lines = text.split('\n');
    
    const locations: Location[] = [];
    
    // ヘッダー行をスキップして、各行を処理
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      const [name, latitude, longitude] = line.split(',');
      if (!name) continue;
      
      const location: Location = {
        id: name,
        name: name.trim(),
        prefecture: '',
        region: getAreaName(name.trim()),
        latitude: parseFloat(latitude) || 0,
        longitude: parseFloat(longitude) || 0,
      };
      
      locations.push(location);
    }
    
    return locations;
  } catch (error) {
    console.error('Failed to load CSV:', error);
    // フォールバック: ハードコードされた地点データを使用
    return getAllLocationNames().map(name => ({
      id: name,
      name: name,
      prefecture: '',
      region: getAreaName(name),
      latitude: 0,
      longitude: 0,
    }));
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

  // APIクライアント（後で注入）
  let apiClient: LocationApiClient | null = null;

  // APIクライアントを設定
  const setApiClient = (client: LocationApiClient) => {
    apiClient = client;
  };

  // 地点データを読み込む
  const loadLocations = async () => {
    state.isLoading = true;
    state.error = null;
    
    try {
      // 確実に142地点を取得
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

  // フィルタリングされた地点を取得
  const getFilteredLocations = () => {
    if (!state.selectedRegion) {
      return state.locations;
    }
    
    return state.locations.filter(location => {
      const area = location.region || getAreaName(location.name);
      return area === state.selectedRegion;
    });
  };

  // 地域の地点を取得（状態から）
  const getRegionLocations = (region: string) => {
    return state.locations
      .filter(location => {
        const area = location.region || getAreaName(location.name);
        return area === region;
      })
      .map(loc => loc.name);
  };

  return {
    // 状態 - getterとして公開
    get locations() { return state.locations; },
    get selectedLocations() { return state.selectedLocations; },
    get isLoading() { return state.isLoading; },
    get error() { return state.error; },
    get selectedRegion() { return state.selectedRegion; },
    
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
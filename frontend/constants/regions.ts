// sharedパッケージから地域データをインポート
import { REGIONS_EXTENDED_KEYS, getAllLocationNames, getLocationsByRegion } from '@mobile-comment-generator/shared'

// Nuxt版との互換性のため、拡張キー名を使用
export const REGIONS = REGIONS_EXTENDED_KEYS

// SIMPLIFIED_REGIONSをエクスポート（REGIONS_EXTENDED_KEYSのエイリアス）
export const SIMPLIFIED_REGIONS = REGIONS_EXTENDED_KEYS

// 地域別の地点を取得（sharedから再エクスポート）
export { getLocationsByRegion }

// 地域の階層構造から地点データを抽出
export function extractAllLocations(): string[] {
  return getAllLocationNames()
}

// 全地点数をカウント
export const TOTAL_LOCATIONS = extractAllLocations().length
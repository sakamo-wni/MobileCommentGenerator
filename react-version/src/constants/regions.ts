// sharedパッケージから地域データをインポート
import { REGIONS as SHARED_REGIONS, getAllLocationNames, getLocationData } from '@mobile-comment-generator/shared'

// React版はシンプルなキー名を使用
export const REGIONS = SHARED_REGIONS

export type RegionName = keyof typeof REGIONS
export type SubRegionName<R extends RegionName> = keyof typeof REGIONS[R]
export type LocationName = string

// 全地点をフラットな配列として取得
export const getAllLocations = (): string[] => {
  return getAllLocationNames()
}

// 地点から地域情報を取得
export const getRegionInfo = (location: string): { region: string; subRegion: string } | null => {
  const locationData = getLocationData(location)
  if (!locationData || !locationData.area || !locationData.prefecture) {
    return null
  }
  return {
    region: locationData.area,
    subRegion: locationData.prefecture
  }
}
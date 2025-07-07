// constants/locations.ts - Re-export from shared package for backward compatibility

export { 
  REGIONS, 
  getAreaName, 
  getLocationsByRegion,
  getAllLocationNames 
} from '@mobile-comment-generator/shared/composables'

export default {
  REGIONS: [] as any, // Placeholder for backward compatibility
  getAreaName: () => '',
  getLocationsByRegion: () => []
}
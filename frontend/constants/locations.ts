// constants/locations.ts - Re-export from shared package for backward compatibility

export { 
  REGIONS, 
  getAreaName, 
  getLocationsByRegion,
  getAllLocationNames 
} from '@mobile-comment-generator/shared/composables'

// Default export for backward compatibility
import * as locationUtils from '@mobile-comment-generator/shared/composables'

export default {
  REGIONS: locationUtils.REGIONS,
  getAreaName: locationUtils.getAreaName,
  getLocationsByRegion: locationUtils.getLocationsByRegion,
  getAllLocationNames: locationUtils.getAllLocationNames
}
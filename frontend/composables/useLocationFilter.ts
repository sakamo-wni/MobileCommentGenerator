import { ref, computed } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import { REGIONS, getAreaName } from '@mobile-comment-generator/shared/composables'

export interface LocationFilterOptions {
  locations: Ref<Array<{ name: string; region?: string; area?: string }>>
}

export const useLocationFilter = (options: LocationFilterOptions) => {
  const { locations } = options
  const selectedRegion = ref<string>('')

  const regions = computed(() => REGIONS)

  const filteredLocations = computed(() => {
    if (!selectedRegion.value) {
      return locations.value
    }
    
    return locations.value.filter(location => {
      const region = location.region || location.area || getAreaName(location.name)
      return region === selectedRegion.value
    })
  })

  const getRegionLocations = (region: string) => {
    return locations.value.filter(location => {
      const locationRegion = location.region || location.area || getAreaName(location.name)
      return locationRegion === region
    })
  }

  const setSelectedRegion = (region: string) => {
    selectedRegion.value = region
  }

  return {
    selectedRegion,
    regions,
    filteredLocations,
    getRegionLocations,
    setSelectedRegion
  }
}
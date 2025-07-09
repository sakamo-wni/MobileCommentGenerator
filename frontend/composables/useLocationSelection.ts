import { ref, computed } from 'vue'
import type { Ref, ComputedRef } from 'vue'

export interface LocationSelectionOptions {
  locations: Ref<Array<{ name: string; region?: string; area?: string }>>
  onSelectionChange?: (locations: string[]) => void
}

export const useLocationSelection = (options: LocationSelectionOptions) => {
  const { locations, onSelectionChange } = options
  const selectedLocations = ref<string[]>([])

  const toggleLocation = (locationName: string) => {
    const index = selectedLocations.value.indexOf(locationName)
    if (index > -1) {
      selectedLocations.value.splice(index, 1)
    } else {
      selectedLocations.value.push(locationName)
    }
    
    if (onSelectionChange) {
      onSelectionChange(selectedLocations.value)
    }
  }

  const selectAllLocations = (locationList?: Array<{ name: string }>) => {
    const targetLocations = locationList || locations.value
    selectedLocations.value = targetLocations.map(loc => loc.name)
    
    if (onSelectionChange) {
      onSelectionChange(selectedLocations.value)
    }
  }

  const clearAllSelections = () => {
    selectedLocations.value = []
    
    if (onSelectionChange) {
      onSelectionChange(selectedLocations.value)
    }
  }

  const selectRegionLocations = (regionLocations: Array<{ name: string }>) => {
    const regionLocationNames = regionLocations.map(loc => loc.name)
    const nonRegionLocations = selectedLocations.value.filter(
      name => !regionLocationNames.includes(name)
    )
    
    selectedLocations.value = [...nonRegionLocations, ...regionLocationNames]
    
    if (onSelectionChange) {
      onSelectionChange(selectedLocations.value)
    }
  }

  const isLocationSelected = (locationName: string) => {
    return selectedLocations.value.includes(locationName)
  }

  return {
    selectedLocations,
    toggleLocation,
    selectAllLocations,
    clearAllSelections,
    selectRegionLocations,
    isLocationSelected
  }
}
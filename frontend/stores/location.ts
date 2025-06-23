import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { getLocationsByRegion } from '~/constants/regions'

export const useLocationStore = defineStore('location', () => {
  // State - 地点選択関連
  const selectedLocation = ref('')
  const selectedLocations = ref<string[]>([])
  const isBatchMode = ref(false)
  const locations = ref<string[]>([])
  const locationsLoading = ref(false)
  
  // Basic Actions
  const setSelectedLocation = (location: string) => {
    selectedLocation.value = location
  }
  
  const setSelectedLocations = (locations: string[]) => {
    selectedLocations.value = locations
  }
  
  const addSelectedLocation = (location: string) => {
    if (!selectedLocations.value.includes(location)) {
      selectedLocations.value.push(location)
    }
  }
  
  const removeSelectedLocation = (location: string) => {
    selectedLocations.value = selectedLocations.value.filter(loc => loc !== location)
  }
  
  const setBatchMode = (value: boolean) => {
    isBatchMode.value = value
    // モード切り替え時のクリア処理
    if (!value) {
      selectedLocations.value = []
    } else {
      selectedLocation.value = ''
    }
  }
  
  const toggleBatchMode = () => {
    setBatchMode(!isBatchMode.value)
  }
  
  const setLocations = (locationList: string[]) => {
    locations.value = locationList
  }
  
  const setLocationsLoading = (loading: boolean) => {
    locationsLoading.value = loading
  }
  
  const clearSelections = () => {
    selectedLocation.value = ''
    selectedLocations.value = []
  }
  
  // Regional selection actions
  const selectAllLocations = () => {
    selectedLocations.value = [...locations.value]
  }

  const clearAllLocations = () => {
    selectedLocations.value = []
  }

  const selectRegionLocations = (regionName: string) => {
    const regionLocations = getLocationsByRegion(regionName)
    
    // 既に全て選択済みかチェック
    const allSelected = regionLocations.every(loc => 
      selectedLocations.value.includes(loc)
    )
    
    if (allSelected) {
      // 全選択済みなら削除
      selectedLocations.value = selectedLocations.value.filter(loc => 
        !regionLocations.includes(loc)
      )
    } else {
      // 未選択があれば追加
      const newLocations = regionLocations.filter(loc => 
        !selectedLocations.value.includes(loc)
      )
      selectedLocations.value = [...selectedLocations.value, ...newLocations]
    }
  }

  // Getters
  const canGenerate = computed(() => {
    if (isBatchMode.value) {
      return selectedLocations.value.length > 0
    } else {
      return selectedLocation.value !== ''
    }
  })
  
  const selectedCount = computed(() => {
    return isBatchMode.value ? selectedLocations.value.length : 
           selectedLocation.value ? 1 : 0
  })
  
  const hasSelection = computed(() => {
    return canGenerate.value
  })
  
  // 地点選択オプション（select用）
  const locationOptions = computed(() => {
    return locations.value.map(location => ({
      label: location,
      value: location,
      id: location
    }))
  })
  
  const isRegionSelected = (regionName: string) => {
    const regionLocations = getLocationsByRegion(regionName)
    return regionLocations.length > 0 && 
           regionLocations.every(loc => selectedLocations.value.includes(loc))
  }
  
  return {
    // State (readonly)
    selectedLocation: readonly(selectedLocation),
    selectedLocations: readonly(selectedLocations),
    isBatchMode: readonly(isBatchMode),
    locations: readonly(locations),
    locationsLoading: readonly(locationsLoading),
    
    // Actions
    setSelectedLocation,
    setSelectedLocations,
    addSelectedLocation,
    removeSelectedLocation,
    setBatchMode,
    toggleBatchMode,
    setLocations,
    setLocationsLoading,
    clearSelections,
    selectAllLocations,
    clearAllLocations,
    selectRegionLocations,
    
    // Getters
    canGenerate,
    selectedCount,
    hasSelection,
    locationOptions,
    isRegionSelected
  }
})
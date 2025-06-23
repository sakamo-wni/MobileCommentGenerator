import { defineStore } from 'pinia'

export const useLocationStore = defineStore('location', () => {
  // State
  const selectedLocation = ref('')
  const selectedLocations = ref<string[]>([])
  const isBatchMode = ref(false)
  const locations = ref<string[]>([
    '東京',
    '大阪',
    '名古屋',
    '札幌',
    '福岡',
    '仙台',
    '広島',
    '神戸',
    '京都',
    '横浜'
  ])
  
  // Computed
  const canGenerate = computed(() => {
    if (isBatchMode.value) {
      return selectedLocations.value.length > 0
    }
    return selectedLocation.value !== ''
  })
  
  // Actions
  const toggleBatchMode = () => {
    isBatchMode.value = !isBatchMode.value
    // モード切り替え時に選択をクリア
    if (isBatchMode.value) {
      selectedLocation.value = ''
    } else {
      selectedLocations.value = []
    }
  }
  
  const selectLocation = (location: string) => {
    if (isBatchMode.value) {
      const index = selectedLocations.value.indexOf(location)
      if (index > -1) {
        selectedLocations.value.splice(index, 1)
      } else {
        selectedLocations.value.push(location)
      }
    } else {
      selectedLocation.value = location
    }
  }
  
  const clearSelection = () => {
    selectedLocation.value = ''
    selectedLocations.value = []
  }
  
  const selectAllLocations = () => {
    if (isBatchMode.value) {
      selectedLocations.value = [...locations.value]
    }
  }
  
  const deselectAllLocations = () => {
    if (isBatchMode.value) {
      selectedLocations.value = []
    }
  }
  
  return {
    // State
    selectedLocation,
    selectedLocations,
    isBatchMode,
    locations: readonly(locations),
    
    // Computed
    canGenerate,
    
    // Actions
    toggleBatchMode,
    selectLocation,
    clearSelection,
    selectAllLocations,
    deselectAllLocations
  }
})
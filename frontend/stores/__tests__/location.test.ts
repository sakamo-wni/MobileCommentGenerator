// 基本的な動作確認のみ
import { setActivePinia, createPinia } from 'pinia'
import { useLocationStore } from '../location'

describe('Location Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should initialize with empty state', () => {
    const store = useLocationStore()
    expect(store.selectedLocation).toBe('')
    expect(store.selectedLocations).toEqual([])
    expect(store.isBatchMode).toBe(false)
    expect(store.locations).toEqual([])
    expect(store.locationsLoading).toBe(false)
  })

  it('should toggle batch mode', () => {
    const store = useLocationStore()
    expect(store.isBatchMode).toBe(false)
    
    store.toggleBatchMode()
    expect(store.isBatchMode).toBe(true)
  })

  it('should clear selections when switching modes', () => {
    const store = useLocationStore()
    store.setSelectedLocation('東京')
    store.setBatchMode(true)
    expect(store.selectedLocation).toBe('')
    
    store.setSelectedLocations(['東京', '大阪'])
    store.setBatchMode(false)
    expect(store.selectedLocations).toEqual([])
  })

  it('should calculate canGenerate correctly', () => {
    const store = useLocationStore()
    expect(store.canGenerate).toBe(false)
    
    store.setSelectedLocation('東京')
    expect(store.canGenerate).toBe(true)
    
    store.setBatchMode(true)
    expect(store.canGenerate).toBe(false)
    
    store.setSelectedLocations(['東京', '大阪'])
    expect(store.canGenerate).toBe(true)
  })

  it('should manage selected locations correctly', () => {
    const store = useLocationStore()
    
    store.addSelectedLocation('東京')
    expect(store.selectedLocations).toEqual(['東京'])
    
    store.addSelectedLocation('大阪')
    expect(store.selectedLocations).toEqual(['東京', '大阪'])
    
    // Should not add duplicates
    store.addSelectedLocation('東京')
    expect(store.selectedLocations).toEqual(['東京', '大阪'])
    
    store.removeSelectedLocation('東京')
    expect(store.selectedLocations).toEqual(['大阪'])
  })

  it('should calculate selectedCount correctly', () => {
    const store = useLocationStore()
    expect(store.selectedCount).toBe(0)
    
    store.setSelectedLocation('東京')
    expect(store.selectedCount).toBe(1)
    
    store.setBatchMode(true)
    expect(store.selectedCount).toBe(0)
    
    store.setSelectedLocations(['東京', '大阪', '名古屋'])
    expect(store.selectedCount).toBe(3)
  })

  it('should clear all selections', () => {
    const store = useLocationStore()
    store.setSelectedLocation('東京')
    store.setSelectedLocations(['大阪', '名古屋'])
    
    store.clearSelections()
    expect(store.selectedLocation).toBe('')
    expect(store.selectedLocations).toEqual([])
  })

  it('should generate location options correctly', () => {
    const store = useLocationStore()
    store.setLocations(['東京', '大阪', '名古屋'])
    
    const options = store.locationOptions
    expect(options).toHaveLength(3)
    expect(options[0]).toEqual({
      label: '東京',
      value: '東京',
      id: '東京'
    })
  })
})
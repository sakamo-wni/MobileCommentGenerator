// 基本的な動作確認のみ
import { setActivePinia, createPinia } from 'pinia'
import { useCommentStore } from '../comment'

describe('Comment Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should initialize with empty state', () => {
    const store = useCommentStore()
    expect(store.generating).toBe(false)
    expect(store.result).toBeNull()
    expect(store.results).toEqual([])
  })

  it('should update generating state', () => {
    const store = useCommentStore()
    store.setGenerating(true)
    expect(store.generating).toBe(true)
  })

  it('should clear results', () => {
    const store = useCommentStore()
    store.setResult({ success: true, location: 'test' })
    store.clearResults()
    expect(store.result).toBeNull()
  })

  it('should add results', () => {
    const store = useCommentStore()
    const testResult = { success: true, location: 'test location' }
    store.addResult(testResult)
    expect(store.results).toHaveLength(1)
    expect(store.results[0]).toEqual(testResult)
  })

  it('should compute hasResults correctly', () => {
    const store = useCommentStore()
    expect(store.hasResults).toBe(false)
    
    store.setResult({ success: true, location: 'test' })
    expect(store.hasResults).toBe(true)
  })

  it('should compute successCount correctly', () => {
    const store = useCommentStore()
    store.addResult({ success: true, location: 'location1' })
    store.addResult({ success: false, location: 'location2' })
    store.addResult({ success: true, location: 'location3' })
    
    expect(store.successCount).toBe(2)
    expect(store.totalCount).toBe(3)
  })
})
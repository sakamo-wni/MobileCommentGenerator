import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import type { GenerationResult, BatchResult } from '~/types/store'

export const useCommentStore = defineStore('comment', () => {
  // State - 生成関連の基本状態のみ
  const generating = ref(false)
  const result = ref<GenerationResult | null>(null)
  const results = ref<BatchResult[]>([])
  
  // Basic Actions - シンプルなセッター/ゲッターのみ
  const setGenerating = (value: boolean) => {
    generating.value = value
  }
  
  const setResult = (value: GenerationResult | null) => {
    result.value = value
  }
  
  const setResults = (value: BatchResult[]) => {
    results.value = value
  }
  
  const addResult = (value: BatchResult) => {
    results.value.push(value)
  }
  
  const addResults = (values: BatchResult[]) => {
    results.value.push(...values)
  }
  
  const updateResultAtIndex = (index: number, value: BatchResult) => {
    if (index >= 0 && index < results.value.length) {
      results.value[index] = value
    }
  }
  
  const clearResults = () => {
    result.value = null
    results.value = []
  }
  
  // Basic Getters
  const hasResults = computed(() => {
    return result.value !== null || results.value.length > 0
  })
  
  const hasSuccessResults = computed(() => {
    if (result.value) {
      return result.value.success
    }
    return results.value.some(r => r.success)
  })
  
  const successCount = computed(() => {
    return results.value.filter(r => r.success).length
  })
  
  const totalCount = computed(() => {
    return results.value.length
  })
  
  return {
    // State (readonly for external use)
    generating: readonly(generating),
    result: readonly(result),
    results: readonly(results),
    
    // Actions
    setGenerating,
    setResult,
    setResults,
    addResult,
    addResults,
    updateResultAtIndex,
    clearResults,
    
    // Getters
    hasResults,
    hasSuccessResults,
    successCount,
    totalCount
  }
})
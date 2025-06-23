import { defineStore } from 'pinia'
import { watch } from 'vue'
import type { CommentGenerationResult } from '~/types'

interface HistoryItem {
  timestamp: string
  location: string
  provider: string
  success: boolean
  comment?: string
}

interface GenerateParams {
  location: string
  locations?: string[]
  provider: string
  isBatchMode: boolean
}

export const useCommentStore = defineStore('comment', () => {
  // State
  const generating = ref(false)
  const result = ref<CommentGenerationResult | null>(null)
  const results = ref<CommentGenerationResult[]>([])
  const history = ref<HistoryItem[]>([])
  
  // Actions
  const generateComment = async (params: GenerateParams) => {
    generating.value = true
    try {
      
      if (params.isBatchMode && params.locations) {
        // バッチモード
        const allResults = await Promise.all(
          params.locations.map(async (location) => {
            try {
              const response = await $fetch<CommentGenerationResult>('/api/generate-comment', {
                method: 'POST',
                body: {
                  location,
                  provider: params.provider
                }
              })
              
              // 履歴に追加
              addToHistory({
                timestamp: new Date().toLocaleString('ja-JP'),
                location,
                provider: params.provider,
                success: response.success,
                comment: response.comment || undefined
              })
              
              return response
            } catch (error) {
              console.error(`Error generating comment for ${location}:`, error)
              return {
                success: false,
                location,
                comment: null,
                advice_comment: null,
                error: 'リクエストに失敗しました',
                metadata: null
              }
            }
          })
        )
        
        results.value = allResults
        result.value = null
      } else {
        // 単一モード
        const response = await $fetch<CommentGenerationResult>('/api/generate-comment', {
          method: 'POST',
          body: {
            location: params.location,
            provider: params.provider
          }
        })
        
        result.value = response
        results.value = []
        
        // 履歴に追加
        addToHistory({
          timestamp: new Date().toLocaleString('ja-JP'),
          location: params.location,
          provider: params.provider,
          success: response.success,
          comment: response.comment || undefined
        })
      }
    } catch (error) {
      console.error('Error generating comment:', error)
      if (!params.isBatchMode) {
        result.value = {
          success: false,
          location: params.location,
          comment: null,
          advice_comment: null,
          error: 'リクエストに失敗しました',
          metadata: null
        }
      }
    } finally {
      generating.value = false
    }
  }
  
  const clearResults = () => {
    result.value = null
    results.value = []
  }
  
  const addToHistory = (item: HistoryItem) => {
    history.value.unshift(item)
    // 最大50件まで保持
    if (history.value.length > 50) {
      history.value = history.value.slice(0, 50)
    }
  }
  
  // $persist を使用して永続化設定
  // @ts-ignore
  if (process.client) {
    const savedHistory = localStorage.getItem('comment-history')
    if (savedHistory) {
      history.value = JSON.parse(savedHistory)
    }
    
    watch(history, (newHistory) => {
      localStorage.setItem('comment-history', JSON.stringify(newHistory))
    }, { deep: true })
  }
  
  const clearHistory = () => {
    history.value = []
  }
  
  return {
    // State
    generating,
    result,
    results,
    history,
    
    // Actions
    generateComment,
    clearResults,
    clearHistory
  }
})
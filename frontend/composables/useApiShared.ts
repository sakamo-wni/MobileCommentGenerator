// useApiShared.ts - API composable using shared client
import { createApiClient } from '@mobile-comment-generator/shared'
import type { 
  Location as SharedLocation,
  GenerateSettings as SharedGenerateSettings,
  GeneratedComment as SharedGeneratedComment,
  WeatherData as SharedWeatherData
} from '@mobile-comment-generator/shared'
import { useErrorHandler } from '~/composables/useErrorHandler'

// 型のマッピング
export const useApiShared = () => {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBaseUrl || 'http://localhost:8000'
  const { handleError } = useErrorHandler()
  
  // 共通APIクライアントのインスタンスを作成
  const apiClient = createApiClient(baseURL)

  // Health check
  const checkHealth = async (): Promise<boolean> => {
    try {
      const response = await $fetch(`${baseURL}/health`)
      return response.status === 'ok'
    } catch (error) {
      handleError(error, 'ヘルスチェックに失敗しました')
      return false
    }
  }

  // Fetch locations
  const fetchLocations = async (): Promise<{ success: boolean; data?: SharedLocation[]; error?: string }> => {
    try {
      const locations = await apiClient.getLocations()
      return { success: true, data: locations }
    } catch (error: any) {
      const errorDetails = handleError(error, '地点データの取得に失敗しました')
      return { 
        success: false, 
        error: errorDetails.message
      }
    }
  }

  // Generate comments
  const generateComments = async (
    location: SharedLocation,
    settings: Partial<SharedGenerateSettings>
  ): Promise<{ success: boolean; data?: SharedGeneratedComment[]; error?: string }> => {
    try {
      const generateSettings: SharedGenerateSettings = {
        location,
        llmProvider: settings.llmProvider || 'gemini',
        targetDateTime: settings.targetDateTime || new Date().toISOString(),
        excludePrevious: settings.excludePrevious || false,
        temperature: settings.temperature
      }
      
      const comment = await apiClient.generateComment(generateSettings)
      return { success: true, data: [comment] }
    } catch (error: any) {
      const errorDetails = handleError(error, 'コメント生成に失敗しました')
      return { 
        success: false, 
        error: errorDetails.message
      }
    }
  }

  // Get weather data
  const fetchWeatherData = async (
    locationId: string
  ): Promise<{ success: boolean; data?: SharedWeatherData; error?: string }> => {
    try {
      const data = await apiClient.getWeatherData(locationId)
      return { success: true, data }
    } catch (error: any) {
      const errorDetails = handleError(error, '天気データの取得に失敗しました')
      return { 
        success: false, 
        error: errorDetails.message
      }
    }
  }

  // Get history
  const fetchHistory = async (limit: number = 10): Promise<{ success: boolean; data?: SharedGeneratedComment[]; error?: string }> => {
    try {
      const history = await apiClient.getHistory(limit)
      return { success: true, data: history }
    } catch (error: any) {
      const errorDetails = handleError(error, '履歴の取得に失敗しました')
      return { 
        success: false, 
        error: errorDetails.message
      }
    }
  }

  return {
    checkHealth,
    fetchLocations,
    generateComments,
    fetchWeatherData,
    fetchHistory
  }
}
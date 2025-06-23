// useApi.ts - API composable for frontend
import type { 
  Location, 
  Coordinates, 
  GenerateSettings, 
  GeneratedComment,
  WeatherData,
  ApiResponse
} from '~/types'

export const useApi = () => {
  const config = useRuntimeConfig()
  const baseURL = 'http://localhost:8000' // Direct API URL

  // Health check
  const checkHealth = async (): Promise<boolean> => {
    try {
      const response = await $fetch(`${baseURL}/health`)
      return response.status === 'ok'
    } catch {
      return false
    }
  }

  // Fetch locations
  const fetchLocations = async (): Promise<ApiResponse<Location[]>> => {
    try {
      const data = await $fetch<Location[]>(`${baseURL}/api/locations`)
      return { success: true, data }
    } catch (error) {
      return { 
        success: false, 
        error: '地点データの取得に失敗しました' 
      }
    }
  }

  // Fetch weather data
  const fetchWeatherData = async (
    coords: Coordinates, 
    targetTime: string
  ): Promise<ApiResponse<WeatherData>> => {
    try {
      const data = await $fetch<WeatherData>(`${baseURL}/api/weather`, {
        method: 'POST',
        body: {
          latitude: coords.latitude,
          longitude: coords.longitude,
          target_time: targetTime
        }
      })
      return { success: true, data }
    } catch (error) {
      return { 
        success: false, 
        error: '天気データの取得に失敗しました' 
      }
    }
  }

  // Generate comments
  const generateComments = async (
    locations: string[],
    settings: GenerateSettings,
    weatherData?: WeatherData
  ): Promise<ApiResponse<GeneratedComment[]>> => {
    try {
      const data = await $fetch<GeneratedComment[]>(`${baseURL}/api/generate`, {
        method: 'POST',
        body: {
          location: locations[0], // Backend expects single location string
          llm_provider: 'gemini',
          target_datetime: new Date().toISOString(),
          exclude_previous: false
        }
      })
      return { success: true, data }
    } catch (error) {
      return { 
        success: false, 
        error: 'コメント生成に失敗しました' 
      }
    }
  }

  // Check workflow integration
  const checkWorkflowIntegration = async (): Promise<ApiResponse<any>> => {
    try {
      const data = await $fetch(`${baseURL}/api/workflow/status`)
      return { success: true, data }
    } catch (error) {
      return { 
        success: false, 
        error: 'ワークフローの状態確認に失敗しました' 
      }
    }
  }

  return {
    checkHealth,
    fetchLocations,
    fetchWeatherData,
    generateComments,
    checkWorkflowIntegration
  }
}
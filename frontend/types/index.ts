// types/index.ts - TypeScript type definitions

export interface Location {
  name: string
  latitude: number
  longitude: number
  area?: string
}

export interface Coordinates {
  latitude: number
  longitude: number
}

export interface GenerateSettings {
  method: string
  count: number
  includeEmoji: boolean
  includeAdvice: boolean
  politeForm: boolean
  targetTime: string
}

export interface GeneratedComment {
  id: string
  location: string
  comment: string
  timestamp: string
  score?: number
}

export interface WeatherForecast {
  time: string
  label: string
  weather: string
  temperature: number
  precipitation: number
}

export interface WeatherTimeline {
  future_forecasts: WeatherForecast[]
  past_forecasts: WeatherForecast[]
  base_time: string
  summary: {
    temperature_range: string
    max_precipitation: string
    weather_pattern: string
  }
}

export interface WeatherMetadata {
  weather_forecast_time: string
  temperature: number
  weather_condition: string
  wind_speed: number
  humidity: number
  weather_timeline: WeatherTimeline
  llm_provider: string
}

export interface CommentGenerationResult {
  success: boolean
  location: string
  comment: string | null
  advice_comment: string | null
  error: string | null
  metadata: WeatherMetadata | null
}

export interface WeatherData {
  temperature: number
  condition: string
  humidity: number
  windSpeed: number
  timestamp: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

// Workflow related types
export interface WorkflowStatus {
  available: boolean
  version: string
  lastUpdate: string
}
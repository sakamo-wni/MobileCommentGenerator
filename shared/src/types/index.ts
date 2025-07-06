// 既存のNuxt.js版と共通の型定義
export interface Location {
  id: string;
  name: string;
  prefecture: string;
  region: string;
  latitude?: number;
  longitude?: number;
}

export interface GenerateSettings {
  location: Location;
  llmProvider: 'openai' | 'gemini' | 'anthropic';
  temperature?: number;
  targetDateTime?: string;
  excludePrevious?: boolean;
}

export interface GeneratedComment {
  id: string;
  comment: string;
  adviceComment?: string;
  weather: WeatherData;
  metadata?: WeatherMetadata;
  timestamp: string;
  confidence: number;
  location: Location;
  settings: GenerateSettings;
}

export interface WeatherData {
  current: CurrentWeather;
  forecast: ForecastWeather[];
  trend?: WeatherTrend;
}

export interface CurrentWeather {
  temperature: number;
  humidity: number;
  pressure: number;
  windSpeed: number;
  windDirection: string;
  description: string;
  icon: string;
}

export interface ForecastWeather {
  datetime: string;
  temperature: {
    min: number;
    max: number;
  };
  humidity: number;
  precipitation: number;
  description: string;
  icon: string;
}

export interface WeatherTrend {
  trend: 'improving' | 'worsening' | 'stable';
  confidence: number;
  description: string;
}

// 天気予報のメタデータ型定義（React UIで使用）
export interface WeatherMetadata {
  temperature?: number;
  weather_condition?: string;
  wind_speed?: number;
  humidity?: number;
  weather_forecast_time?: string;
  weather_timeline?: WeatherTimeline;
  selected_weather_comment?: string;
  selected_advice_comment?: string;
}

export interface WeatherTimeline {
  summary?: {
    weather_pattern: string;
    temperature_range: string;
    max_precipitation: string;
  };
  past_forecasts?: TimelineForecast[];
  future_forecasts?: TimelineForecast[];
  error?: string;
}

export interface TimelineForecast {
  label: string;
  time: string;
  weather: string;
  temperature: number;
  precipitation: number;
}

// バッチ処理関連の型定義を再エクスポート
export type { BatchResult, GenerationResult } from './batch';

// UI定数
export const COPY_FEEDBACK_DURATION = 2000; // コピー済み表示の持続時間（ミリ秒）
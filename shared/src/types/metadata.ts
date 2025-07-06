/**
 * 気象データのメタデータ型定義
 */

export interface WeatherMetadata {
  weather_condition: string;
  temperature: number;
  humidity?: number;
  wind_speed?: number;
  generated_at: string;
  period_forecasts?: PeriodForecast[];
  weather_timeline?: WeatherTimeline;
  selection_metadata?: SelectionMetadata;
}

export interface PeriodForecast {
  datetime: string;
  temperature: number;
  precipitation: number;
  weather_description: string;
}

export interface WeatherTimeline {
  today_weather: string;
  tomorrow_weather: string;
  weather_trend: string;
  future_forecasts: FutureForecast[];
}

export interface FutureForecast {
  datetime: string;
  precipitation: number;
  temperature: number;
  weather: string;
}

export interface SelectionMetadata {
  selected_comment?: string;
  selected_advice_comment?: string;
  comment_metadata?: CommentMetadata;
}

export interface CommentMetadata {
  weather_type: string;
  season: string;
  priority: string;
}
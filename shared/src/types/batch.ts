import type { WeatherMetadata } from './metadata';

export interface BatchResult {
  success: boolean;
  location: string;
  comment?: string | null;
  error?: string | null;
  metadata?: WeatherMetadata | null;
  weather?: WeatherMetadata | null;
  adviceComment?: string | null;
  advice_comment?: string | null; // For API compatibility
  loading?: boolean;
}

export interface GenerationResult {
  success: boolean;
  location: string;
  comment?: string | null;
  error?: string | null;
  metadata?: WeatherMetadata | null;
  weather?: WeatherMetadata | null;
  adviceComment?: string | null;
  advice_comment?: string | null; // For API compatibility
}
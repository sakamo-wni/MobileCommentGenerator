import axios, { AxiosInstance } from 'axios';
import type { Location, GenerateSettings, GeneratedComment, WeatherData } from '../types';

export class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL?: string) {
    // APIサーバーは8000番ポートで起動
    const apiUrl = baseURL || 
      (typeof process !== 'undefined' && process.env?.NUXT_PUBLIC_API_URL) || 
      (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || 
      'http://localhost:8000';
    
    this.client = axios.create({
      baseURL: apiUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('[API Error]', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  async getLocations(): Promise<Location[]> {
    const response = await this.client.get('/api/locations');
    // APIは {locations: string[]} の形式で返すので、Location[]に変換
    const locationNames = response.data.locations || response.data;
    return Array.isArray(locationNames) 
      ? locationNames.map((name: string, index: number) => ({
          id: `loc-${index}`,
          name,
          prefecture: name, // 簡易的にnameをprefectureとして使用
          region: name // 簡易的にnameをregionとして使用
        }))
      : [];
  }

  async generateComment(settings: GenerateSettings): Promise<GeneratedComment> {
    // APIサーバーの期待する形式に変換
    const apiRequest = {
      location: settings.location.name,
      llm_provider: settings.llmProvider,
      target_datetime: settings.targetDateTime,
      exclude_previous: settings.excludePrevious || false,
    };
    
    const response = await this.client.post('/api/generate', apiRequest);
    
    // APIレスポンスをGeneratedComment形式に変換
    const apiResponse = response.data;
    return {
      id: `comment-${Date.now()}`,
      comment: apiResponse.comment || '',
      adviceComment: apiResponse.advice_comment || apiResponse.metadata?.selected_advice_comment,
      weather: {
        current: {
          temperature: apiResponse.metadata?.temperature || 0,
          humidity: apiResponse.metadata?.humidity || 0,
          pressure: 0,
          windSpeed: apiResponse.metadata?.wind_speed || 0,
          windDirection: '',
          description: apiResponse.metadata?.weather_condition || '',
          icon: '',
        },
        forecast: [],
      },
      timestamp: new Date().toISOString(),
      confidence: apiResponse.success ? 0.9 : 0.1,
      location: settings.location,
      settings,
    };
  }

  async getHistory(limit: number = 10): Promise<GeneratedComment[]> {
    const response = await this.client.get('/api/history', {
      params: { limit },
    });
    return response.data;
  }

  async getWeatherData(locationId: string): Promise<WeatherData> {
    const response = await this.client.get(`/api/weather/${locationId}`);
    return response.data;
  }
}

export const createApiClient = (baseURL?: string) => new ApiClient(baseURL);
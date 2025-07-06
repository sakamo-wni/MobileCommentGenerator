import React from 'react';
import { Cloud, Thermometer, Droplets, Wind, Gauge, TrendingUp, Clock, CloudRain, Info } from 'lucide-react';
import type { WeatherData, WeatherMetadata } from '@mobile-comment-generator/shared';
import { WeatherTimeline } from './WeatherTimeline';

interface WeatherDataProps {
  weather: WeatherData | null;
  metadata?: WeatherMetadata;
  className?: string;
}

const formatDateTime = (dateString: string | undefined) => {
  if (!dateString) return '不明';
  try {
    const date = new Date(dateString.replace('Z', '+00:00'));
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return dateString;
  }
};

export const WeatherDataDisplay: React.FC<WeatherDataProps> = ({
  weather,
  metadata,
  className = '',
}) => {
  if (!weather) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <Cloud className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400">天気データを取得中...</p>
      </div>
    );
  }

  const { current, forecast, trend } = weather;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 予報基準時刻 */}
      {metadata?.weather_forecast_time && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-semibold text-blue-800 dark:text-blue-200">予報基準時刻</span>
          </div>
          <div className="text-blue-700 dark:text-blue-300 font-medium">
            {formatDateTime(metadata.weather_forecast_time)}
          </div>
          <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
            翌日の9時、12時、15時、18時の天気変化を分析してコメントを生成
          </div>
        </div>
      )}

      {/* Weather Timeline - 4時間予報データ */}
      {metadata?.weather_timeline && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 shadow-sm">
          <WeatherTimeline timeline={metadata.weather_timeline} />
        </div>
      )}

      {/* 翌日の天気予報 */}
      <div className="bg-app-surface border border-app-border rounded-lg p-6 shadow-sm">
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <Cloud className="w-5 h-5 mr-2 text-blue-600" />
            翌日の天気予報
          </h3>
          {metadata?.weather_forecast_time && (
            <div className="text-sm text-gray-600 dark:text-gray-400">
              予報時刻: {formatDateTime(metadata.weather_forecast_time)}
            </div>
          )}
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Thermometer className="w-5 h-5 text-red-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{current.temperature}°C</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">気温</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Droplets className="w-5 h-5 text-blue-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{current.humidity}%</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">湿度</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Wind className="w-5 h-5 text-green-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{current.windSpeed}m/s</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">風速</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Gauge className="w-5 h-5 text-purple-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{current.pressure}hPa</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">気圧</div>
          </div>
        </div>

        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">{current.icon}</span>
            <div>
              <div className="font-medium text-gray-900 dark:text-gray-100">{current.description}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">風向: {current.windDirection}</div>
            </div>
          </div>
        </div>
      </div>

      {/* 予報データ */}
      {forecast && forecast.length > 0 && (
        <div className="bg-app-surface border border-app-border rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">基本天気予報</h3>
          
          <div className="space-y-3">
            {forecast.slice(0, 5).map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <span className="text-xl">{item.icon}</span>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {new Date(item.datetime).toLocaleDateString('ja-JP', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">{item.description}</div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="font-bold text-gray-900 dark:text-gray-100">
                    {item.temperature.max}°C / {item.temperature.min}°C
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    湿度: {item.humidity}% | 降水: {item.precipitation}mm
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* トレンド情報 */}
      {trend && (
        <div className="bg-app-surface border border-app-border rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-green-600" />
            天気の傾向
          </h3>
          
          <div className="flex items-center space-x-4">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              trend.trend === 'improving' ? 'bg-green-100 text-green-800' :
              trend.trend === 'worsening' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {trend.trend === 'improving' ? '改善傾向' :
               trend.trend === 'worsening' ? '悪化傾向' : '安定'}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              信頼度: {Math.round(trend.confidence * 100)}%
            </div>
          </div>

          <p className="mt-3 text-gray-700 dark:text-gray-300">{trend.description}</p>
        </div>
      )}

      {/* Selected Comments */}
      {(metadata?.selected_weather_comment || metadata?.selected_advice_comment) && (
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-700 rounded-lg p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Info className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h3 className="text-lg font-semibold text-purple-800 dark:text-purple-200">選択されたコメント</h3>
          </div>
          {metadata.selected_weather_comment && (
            <div className="mb-3">
              <div className="text-sm font-medium text-purple-700 dark:text-purple-300 mb-1">
                <strong>天気コメント:</strong>
              </div>
              <div className="text-purple-800 dark:text-purple-200">
                {metadata.selected_weather_comment}
              </div>
            </div>
          )}
          {metadata.selected_advice_comment && (
            <div>
              <div className="text-sm font-medium text-purple-700 dark:text-purple-300 mb-1">
                <strong>アドバイスコメント:</strong>
              </div>
              <div className="text-purple-800 dark:text-purple-200">
                {metadata.selected_advice_comment}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
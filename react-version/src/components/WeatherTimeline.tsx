import React from 'react';
import { Clock, CloudRain, Thermometer, Zap } from 'lucide-react';

interface WeatherTimelineProps {
  timeline?: {
    summary?: {
      weather_pattern: string;
      temperature_range: string;
      max_precipitation: string;
    };
    past_forecasts?: Array<{
      label: string;
      time: string;
      weather: string;
      temperature: number;
      precipitation: number;
    }>;
    future_forecasts?: Array<{
      label: string;
      time: string;
      weather: string;
      temperature: number;
      precipitation: number;
    }>;
    error?: string;
  };
  className?: string;
}

export const WeatherTimeline: React.FC<WeatherTimelineProps> = ({
  timeline,
  className = '',
}) => {
  if (!timeline) {
    return null;
  }

  if (timeline.error) {
    return (
      <div className={`p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg ${className}`}>
        <div className="text-sm text-red-600 dark:text-red-400">
          時系列データ取得エラー: {timeline.error}
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center space-x-2 mb-3">
        <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        <h4 className="text-lg font-semibold text-gray-900 dark:text-white">時系列予報データ</h4>
      </div>

      {/* Summary */}
      {timeline.summary && (
        <div className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 border border-blue-200 dark:border-blue-700 rounded-lg">
          <div className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-2">
            📊 予報概要
          </div>
          <div className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
            <div className="flex items-center space-x-2">
              <span className="font-medium">天気パターン:</span>
              <span>{timeline.summary.weather_pattern}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Thermometer className="w-4 h-4" />
              <span className="font-medium">気温範囲:</span>
              <span>{timeline.summary.temperature_range}</span>
            </div>
            <div className="flex items-center space-x-2">
              <CloudRain className="w-4 h-4" />
              <span className="font-medium">最大降水量:</span>
              <span>{timeline.summary.max_precipitation}</span>
            </div>
          </div>
        </div>
      )}

      {/* Past Forecasts */}
      {timeline.past_forecasts && timeline.past_forecasts.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-semibold text-orange-700 dark:text-orange-300 mb-3">
            📈 過去の推移（12時間前〜基準時刻）
          </div>
          <div className="space-y-1">
            {timeline.past_forecasts.map((forecast, index) => (
              <div
                key={index}
                className="flex items-center justify-between py-2 px-3 bg-gradient-to-r from-orange-50 to-yellow-50 dark:from-orange-900/20 dark:to-yellow-900/20 border border-orange-200 dark:border-orange-700 rounded-lg text-sm hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center space-x-3 min-w-0 flex-1">
                  <span className="font-mono text-xs bg-orange-100 dark:bg-orange-800 px-2 py-1 rounded whitespace-nowrap">
                    {forecast.label}
                  </span>
                  <span className="text-gray-600 dark:text-gray-400 text-xs whitespace-nowrap">
                    {forecast.time}
                  </span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {forecast.weather}
                  </span>
                  <div className="flex items-center space-x-1">
                    <Thermometer className="w-4 h-4 text-red-500" />
                    <span className="font-medium">{forecast.temperature}°C</span>
                  </div>
                  {forecast.precipitation > 0 && (
                    <div className="flex items-center space-x-1">
                      <CloudRain className="w-4 h-4 text-blue-500" />
                      <span className="text-blue-600 dark:text-blue-400 font-medium">
                        {forecast.precipitation}mm
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Future Forecasts */}
      {timeline.future_forecasts && timeline.future_forecasts.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm font-semibold text-green-700 dark:text-green-300 mb-3">
            🔮 今後の予報（3〜12時間後）
          </div>
          <div className="space-y-1">
            {timeline.future_forecasts.map((forecast, index) => (
              <div
                key={index}
                className="flex items-center justify-between py-2 px-3 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-700 rounded-lg text-sm hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center space-x-3 min-w-0 flex-1">
                  <span className="font-mono text-xs bg-green-100 dark:bg-green-800 px-2 py-1 rounded whitespace-nowrap">
                    {forecast.label}
                  </span>
                  <span className="text-gray-600 dark:text-gray-400 text-xs whitespace-nowrap">
                    {forecast.time}
                  </span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {forecast.weather}
                  </span>
                  <div className="flex items-center space-x-1">
                    <Thermometer className="w-4 h-4 text-red-500" />
                    <span className="font-medium">{forecast.temperature}°C</span>
                  </div>
                  {forecast.precipitation > 0 && (
                    <div className="flex items-center space-x-1">
                      <CloudRain className="w-4 h-4 text-blue-500" />
                      <span className="text-blue-600 dark:text-blue-400 font-medium">
                        {forecast.precipitation}mm
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {!timeline.past_forecasts?.length && !timeline.future_forecasts?.length && !timeline.summary && (
        <div className="text-center py-4 text-gray-500 dark:text-gray-400">
          時系列データがありません
        </div>
      )}
    </div>
  );
};
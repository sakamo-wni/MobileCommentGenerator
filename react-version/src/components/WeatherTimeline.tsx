import React from 'react';
import { 
  Cloud, 
  CloudRain, 
  Sun, 
  CloudSnow, 
  Wind,
  Droplets,
  Thermometer,
  AlertCircle,
  TrendingUp,
  ArrowRight,
  Clock
} from 'lucide-react';
import type { WeatherTimeline as WeatherTimelineType, TimelineForecast } from '@mobile-comment-generator/shared';

interface WeatherTimelineProps {
  timeline: WeatherTimelineType;
}

interface ForecastListProps {
  forecasts: TimelineForecast[];
  gradientColor: string;
}

const getWeatherIcon = (weather: string) => {
  const weatherLower = weather.toLowerCase();
  if (weatherLower.includes('雨') || weatherLower.includes('rain')) {
    return <CloudRain className="w-4 h-4" aria-label={`雨の天気: ${weather}`} />;
  }
  if (weatherLower.includes('雪') || weatherLower.includes('snow')) {
    return <CloudSnow className="w-4 h-4" aria-label={`雪の天気: ${weather}`} />;
  }
  if (weatherLower.includes('曇') || weatherLower.includes('cloud')) {
    return <Cloud className="w-4 h-4" aria-label={`曇りの天気: ${weather}`} />;
  }
  if (weatherLower.includes('晴') || weatherLower.includes('sun')) {
    return <Sun className="w-4 h-4" aria-label={`晴れの天気: ${weather}`} />;
  }
  return <Cloud className="w-4 h-4" aria-label={`天気: ${weather}`} />;
};

const getWeatherColors = (weather: string) => {
  const weatherLower = weather.toLowerCase();
  if (weatherLower.includes('雨') || weatherLower.includes('rain')) {
    return {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-700',
      text: 'text-blue-600 dark:text-blue-400',
      icon: 'text-blue-500'
    };
  }
  if (weatherLower.includes('雪') || weatherLower.includes('snow')) {
    return {
      bg: 'bg-gray-50 dark:bg-gray-900/20',
      border: 'border-gray-200 dark:border-gray-700',
      text: 'text-gray-600 dark:text-gray-400',
      icon: 'text-gray-500'
    };
  }
  if (weatherLower.includes('曇') || weatherLower.includes('cloud')) {
    return {
      bg: 'bg-slate-50 dark:bg-slate-900/20',
      border: 'border-slate-200 dark:border-slate-700',
      text: 'text-slate-600 dark:text-slate-400',
      icon: 'text-slate-500'
    };
  }
  if (weatherLower.includes('晴') || weatherLower.includes('sun')) {
    return {
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      border: 'border-yellow-200 dark:border-yellow-700',
      text: 'text-yellow-600 dark:text-yellow-400',
      icon: 'text-yellow-500'
    };
  }
  return {
    bg: 'bg-gray-50 dark:bg-gray-900/20',
    border: 'border-gray-200 dark:border-gray-700',
    text: 'text-gray-600 dark:text-gray-400',
    icon: 'text-gray-500'
  };
};

const ForecastList: React.FC<ForecastListProps> = ({ forecasts, gradientColor }) => {
  return (
    <div className="space-y-3">
      {forecasts.map((forecast, index) => {
        const colors = getWeatherColors(forecast.weather);
        const isLast = index === forecasts.length - 1;
        
        return (
          <div key={forecast.time} className="relative">
            <div className={`${colors.bg} ${colors.border} border rounded-xl p-4 shadow-sm hover:shadow-md transition-all duration-200 transform hover:scale-[1.02] will-change-transform`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`flex-shrink-0 w-8 h-8 bg-white dark:bg-gray-800 rounded-full flex items-center justify-center shadow-sm border ${colors.border}`}>
                    <div className={colors.icon}>
                      {getWeatherIcon(forecast.weather)}
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-xs md:text-sm bg-white/80 dark:bg-gray-800/80 px-2 py-1 rounded text-gray-700 dark:text-gray-300">
                        {forecast.label}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {forecast.time}
                      </span>
                    </div>
                    <p className={`font-semibold text-sm md:text-base ${colors.text} mt-1`}>{forecast.weather}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="flex items-center space-x-1">
                      <Thermometer className="w-3 h-3 text-red-400" />
                      <span className="font-bold text-red-600 dark:text-red-400">{forecast.temperature}°C</span>
                    </div>
                    {forecast.precipitation > 0 && (
                      <div className="flex items-center space-x-1 mt-1">
                        <Droplets className="w-3 h-3 text-blue-400" />
                        <span className="text-sm font-medium text-blue-600 dark:text-blue-400">{forecast.precipitation}mm</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            {!isLast && (
              <div className={`absolute left-8 top-full w-0.5 h-3 bg-gradient-to-b from-${gradientColor}-300 to-transparent transform -translate-x-1/2`}></div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export const WeatherTimeline: React.FC<WeatherTimelineProps> = ({ timeline }) => {
  if (timeline.error) {
    return (
      <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border border-red-200 dark:border-red-700 rounded-xl p-6">
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0 w-8 h-8 bg-red-100 dark:bg-red-800 rounded-full flex items-center justify-center">
            <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-300" />
          </div>
          <div>
            <h4 className="font-bold text-red-800 dark:text-red-200">時系列データ取得エラー</h4>
            <p className="text-sm text-red-600 dark:text-red-400">{timeline.error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Section */}
      {timeline.summary && (
        <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-indigo-900/20 dark:via-purple-900/20 dark:to-pink-900/20 border border-indigo-200 dark:border-indigo-700 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-4">
            <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-full flex items-center justify-center shadow-lg">
              <TrendingUp className="w-4 h-4 text-white" />
            </div>
            <h4 className="text-lg font-bold text-indigo-800 dark:text-indigo-200">📊 予報概要</h4>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-center space-x-2 mb-2">
                <Cloud className="w-4 h-4 text-indigo-500" />
                <span className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">天気パターン</span>
              </div>
              <p className="text-indigo-800 dark:text-indigo-200 font-medium">{timeline.summary.weather_pattern}</p>
            </div>
            
            <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-center space-x-2 mb-2">
                <Thermometer className="w-4 h-4 text-red-500" />
                <span className="text-sm font-semibold text-red-700 dark:text-red-300">気温範囲</span>
              </div>
              <p className="text-red-800 dark:text-red-200 font-medium">{timeline.summary.temperature_range}</p>
            </div>
            
            <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-center space-x-2 mb-2">
                <Droplets className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-semibold text-blue-700 dark:text-blue-300">最大降水量</span>
              </div>
              <p className="text-blue-800 dark:text-blue-200 font-medium">{timeline.summary.max_precipitation}</p>
            </div>
          </div>
        </div>
      )}

      {/* Past Forecasts */}
      {timeline.past_forecasts && timeline.past_forecasts.length > 0 && (
        <div className="bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50 dark:from-orange-900/20 dark:via-amber-900/20 dark:to-yellow-900/20 border border-orange-200 dark:border-orange-700 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gradient-to-r from-orange-400 to-amber-500 p-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <Clock className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="text-lg font-bold text-white">📈 過去の推移</h4>
                <p className="text-sm text-orange-100">12時間前〜基準時刻</p>
              </div>
            </div>
          </div>
          
          <div className="p-6">
            <ForecastList forecasts={timeline.past_forecasts} gradientColor="orange" />
          </div>
        </div>
      )}

      {/* Future Forecasts */}
      {timeline.future_forecasts && timeline.future_forecasts.length > 0 && (
        <div className="bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50 dark:from-emerald-900/20 dark:via-green-900/20 dark:to-teal-900/20 border border-emerald-200 dark:border-emerald-700 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-gradient-to-r from-emerald-500 to-teal-500 p-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <ArrowRight className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="text-lg font-bold text-white">🔮 今後の予報</h4>
                <p className="text-sm text-emerald-100">3〜12時間後</p>
              </div>
            </div>
          </div>
          
          <div className="p-6">
            <ForecastList forecasts={timeline.future_forecasts} gradientColor="emerald" />
          </div>
        </div>
      )}
    </div>
  );
};
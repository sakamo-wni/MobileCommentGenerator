import React, { useState, useCallback } from 'react';
import { 
  CheckCircle, 
  ChevronDown, 
  ChevronUp, 
  Copy, 
  Clock, 
  Info, 
  Thermometer, 
  Wind, 
  Droplets,
  Calendar,
  TrendingUp,
  CloudRain,
  Sun,
  RotateCcw
} from 'lucide-react';
import type { WeatherMetadata, WeatherData } from '@mobile-comment-generator/shared';
import { COPY_FEEDBACK_DURATION } from '@mobile-comment-generator/shared';
import { WeatherDataDisplay } from './WeatherData';
import { WeatherTimeline } from './WeatherTimeline';

interface BatchResultItemProps {
  result: {
    success: boolean;
    location: string;
    comment?: string;
    error?: string;
    metadata?: WeatherMetadata;
    weather?: WeatherData;
    adviceComment?: string;
  };
  isExpanded: boolean;
  onToggleExpanded: () => void;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
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

export const BatchResultItem: React.FC<BatchResultItemProps> = ({
  result,
  isExpanded,
  onToggleExpanded,
  onRegenerate,
  isRegenerating = false,
}) => {
  const [copiedText, setCopiedText] = useState<string | null>(null);
  
  const handleCopyWithFeedback = useCallback(async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedText(type);
      setTimeout(() => setCopiedText(null), COPY_FEEDBACK_DURATION);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  }, []);
  
  if (!result.success) {
    return (
      <div className="relative overflow-hidden bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border border-red-200 dark:border-red-700 rounded-xl shadow-lg transition-all duration-300 hover:shadow-xl">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-red-600"></div>
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-2">
            <div className="flex-shrink-0 w-8 h-8 bg-red-100 dark:bg-red-800 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-red-600 dark:text-red-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div>
              <h3 className="font-bold text-red-800 dark:text-red-200">{result.location}</h3>
              <p className="text-sm text-red-600 dark:text-red-300">生成失敗</p>
            </div>
          </div>
          <p className="text-red-700 dark:text-red-300 text-sm bg-red-100/50 dark:bg-red-800/30 rounded-lg p-3">
            {result.error}
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-white to-green-50/30 dark:from-gray-800 dark:to-green-900/10 border border-green-200 dark:border-gray-700 rounded-xl shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-[1.02] will-change-transform">
      {/* Success indicator stripe */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-green-500 via-emerald-500 to-teal-500"></div>
      
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center shadow-lg">
              <CheckCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900 dark:text-white text-lg">{result.location}</h3>
              <p className="text-sm text-green-600 dark:text-green-400 font-medium">✨ 生成完了</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                disabled={isRegenerating}
                className={`group flex items-center space-x-2 px-3 py-2 rounded-lg shadow-md transition-all duration-200 transform hover:scale-105 ${
                  isRegenerating
                    ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-orange-400 to-amber-500 hover:from-orange-500 hover:to-amber-600 text-white hover:shadow-lg'
                }`}
              >
                <RotateCcw className={`w-3 h-3 ${isRegenerating ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-300'}`} />
                <span className="text-xs font-medium">{isRegenerating ? '再生成中...' : '再生成'}</span>
              </button>
            )}
            <button
              onClick={onToggleExpanded}
              className="group flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white rounded-lg shadow-md transition-all duration-200 hover:shadow-lg hover:scale-105"
            >
              <span className="font-medium">詳細情報</span>
              {isExpanded ? 
                <ChevronUp className="w-4 h-4 transition-transform duration-200 group-hover:scale-110" /> : 
                <ChevronDown className="w-4 h-4 transition-transform duration-200 group-hover:scale-110" />
              }
            </button>
          </div>
        </div>
        
        {/* Comments */}
        <div className="space-y-4">
          {/* Main Comment */}
          <div className="relative overflow-hidden bg-gradient-to-br from-emerald-50 to-green-100 dark:from-emerald-900/20 dark:to-green-900/20 border border-emerald-200 dark:border-emerald-700 rounded-xl p-4 shadow-sm">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Sun className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">天気コメント</span>
              </div>
              <button
                onClick={() => result.comment && handleCopyWithFeedback(result.comment, 'main')}
                className={`flex items-center space-x-1 px-3 py-1 rounded-lg text-xs font-medium transition-all duration-200 transform hover:scale-105 ${
                  copiedText === 'main'
                    ? 'bg-green-200 text-green-800 shadow-md'
                    : 'bg-white/80 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-600 shadow-sm hover:shadow-md'
                }`}
              >
                {copiedText === 'main' ? (
                  <>
                    <CheckCircle className="w-3 h-3" />
                    <span>コピー済み</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>コピー</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-emerald-900 dark:text-emerald-100 leading-relaxed">
              {result.comment}
            </p>
          </div>
          
          {/* Advice Comment */}
          {result.adviceComment && (
            <div className="relative overflow-hidden bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-700 rounded-xl p-4 shadow-sm">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Info className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm font-semibold text-blue-800 dark:text-blue-300">アドバイスコメント</span>
                </div>
                <button
                  onClick={() => result.adviceComment && handleCopyWithFeedback(result.adviceComment, 'advice')}
                  className={`flex items-center space-x-1 px-3 py-1 rounded-lg text-xs font-medium transition-all duration-200 transform hover:scale-105 ${
                    copiedText === 'advice'
                      ? 'bg-green-200 text-green-800 shadow-md'
                      : 'bg-white/80 dark:bg-gray-700 text-blue-600 dark:text-blue-300 hover:bg-white dark:hover:bg-gray-600 shadow-sm hover:shadow-md'
                  }`}
                >
                  {copiedText === 'advice' ? (
                    <>
                      <CheckCircle className="w-3 h-3" />
                      <span>コピー済み</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>コピー</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-blue-900 dark:text-blue-100 leading-relaxed">
                {result.adviceComment}
              </p>
            </div>
          )}
        </div>
      </div>
      
      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-700 bg-gradient-to-br from-gray-50 to-white dark:from-gray-800 dark:to-gray-900">
          {result.metadata ? (
            <div className="p-6 space-y-6">
              {/* Quick Stats Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {result.metadata.temperature !== undefined && (
                  <div className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 border border-red-200 dark:border-red-700 rounded-xl p-3 md:p-4 text-center shadow-sm hover:shadow-md transition-shadow">
                    <Thermometer className="w-5 h-5 md:w-6 md:h-6 text-red-500 mx-auto mb-2" />
                    <p className="text-xs font-medium text-red-700 dark:text-red-300 mb-1">気温</p>
                    <p className="text-lg md:text-xl font-bold text-red-800 dark:text-red-200">{result.metadata.temperature}°C</p>
                  </div>
                )}
                {result.metadata.weather_condition && (
                  <div className="bg-gradient-to-br from-sky-50 to-blue-50 dark:from-sky-900/20 dark:to-blue-900/20 border border-sky-200 dark:border-sky-700 rounded-xl p-3 md:p-4 text-center shadow-sm hover:shadow-md transition-shadow">
                    <Sun className="w-5 h-5 md:w-6 md:h-6 text-sky-500 mx-auto mb-2" />
                    <p className="text-xs font-medium text-sky-700 dark:text-sky-300 mb-1">天気</p>
                    <p className="text-xs md:text-sm font-bold text-sky-800 dark:text-sky-200">{result.metadata.weather_condition}</p>
                  </div>
                )}
                {result.metadata.wind_speed !== undefined && (
                  <div className="bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-900/20 dark:to-green-900/20 border border-emerald-200 dark:border-emerald-700 rounded-xl p-3 md:p-4 text-center shadow-sm hover:shadow-md transition-shadow">
                    <Wind className="w-5 h-5 md:w-6 md:h-6 text-emerald-500 mx-auto mb-2" />
                    <p className="text-xs font-medium text-emerald-700 dark:text-emerald-300 mb-1">風速</p>
                    <p className="text-lg md:text-xl font-bold text-emerald-800 dark:text-emerald-200">{result.metadata.wind_speed}m/s</p>
                  </div>
                )}
                {result.metadata.humidity !== undefined && (
                  <div className="bg-gradient-to-br from-cyan-50 to-teal-50 dark:from-cyan-900/20 dark:to-teal-900/20 border border-cyan-200 dark:border-cyan-700 rounded-xl p-3 md:p-4 text-center shadow-sm hover:shadow-md transition-shadow">
                    <Droplets className="w-5 h-5 md:w-6 md:h-6 text-cyan-500 mx-auto mb-2" />
                    <p className="text-xs font-medium text-cyan-700 dark:text-cyan-300 mb-1">湿度</p>
                    <p className="text-lg md:text-xl font-bold text-cyan-800 dark:text-cyan-200">{result.metadata.humidity}%</p>
                  </div>
                )}
              </div>
              
              {/* Forecast Base Time */}
              {result.metadata.weather_forecast_time && (
                <div className="bg-gradient-to-br from-indigo-50 via-blue-50 to-purple-50 dark:from-indigo-900/20 dark:via-blue-900/20 dark:to-purple-900/20 border border-indigo-200 dark:border-indigo-700 rounded-xl p-6 shadow-sm">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-full flex items-center justify-center shadow-lg">
                      <Clock className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h4 className="text-lg font-bold text-indigo-800 dark:text-indigo-200">予報基準時刻</h4>
                      <p className="text-sm text-indigo-600 dark:text-indigo-400">コメント生成の基準となった時刻</p>
                    </div>
                  </div>
                  <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 backdrop-blur-sm">
                    <p className="text-lg font-mono font-bold text-indigo-800 dark:text-indigo-200 mb-2">
                      {formatDateTime(result.metadata.weather_forecast_time)}
                    </p>
                    <p className="text-sm text-indigo-600 dark:text-indigo-400">
                      翌日の9時、12時、15時、18時の天気変化を分析してコメントを生成
                    </p>
                  </div>
                </div>
              )}

              {/* Weather Timeline - Enhanced */}
              {result.metadata.weather_timeline && (
                <div className="bg-gradient-to-br from-slate-50 via-gray-50 to-zinc-50 dark:from-slate-900/50 dark:via-gray-900/50 dark:to-zinc-900/50 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden shadow-lg">
                  <div className="bg-gradient-to-r from-slate-600 to-gray-600 p-4">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                        <TrendingUp className="w-4 h-4 text-white" />
                      </div>
                      <h4 className="text-lg font-bold text-white">🌦️ 詳細天気予報データ</h4>
                    </div>
                    <p className="text-sm text-slate-200 mt-1">コメント選択に使用した4時間分の予報データ</p>
                  </div>
                  <div className="p-6">
                    <WeatherTimeline timeline={result.metadata.weather_timeline} />
                  </div>
                </div>
              )}

              {/* Selected Comments - Enhanced */}
              {(result.metadata.selected_weather_comment || result.metadata.selected_advice_comment) && (
                <div className="bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 dark:from-purple-900/20 dark:via-pink-900/20 dark:to-rose-900/20 border border-purple-200 dark:border-purple-700 rounded-xl overflow-hidden shadow-lg">
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-4">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                        <Info className="w-4 h-4 text-white" />
                      </div>
                      <h4 className="text-lg font-bold text-white">💬 選択されたコメント</h4>
                    </div>
                    <p className="text-sm text-purple-100 mt-1">AI が分析して選択したコメント内容</p>
                  </div>
                  <div className="p-6 space-y-4">
                    {result.metadata.selected_weather_comment && (
                      <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 backdrop-blur-sm">
                        <h5 className="text-sm font-bold text-purple-700 dark:text-purple-300 mb-2 flex items-center">
                          <Calendar className="w-4 h-4 mr-2" />
                          天気コメント
                        </h5>
                        <p className="text-purple-800 dark:text-purple-200 leading-relaxed">
                          {result.metadata.selected_weather_comment}
                        </p>
                      </div>
                    )}
                    {result.metadata.selected_advice_comment && (
                      <div className="bg-white/60 dark:bg-gray-800/60 rounded-lg p-4 backdrop-blur-sm">
                        <h5 className="text-sm font-bold text-purple-700 dark:text-purple-300 mb-2 flex items-center">
                          <CloudRain className="w-4 h-4 mr-2" />
                          アドバイスコメント
                        </h5>
                        <p className="text-purple-800 dark:text-purple-200 leading-relaxed">
                          {result.metadata.selected_advice_comment}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            // Fallback weather display if no metadata
            result.weather && (
              <div className="p-6">
                <WeatherDataDisplay weather={result.weather} />
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
};
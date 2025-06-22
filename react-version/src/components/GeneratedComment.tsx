import React from 'react';
import { Copy, MessageSquare, Clock, MapPin, CheckCircle, RotateCcw, TrendingUp } from 'lucide-react';
import type { GeneratedComment } from '@mobile-comment-generator/shared';
import { COPY_FEEDBACK_DURATION } from '@mobile-comment-generator/shared';
import { clsx } from 'clsx';
import { WeatherTimeline } from './WeatherTimeline';

interface GeneratedCommentProps {
  comment: GeneratedComment | null;
  onCopy?: (text: string) => void;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
  className?: string;
}

export const GeneratedCommentDisplay: React.FC<GeneratedCommentProps> = ({
  comment,
  onCopy,
  onRegenerate,
  isRegenerating = false,
  className = '',
}) => {
  const [copiedText, setCopiedText] = React.useState<string | null>(null);

  const handleCopy = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedText(type);
      onCopy?.(text);
      
      // 定数を使用してタイムアウト時間を統一
      setTimeout(() => setCopiedText(null), COPY_FEEDBACK_DURATION);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  if (!comment) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400">地点を選択して「コメント生成」ボタンを押してください</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* メインコメント */}
      <div className="bg-app-surface border border-app-border rounded-lg p-6 shadow-sm">
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 flex items-center">
            <MessageSquare className="w-5 h-5 mr-2 text-blue-600" />
            天気コメント
          </h3>
          <div className="flex items-center space-x-2">
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                disabled={isRegenerating}
                className={clsx(
                  'flex items-center space-x-1 px-3 py-1 rounded-md text-sm transition-colors',
                  isRegenerating
                    ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    : 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 hover:bg-orange-200 dark:hover:bg-orange-800/50'
                )}
              >
                <RotateCcw className={`w-4 h-4 ${isRegenerating ? 'animate-spin' : ''}`} />
                <span>{isRegenerating ? '再生成中...' : '再生成'}</span>
              </button>
            )}
            <button
              onClick={() => handleCopy(comment.comment, 'main')}
              className={clsx(
                'flex items-center space-x-1 px-3 py-1 rounded-md text-sm transition-colors',
                copiedText === 'main'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              )}
            >
              {copiedText === 'main' ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span>コピー済み</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span>コピー</span>
                </>
              )}
            </button>
          </div>
        </div>
        <p className="text-gray-800 dark:text-gray-100 text-lg leading-relaxed">{comment.comment}</p>
      </div>

      {/* アドバイスコメント */}
      {comment.adviceComment && (
        <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-6">
          <div className="flex items-start justify-between mb-4">
            <h3 className="text-lg font-medium text-blue-900 dark:text-blue-300 flex items-center">
              <MessageSquare className="w-5 h-5 mr-2 text-blue-600" />
              アドバイスコメント
            </h3>
            <button
              onClick={() => handleCopy(comment.adviceComment!, 'advice')}
              className={clsx(
                'flex items-center space-x-1 px-3 py-1 rounded-md text-sm transition-colors',
                copiedText === 'advice'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800'
              )}
            >
              {copiedText === 'advice' ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span>コピー済み</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span>コピー</span>
                </>
              )}
            </button>
          </div>
          <p className="text-blue-800 dark:text-blue-300 text-lg leading-relaxed">{comment.adviceComment}</p>
        </div>
      )}

      {/* Weather Timeline */}
      {comment.metadata?.weather_timeline && (
        <div className="bg-gradient-to-br from-slate-50 via-gray-50 to-zinc-50 dark:from-slate-900/50 dark:via-gray-900/50 dark:to-zinc-900/50 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden shadow-lg">
          <div className="bg-gradient-to-r from-slate-600 to-gray-600 p-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-white" />
              </div>
              <h4 className="text-lg font-bold text-white">🌦️ 詳細天気予報データ</h4>
            </div>
            <p className="text-sm text-slate-200 mt-1">コメント選択に使用した予報データ</p>
          </div>
          <div className="p-6">
            <WeatherTimeline timeline={comment.metadata.weather_timeline} />
          </div>
        </div>
      )}

      {/* メタ情報 */}
      <div className="bg-gray-50 dark:bg-gray-800 border border-app-border rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">生成情報</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600 dark:text-gray-400">地点:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">{comment.location.name}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600 dark:text-gray-400">生成日時:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {new Date(comment.timestamp).toLocaleString('ja-JP')}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-gray-600 dark:text-gray-400">LLM:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100 capitalize">{comment.settings.llmProvider}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-gray-600 dark:text-gray-400">信頼度:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">{Math.round(comment.confidence * 100)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
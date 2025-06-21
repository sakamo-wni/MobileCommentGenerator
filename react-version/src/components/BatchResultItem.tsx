import React, { useState } from 'react';
import { CheckCircle, ChevronDown, ChevronUp, Copy } from 'lucide-react';
import { WeatherDataDisplay } from './WeatherData';

interface BatchResultItemProps {
  result: {
    success: boolean;
    location: string;
    comment?: string;
    error?: string;
    metadata?: any;
    weather?: any;
    adviceComment?: string;
  };
  isExpanded: boolean;
  onToggleExpanded: () => void;
}

export const BatchResultItem: React.FC<BatchResultItemProps> = ({
  result,
  isExpanded,
  onToggleExpanded,
}) => {
  const [copiedText, setCopiedText] = useState<string | null>(null);
  
  const handleCopyWithFeedback = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedText(type);
      setTimeout(() => setCopiedText(null), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };
  
  if (!result.success) {
    return (
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div className="p-4">
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-3">
            <div className="flex items-center text-red-700 dark:text-red-300 mb-1">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span className="font-medium">{result.location} - 生成失敗</span>
            </div>
            <div className="text-red-600 dark:text-red-400 text-sm">
              {result.error}
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <div>
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center text-green-700 dark:text-green-300">
              <CheckCircle className="w-5 h-5 mr-2" />
              <span className="font-medium">{result.location}</span>
            </div>
            <button
              onClick={onToggleExpanded}
              className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800 transition-colors"
            >
              <span>詳細情報</span>
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
          
          <div className="space-y-3">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <div className="flex items-start justify-between mb-2">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-300">天気コメント</span>
                <button
                  onClick={() => result.comment && handleCopyWithFeedback(result.comment, 'main')}
                  className={`flex items-center space-x-1 px-2 py-1 rounded text-xs transition-colors ${
                    copiedText === 'main'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500'
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
              <div className="text-gray-800 dark:text-gray-200">
                {result.comment}
              </div>
            </div>
            
            {result.adviceComment && (
              <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-3">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-sm font-medium text-blue-700 dark:text-blue-300">アドバイスコメント</span>
                  <button
                    onClick={() => result.adviceComment && handleCopyWithFeedback(result.adviceComment, 'advice')}
                    className={`flex items-center space-x-1 px-2 py-1 rounded text-xs transition-colors ${
                      copiedText === 'advice'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 dark:bg-blue-800 text-blue-600 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-700'
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
                <div className="text-blue-800 dark:text-blue-200">
                  {result.adviceComment}
                </div>
              </div>
            )}
          </div>
        </div>
        
        {isExpanded && result.weather && (
          <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800">
            <WeatherDataDisplay weather={result.weather} />
          </div>
        )}
      </div>
    </div>
  );
};
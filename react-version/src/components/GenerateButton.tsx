import React from 'react';
import { Sparkles } from 'lucide-react';

interface GenerateButtonProps {
  loading: boolean;
  disabled: boolean;
  isBatchMode: boolean;
  selectedCount?: number;
  onClick: () => void;
}

export function GenerateButton({ 
  loading, 
  disabled, 
  isBatchMode, 
  selectedCount = 0,
  onClick 
}: GenerateButtonProps) {
  const getButtonText = () => {
    if (loading) {
      return isBatchMode ? 'コメントを生成中...' : 'コメントを生成中...';
    }
    if (isBatchMode) {
      return selectedCount > 0 
        ? `選択した${selectedCount}地点のコメントを生成` 
        : 'コメントを一括生成';
    }
    return 'コメントを生成';
  };

  return (
    <div className="flex justify-center mb-8">
      <button
        onClick={onClick}
        disabled={disabled || loading}
        className={`
          flex items-center gap-2 px-8 py-4 rounded-xl font-medium text-white
          transition-all duration-200 transform
          ${loading 
            ? 'bg-gray-400 cursor-not-allowed' 
            : disabled
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 hover:scale-105 shadow-lg'
          }
        `}
      >
        <Sparkles className={`w-5 h-5 ${loading ? 'animate-pulse' : ''}`} />
        <span>{getButtonText()}</span>
      </button>
    </div>
  );
}
import React from 'react';
import { Sparkles } from 'lucide-react';

interface EmptyStateProps {
  isBatchMode: boolean;
}

export function EmptyState({ isBatchMode }: EmptyStateProps) {
  return (
    <div className="mt-8 p-8 bg-gray-50 dark:bg-gray-800 rounded-xl text-center">
      <Sparkles className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-2">
        {isBatchMode ? '地点を選択してください' : '地点を選択してコメントを生成しましょう'}
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        {isBatchMode 
          ? '複数の地点を選択して、一括でコメントを生成できます。'
          : '天気予報に基づいて、移動に適したコメントを自動生成します。'
        }
      </p>
      {!isBatchMode && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 text-left max-w-2xl mx-auto">
          <div className="bg-white dark:bg-gray-700 p-4 rounded-lg shadow-sm">
            <h4 className="font-medium text-gray-800 dark:text-gray-200 mb-2">☀️ 晴れの例</h4>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              本日の東京は晴れ、最高気温25度で過ごしやすい一日です。紫外線対策をお忘れなく。
            </p>
          </div>
          <div className="bg-white dark:bg-gray-700 p-4 rounded-lg shadow-sm">
            <h4 className="font-medium text-gray-800 dark:text-gray-200 mb-2">🌧️ 雨の例</h4>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              大阪は午後から雨、傘必須です。最高気温18度と肌寒いので上着もお持ちください。
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
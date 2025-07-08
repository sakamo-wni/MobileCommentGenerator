import React from 'react';
import { Cloud, Sun, Moon } from 'lucide-react';

interface HeaderProps {
  version: string;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export function Header({ version, theme, onToggleTheme }: HeaderProps) {
  return (
    <header className="text-center mb-8 relative">
      <div className="flex items-center justify-center gap-2 mb-2">
        <Cloud className="w-8 h-8 text-blue-500" />
        <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">
          移動用天気コメント生成AI
        </h1>
      </div>
      <p className="text-gray-600 dark:text-gray-300">
        最新の気象情報から最適な天気コメントを生成
      </p>
      <div className="absolute top-0 right-0 flex items-center gap-2">
        <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-1 rounded">
          {version}
        </span>
        <button
          onClick={onToggleTheme}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'light' ? (
            <Moon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          ) : (
            <Sun className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          )}
        </button>
      </div>
    </header>
  );
}
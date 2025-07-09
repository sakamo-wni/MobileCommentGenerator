import React from 'react';
import { Sun, Moon } from 'lucide-react';

interface HeaderProps {
  version: string;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export function Header({ version, theme, onToggleTheme }: HeaderProps) {
  return (
    <header className="bg-white dark:bg-gray-800 shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Sun className="w-8 h-8 text-yellow-500 mr-3" />
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              天気コメント生成システム
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              React版 {version}
            </span>
            <button
              type="button"
              onClick={onToggleTheme}
              className="p-2 rounded-lg text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              aria-label={theme === 'light' ? 'ダークモードに切り替え' : 'ライトモードに切り替え'}
            >
              {theme === 'light' ? (
                <Moon className="h-5 w-5" />
              ) : (
                <Sun className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
import { defineConfig } from 'unocss'
import { presetUno } from '@unocss/preset-uno'
import { presetTypography } from '@unocss/preset-typography'

export default defineConfig({
  presets: [
    presetUno(),
    presetTypography()
  ],
  
  safelist: [
    'max-h-40',
    'h-40',
    'overflow-y-auto',
    'border',
    'border-gray-200',
    'rounded',
    'hover:bg-gray-50'
  ],
  
  theme: {
    colors: {
      // 既存のプライマリカラー（拡張）
      primary: {
        50: '#eff6ff',
        100: '#dbeafe',
        200: '#bfdbfe',
        300: '#93c5fd',
        400: '#60a5fa',
        500: '#3b82f6',
        600: '#2563eb',
        700: '#1d4ed8',
        800: '#1e40af',
        900: '#1e3a8a',
        950: '#172554'
      },
      
      // セカンダリカラー（グレー系）
      secondary: {
        50: '#f8fafc',
        100: '#f1f5f9',
        200: '#e2e8f0',
        300: '#cbd5e1',
        400: '#94a3b8',
        500: '#64748b',
        600: '#475569',
        700: '#334155',
        800: '#1e293b',
        900: '#0f172a',
        950: '#020617'
      },
      
      // 天気状態専用カラー
      weather: {
        sunny: {
          light: '#fbbf24',
          DEFAULT: '#f59e0b',
          dark: '#d97706'
        },
        cloudy: {
          light: '#9ca3af',
          DEFAULT: '#6b7280',
          dark: '#4b5563'
        },
        rainy: {
          light: '#60a5fa',
          DEFAULT: '#3b82f6',
          dark: '#1d4ed8'
        },
        snowy: {
          light: '#f3f4f6',
          DEFAULT: '#e5e7eb',
          dark: '#d1d5db'
        },
        stormy: {
          light: '#a78bfa',
          DEFAULT: '#7c3aed',
          dark: '#5b21b6'
        }
      },
      
      // 既存blueカラー（互換性維持）
      blue: {
        500: '#0C419A',
        600: '#6BA2FC'
      },
      
      // ステータスカラー
      success: {
        50: '#f0fdf4',
        100: '#dcfce7',
        200: '#bbf7d0',
        500: '#22c55e',
        600: '#16a34a',
        700: '#15803d',
        800: '#166534',
        900: '#14532d'
      },
      error: {
        50: '#fef2f2',
        100: '#fee2e2',
        200: '#fecaca',
        500: '#ef4444',
        600: '#dc2626',
        700: '#b91c1c',
        800: '#991b1b',
        900: '#7f1d1d'
      },
      warning: {
        50: '#fffbeb',
        100: '#fef3c7',
        200: '#fed7aa',
        500: '#f59e0b',
        600: '#d97706',
        700: '#b45309',
        800: '#92400e',
        900: '#78350f'
      }
    },
    
    // スペーシング拡張
    spacing: {
      '18': '4.5rem',
      '88': '22rem',
      '100': '25rem'
    },
    
    // シャドウ拡張
    boxShadow: {
      'soft': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
      'medium': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      'strong': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
    }
  },
  
  shortcuts: {
    // === レイアウト系ショートカット ===
    'container-main': 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',
    'container-content': 'max-w-4xl mx-auto px-4 sm:px-6',
    'container-narrow': 'max-w-2xl mx-auto px-4 sm:px-6',
    
    // Flexbox便利クラス
    'flex-center': 'flex items-center justify-center',
    'flex-between': 'flex items-center justify-between',
    'flex-start': 'flex items-center justify-start',
    'flex-end': 'flex items-center justify-end',
    'flex-col-center': 'flex flex-col items-center justify-center',
    
    // Grid便利クラス
    'grid-responsive': 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6',
    'grid-auto-fit': 'grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-4',
    
    // === テキスト系ショートカット ===
    'text-heading': 'font-semibold text-secondary-900 dark:text-white tracking-tight',
    'text-subheading': 'font-medium text-secondary-700 dark:text-secondary-300',
    'text-body': 'text-secondary-700 dark:text-secondary-300 leading-relaxed',
    'text-body-sm': 'text-sm text-secondary-600 dark:text-secondary-400 leading-relaxed',
    'text-muted': 'text-secondary-500 dark:text-secondary-400',
    
    // === 既存ボタン（更新） ===
    'btn-primary': 'px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
    'btn-outline': 'px-4 py-2 border border-secondary-300 text-secondary-700 rounded-lg hover:bg-secondary-50 transition-colors',
    'btn-xs': 'px-2 py-1 text-xs',
    'btn-sm': 'px-3 py-1.5 text-sm',
    'btn-md': 'px-4 py-2 text-sm',
    'btn-lg': 'px-6 py-3 text-base',
    'btn-green': 'bg-success-600 text-white hover:bg-success-700',
    'btn-red': 'bg-error-600 text-white hover:bg-error-700',
    'btn-gray': 'bg-secondary-600 text-white hover:bg-secondary-700',
    
    // === カードコンポーネント（更新） ===
    'card': 'bg-white dark:bg-secondary-800 rounded-lg shadow-soft border border-secondary-200 dark:border-secondary-700',
    'card-header': 'bg-gradient-to-r from-primary-500 to-primary-600 text-white p-4 font-semibold',
    
    // === アラートコンポーネント（更新） ===
    'alert-blue': 'bg-primary-50 border border-primary-200 text-primary-800 rounded-lg p-4',
    'alert-green': 'bg-success-50 border border-success-200 text-success-800 rounded-lg p-4',
    'alert-red': 'bg-error-50 border border-error-200 text-error-800 rounded-lg p-4',
    'alert-warning': 'bg-warning-50 border border-warning-200 text-warning-800 rounded-lg p-4',
    
    // === フォームコンポーネント（更新） ===
    'form-input': 'w-full px-3 py-2 border border-secondary-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors',
    'form-select': 'w-full px-3 py-2 border border-secondary-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white transition-colors',
    
    // === 天気アプリ専用ショートカット ===
    'weather-card': 'card p-6 flex-col-center text-center',
    'weather-sunny': 'bg-weather-sunny text-white',
    'weather-cloudy': 'bg-weather-cloudy text-white',
    'weather-rainy': 'bg-weather-rainy text-white',
    'weather-snowy': 'bg-weather-snowy text-secondary-800',
    'weather-stormy': 'bg-weather-stormy text-white',
    
    // === スペーシングショートカット ===
    'spacing-content': 'space-y-6',
    'spacing-section': 'space-y-8 sm:space-y-12',
    'spacing-compact': 'space-y-3',
    'spacing-comfortable': 'space-y-4 sm:space-y-6'
  }
})

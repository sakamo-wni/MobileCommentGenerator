import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: ['class'],
  // Vanilla Extract のテーマクラスをパージ対象外にする場合:
  // safelist: ['<%= themeClass %>'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['system-ui', 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', 'Meiryo', 'sans-serif'],
      },
      colors: {
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
        },
        'app-bg': 'var(--app-color-bg)',
        'app-surface': 'var(--app-color-surface)',
        'app-border': 'var(--app-color-border)',
        'app-text': 'var(--app-color-text)',
      },
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        shimmer: 'shimmer 2s infinite linear',
      },
    },
  },
} satisfies Config
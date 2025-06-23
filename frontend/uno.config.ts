import { defineConfig } from 'unocss'
import { presetUno } from '@unocss/preset-uno'
import { presetTypography } from '@unocss/preset-typography'

export default defineConfig({
  presets: [
    presetUno(),
    presetTypography()
  ],
  
  theme: {
    colors: {
      primary: {
        50: '#eff6ff',
        500: '#3b82f6',
        600: '#2563eb',
        700: '#1d4ed8'
      },
      blue: {
        500: '#0C419A',
        600: '#6BA2FC'
      }
    }
  },
  
  shortcuts: {
    'btn-primary': 'px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed',
    'btn-outline': 'px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors',
    'btn-xs': 'px-2 py-1 text-xs',
    'btn-sm': 'px-3 py-1.5 text-sm',
    'btn-md': 'px-4 py-2 text-sm',
    'btn-lg': 'px-6 py-3 text-base',
    'btn-green': 'bg-green-600 text-white hover:bg-green-700',
    'btn-red': 'bg-red-600 text-white hover:bg-red-700',
    'btn-gray': 'bg-gray-600 text-white hover:bg-gray-700',
    'card': 'bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700',
    'card-header': 'bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4 font-semibold',
    'alert-blue': 'bg-blue-50 border border-blue-200 text-blue-800 rounded-lg p-4',
    'alert-green': 'bg-green-50 border border-green-200 text-green-800 rounded-lg p-4',
    'alert-red': 'bg-red-50 border border-red-200 text-red-800 rounded-lg p-4',
    'form-input': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
    'form-select': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'
  }
})

<template>
  <div :class="containerClasses">
    <!-- スピナー -->
    <div 
      v-if="type === 'spinner'"
      :class="spinnerClasses"
      role="status"
      :aria-label="ariaLabel"
    >
      <svg class="animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span class="sr-only">{{ text || '読み込み中...' }}</span>
    </div>
    
    <!-- ドット -->
    <div 
      v-else-if="type === 'dots'"
      class="flex space-x-1"
      role="status"
      :aria-label="ariaLabel"
    >
      <div 
        v-for="i in 3" 
        :key="i"
        :class="dotClasses"
        :style="{ animationDelay: `${(i - 1) * 0.1}s` }"
      />
      <span class="sr-only">{{ text || '読み込み中...' }}</span>
    </div>
    
    <!-- パルス -->
    <div 
      v-else-if="type === 'pulse'"
      :class="pulseClasses"
      role="status"
      :aria-label="ariaLabel"
    >
      <span class="sr-only">{{ text || '読み込み中...' }}</span>
    </div>
    
    <!-- スケルトン -->
    <div 
      v-else-if="type === 'skeleton'"
      :class="skeletonClasses"
      role="status"
      :aria-label="ariaLabel"
    >
      <span class="sr-only">{{ text || '読み込み中...' }}</span>
    </div>
    
    <!-- テキスト付きローディング -->
    <div 
      v-show="text && showText"
      :class="textClasses"
    >
      {{ text }}
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Loading Component
 * 
 * @description
 * 様々なスタイルのローディングインジケーターを提供するコンポーネント。
 * スピナー、ドット、パルス、スケルトンの4種類のアニメーションに対応。
 * 
 * @example
 * ```vue
 * <!-- 基本的なスピナー -->
 * <Loading />
 * 
 * <!-- サイズと色を指定 -->
 * <Loading size="lg" color="secondary" />
 * 
 * <!-- テキスト付き -->
 * <Loading text="データを読み込んでいます..." show-text />
 * 
 * <!-- ドットアニメーション -->
 * <Loading type="dots" size="sm" />
 * 
 * <!-- 中央寄せ -->
 * <Loading center />
 * ```
 */
import { computed } from 'vue'

interface Props {
  /**
   * ローディングアニメーションの種類
   * @default 'spinner'
   */
  type?: 'spinner' | 'dots' | 'pulse' | 'skeleton'
  
  /**
   * ローディングインジケーターのサイズ
   * @default 'md'
   */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  
  /**
   * ローディングインジケーターの色
   * @default 'primary'
   */
  color?: 'primary' | 'secondary' | 'white' | 'current'
  
  /**
   * ローディングテキスト
   */
  text?: string
  
  /**
   * テキストを表示するか
   * @default false
   */
  showText?: boolean
  
  /**
   * コンテナを中央寄せするか
   * @default false
   */
  center?: boolean
  
  /**
   * スクリーンリーダー用のARIAラベル
   */
  ariaLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'spinner',
  size: 'md',
  color: 'primary',
  showText: false,
  center: false
})

// コンテナクラス
const containerClasses = computed(() => [
  props.center ? 'flex flex-col items-center justify-center' : 'inline-flex items-center',
  props.showText && props.text ? 'space-y-2' : ''
])

// スピナークラス
const spinnerClasses = computed(() => {
  const sizes = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-10 h-10'
  }
  
  const colors = {
    primary: 'text-primary-500',
    secondary: 'text-secondary-500',
    white: 'text-white',
    current: 'text-current'
  }
  
  return [
    sizes[props.size],
    colors[props.color]
  ]
})

// ドットクラス
const dotClasses = computed(() => {
  const sizes = {
    xs: 'w-1 h-1',
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
    xl: 'w-3 h-3'
  }
  
  const colors = {
    primary: 'bg-primary-500',
    secondary: 'bg-secondary-500',
    white: 'bg-white',
    current: 'bg-current'
  }
  
  return [
    'rounded-full animate-bounce-custom',
    sizes[props.size],
    colors[props.color]
  ]
})

// パルスクラス
const pulseClasses = computed(() => {
  const sizes = {
    xs: 'w-6 h-6',
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
    xl: 'w-20 h-20'
  }
  
  const colors = {
    primary: 'bg-primary-500',
    secondary: 'bg-secondary-500',
    white: 'bg-white',
    current: 'bg-current'
  }
  
  return [
    'rounded-full animate-pulse',
    sizes[props.size],
    colors[props.color]
  ]
})

// スケルトンクラス
const skeletonClasses = computed(() => {
  const colors = {
    primary: 'bg-primary-200 dark:bg-primary-800',
    secondary: 'bg-secondary-200 dark:bg-secondary-700', 
    white: 'bg-white/20',
    current: 'bg-current/20'
  }
  
  return [
    'animate-pulse rounded',
    'w-full h-4', // デフォルトサイズ
    colors[props.color]
  ]
})

// テキストクラス
const textClasses = computed(() => [
  'text-sm text-secondary-600 dark:text-secondary-400',
  props.center ? 'text-center' : ''
])
</script>

<style scoped>
/* カスタムアニメーション */
@keyframes bounce-custom {
  0%, 20%, 53%, 80%, 100% {
    transform: translate3d(0,0,0);
  }
  40%, 43% {
    transform: translate3d(0, -8px, 0);
  }
  70% {
    transform: translate3d(0, -4px, 0);
  }
  90% {
    transform: translate3d(0, -2px, 0);
  }
}

.animate-bounce-custom {
  animation: bounce-custom 1.4s ease-in-out infinite both;
}

/* スクリーンリーダー用の非表示クラス */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
<template>
  <component
    :is="as"
    :class="buttonClasses"
    :disabled="disabled || loading"
    :type="as === 'button' ? type : undefined"
    :aria-busy="loading"
    :aria-disabled="disabled || loading"
    v-bind="$attrs"
    @click="handleClick"
  >
    <!-- ローディングスピナー -->
    <span 
      v-show="loading" 
      class="loading-spinner mr-2"
      aria-hidden="true"
    >
      <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </span>
    
    <!-- 左側アイコン -->
    <i 
      v-show="!loading && iconLeft"
      :class="iconLeft"
      class="mr-2"
      aria-hidden="true"
    />
    
    <!-- ボタンテキスト -->
    <span v-if="$slots.default">
      <slot />
    </span>
    
    <!-- 右側アイコン -->
    <i 
      v-if="iconRight && !loading"
      :class="iconRight"
      class="ml-2"
      aria-hidden="true"
    />
  </component>
</template>

<script setup lang="ts">
/**
 * Button Component
 * 
 * @description
 * 汎用的なボタンコンポーネント。様々なバリアント、サイズ、状態に対応し、
 * アクセシビリティとレスポンシブデザインを考慮した実装。
 * 
 * @example
 * ```vue
 * <!-- 基本的な使用例 -->
 * <Button @click="handleClick">クリック</Button>
 * 
 * <!-- バリアントとサイズの指定 -->
 * <Button variant="secondary" size="lg">大きいボタン</Button>
 * 
 * <!-- ローディング状態 -->
 * <Button :loading="isLoading">保存中...</Button>
 * 
 * <!-- アイコン付きボタン -->
 * <Button icon-left="i-heroicons-plus">新規作成</Button>
 * 
 * <!-- リンクとして使用 -->
 * <Button as="nuxt-link" to="/about">詳細を見る</Button>
 * ```
 */
import { computed } from 'vue'

interface Props {
  /**
   * ボタンの見た目のバリエーション
   * @default 'primary'
   */
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger'
  
  /**
   * ボタンのサイズ
   * @default 'md'
   */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  
  /**
   * レンダリングするHTML要素またはコンポーネント
   * @default 'button'
   */
  as?: 'button' | 'a' | 'router-link' | 'nuxt-link'
  
  /**
   * ボタンのtype属性（button要素の場合のみ有効）
   * @default 'button'
   */
  type?: 'button' | 'submit' | 'reset'
  
  /**
   * ボタンを無効化するか
   * @default false
   */
  disabled?: boolean
  
  /**
   * ローディング状態を表示するか
   * @default false
   */
  loading?: boolean
  
  /**
   * 左側に表示するアイコンクラス（UnoCSS icon形式）
   */
  iconLeft?: string
  
  /**
   * 右側に表示するアイコンクラス（UnoCSS icon形式）
   */
  iconRight?: string
  
  /**
   * ボタンを親要素の幅いっぱいに広げるか
   * @default false
   */
  fullWidth?: boolean
  
  /**
   * 角丸を無効にするか
   * @default false
   */
  square?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  as: 'button',
  type: 'button',
  disabled: false,
  loading: false,
  fullWidth: false,
  square: false
})

/**
 * Emit定義
 */
interface Emits {
  /**
   * ボタンがクリックされたときに発火
   * @param event - MouseEvent
   */
  click: [event: MouseEvent]
}

const emit = defineEmits<Emits>()

// バリアント別スタイル
const variantClasses = computed(() => {
  const variants = {
    primary: 'bg-primary-500 hover:bg-primary-600 active:bg-primary-700 text-white shadow-soft hover:shadow-medium focus-visible:ring-primary-500',
    
    secondary: 'bg-secondary-100 hover:bg-secondary-200 active:bg-secondary-300 text-secondary-700 focus-visible:ring-secondary-500 dark:bg-secondary-800 dark:hover:bg-secondary-700 dark:text-secondary-300',
    
    ghost: 'hover:bg-secondary-100 active:bg-secondary-200 text-secondary-600 hover:text-secondary-800 focus-visible:ring-secondary-500 dark:hover:bg-secondary-800 dark:text-secondary-400 dark:hover:text-secondary-200',
    
    outline: 'border-2 border-secondary-300 hover:border-secondary-400 active:border-secondary-500 text-secondary-700 hover:text-secondary-800 focus-visible:ring-secondary-500 dark:border-secondary-600 dark:hover:border-secondary-500 dark:text-secondary-300',
    
    danger: 'bg-error-500 hover:bg-error-600 active:bg-error-700 text-white shadow-soft hover:shadow-medium focus-visible:ring-error-500'
  }
  return variants[props.variant]
})

// サイズ別スタイル
const sizeClasses = computed(() => {
  const sizes = {
    xs: 'px-2.5 py-1.5 text-xs font-medium',
    sm: 'px-3 py-2 text-sm font-medium',
    md: 'px-4 py-2.5 text-sm font-medium',
    lg: 'px-5 py-3 text-base font-medium',
    xl: 'px-6 py-3.5 text-base font-semibold'
  }
  return sizes[props.size]
})

// 最終的なクラス結合
const buttonClasses = computed(() => [
  // 基本スタイル
  'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
  
  // バリアント・サイズ
  variantClasses.value,
  sizeClasses.value,
  
  // 条件付きスタイル
  props.fullWidth ? 'w-full' : '',
  props.square ? 'rounded-none' : 'rounded-lg',
  props.loading ? 'cursor-wait' : ''
])

// クリックハンドラー
const handleClick = (event: MouseEvent) => {
  if (props.disabled || props.loading) {
    event.preventDefault()
    return
  }
  emit('click', event)
}
</script>
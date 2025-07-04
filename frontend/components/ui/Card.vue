<template>
  <div :class="cardClasses" @click="handleClick">
    <!-- ヘッダー -->
    <header 
      v-if="$slots.header || title"
      class="card-header"
      :class="headerClasses"
    >
      <div v-if="title" class="flex-between">
        <h3 class="text-heading text-lg">{{ title }}</h3>
        <slot name="headerActions" />
      </div>
      <slot v-else name="header" />
    </header>
    
    <!-- メインコンテンツ -->
    <div class="card-content" :class="contentClasses">
      <slot />
    </div>
    
    <!-- フッター -->
    <footer 
      v-if="$slots.footer"
      class="card-footer"
      :class="footerClasses"
    >
      <slot name="footer" />
    </footer>
  </div>
</template>

<script setup lang="ts">
/**
 * Card Component
 * 
 * @description
 * 柔軟なレイアウトとバリアントを持つカードコンポーネント。
 * ヘッダー、メインコンテンツ、フッターの3つのセクションを持ち、
 * 様々な用途に対応できる汎用的な設計。
 * 
 * @example
 * ```vue
 * <!-- 基本的な使用例 -->
 * <Card>
 *   <p>カードの内容</p>
 * </Card>
 * 
 * <!-- タイトル付き -->
 * <Card title="カードタイトル">
 *   <p>カードの内容</p>
 * </Card>
 * 
 * <!-- ホバー効果とクリック可能 -->
 * <Card hoverable clickable @click="handleCardClick">
 *   <p>クリック可能なカード</p>
 * </Card>
 * 
 * <!-- スロットを使用した複雑なレイアウト -->
 * <Card>
 *   <template #header>
 *     <h3>カスタムヘッダー</h3>
 *   </template>
 *   <p>メインコンテンツ</p>
 *   <template #footer>
 *     <Button>アクション</Button>
 *   </template>
 * </Card>
 * ```
 */
import { computed } from 'vue'

interface Props {
  /**
   * カードの外観バリアント
   * @default 'default'
   */
  variant?: 'default' | 'outlined' | 'elevated' | 'glass'
  
  /**
   * カードの内側の余白サイズ
   * @default 'md'
   */
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  
  /**
   * ホバー時にカードを浮かせるエフェクトを有効にする
   * @default false
   */
  hoverable?: boolean
  
  /**
   * カードをクリック可能にする
   * @default false
   */
  clickable?: boolean
  
  /**
   * ヘッダーに表示するタイトル（headerスロットより優先度が低い）
   */
  title?: string
  
  /**
   * カードの角丸サイズ
   * @default 'lg'
   */
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  padding: 'md',
  hoverable: false,
  clickable: false,
  rounded: 'lg'
})

/**
 * Emit定義
 */
interface Emits {
  /**
   * カードがクリックされたときに発火（clickableがtrueの場合のみ）
   * @param event - MouseEvent
   */
  click: [event: MouseEvent]
}

const emit = defineEmits<Emits>()

// バリアント別スタイル
const variantClasses = computed(() => {
  const variants = {
    default: 'bg-white dark:bg-secondary-800 border border-secondary-200 dark:border-secondary-700 shadow-soft',
    
    outlined: 'bg-white dark:bg-secondary-800 border-2 border-secondary-300 dark:border-secondary-600',
    
    elevated: 'bg-white dark:bg-secondary-800 border border-secondary-200 dark:border-secondary-700 shadow-medium',
    
    glass: 'backdrop-blur-lg bg-white/70 dark:bg-secondary-800/70 border border-white/20 dark:border-secondary-700/50 shadow-glass'
  }
  return variants[props.variant]
})

// 角丸クラス
const roundedClasses = computed(() => {
  const rounded = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md', 
    lg: 'rounded-lg',
    xl: 'rounded-xl'
  }
  return rounded[props.rounded]
})

// パディングクラス
const paddingClasses = computed(() => {
  const padding = {
    none: '',
    sm: 'p-3',
    md: 'p-4 sm:p-6',
    lg: 'p-6 sm:p-8',
    xl: 'p-8 sm:p-10'
  }
  return padding[props.padding]
})

// 最終的なカードクラス
const cardClasses = computed(() => [
  'transition-all duration-200',
  variantClasses.value,
  roundedClasses.value,
  paddingClasses.value,
  
  // 条件付きスタイル
  props.hoverable ? 'hover:shadow-medium hover:-translate-y-0.5' : '',
  props.clickable ? 'cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2' : ''
])

// ヘッダー/フッター/コンテンツのクラス
const headerClasses = computed(() => 
  props.padding !== 'none' ? 'pb-4 mb-4 border-b border-secondary-200 dark:border-secondary-700' : ''
)

const footerClasses = computed(() => 
  props.padding !== 'none' ? 'pt-4 mt-4 border-t border-secondary-200 dark:border-secondary-700' : ''
)

const contentClasses = computed(() => 
  props.padding === 'none' ? 'p-4 sm:p-6' : ''
)

// クリックハンドラー
const handleClick = (event: MouseEvent) => {
  if (props.clickable) {
    emit('click', event)
  }
}
</script>
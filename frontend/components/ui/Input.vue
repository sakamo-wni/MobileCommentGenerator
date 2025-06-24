<template>
  <div class="input-group" :class="groupClasses">
    <!-- ラベル -->
    <label 
      v-if="label"
      :for="inputId"
      class="input-label"
      :class="labelClasses"
    >
      {{ label }}
      <span v-if="required" class="text-error-500 ml-1" aria-label="必須">*</span>
    </label>
    
    <!-- 入力フィールドコンテナ -->
    <div class="relative">
      <!-- 左側アイコン -->
      <div 
        v-if="iconLeft"
        class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none"
      >
        <i :class="iconLeft" class="text-secondary-400" aria-hidden="true" />
      </div>
      
      <!-- 入力フィールド -->
      <input
        :id="inputId"
        ref="inputRef"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :autocomplete="autocomplete"
        :class="inputClasses"
        :aria-invalid="hasError"
        :aria-describedby="hasError ? `${inputId}-error` : helpText ? `${inputId}-help` : undefined"
        @input="handleInput"
        @blur="handleBlur"
        @focus="handleFocus"
      />
      
      <!-- 右側アイコン/クリアボタン -->
      <div 
        v-if="iconRight || (clearable && modelValue)"
        class="absolute inset-y-0 right-0 flex items-center pr-3"
      >
        <!-- クリアボタン -->
        <button
          v-if="clearable && modelValue && !disabled"
          type="button"
          class="text-secondary-400 hover:text-secondary-600 transition-colors p-1 rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
          @click="handleClear"
          aria-label="入力をクリア"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        
        <!-- 右側アイコン -->
        <i 
          v-else-if="iconRight"
          :class="iconRight" 
          class="text-secondary-400"
          aria-hidden="true"
        />
      </div>
    </div>
    
    <!-- ヘルプテキスト -->
    <p 
      v-if="helpText && !hasError"
      :id="`${inputId}-help`"
      class="input-help"
    >
      {{ helpText }}
    </p>
    
    <!-- エラーメッセージ -->
    <p 
      v-if="hasError"
      :id="`${inputId}-error`"
      class="input-error"
      role="alert"
    >
      {{ errorMessage }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  // v-model
  modelValue?: string | number
  // 基本属性
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search'
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
  required?: boolean
  autocomplete?: string
  
  // UI関連
  label?: string
  helpText?: string
  errorMessage?: string
  iconLeft?: string
  iconRight?: string
  clearable?: boolean
  
  // スタイル
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'outlined' | 'filled'
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  disabled: false,
  readonly: false,
  required: false,
  clearable: false,
  size: 'md',
  variant: 'default'
})

interface Emits {
  'update:modelValue': [value: string | number]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
  clear: []
}

const emit = defineEmits<Emits>()

// リアクティブプロパティ
const inputRef = ref<HTMLInputElement>()
const inputId = ref(`input-${Math.random().toString(36).substr(2, 9)}`)
const isFocused = ref(false)

// 計算プロパティ
const hasError = computed(() => !!props.errorMessage)

const groupClasses = computed(() => [
  'space-y-2'
])

const labelClasses = computed(() => [
  'block text-sm font-medium text-secondary-700 dark:text-secondary-300'
])

const inputClasses = computed(() => {
  const base = [
    'block w-full rounded-lg transition-all duration-200',
    'placeholder:text-secondary-400',
    'focus:outline-none focus:ring-2 focus:ring-offset-0',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    'read-only:bg-secondary-50 read-only:cursor-default dark:read-only:bg-secondary-800'
  ]
  
  // サイズ別スタイル
  const sizes = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-3 py-2.5 text-sm',
    lg: 'px-4 py-3 text-base'
  }
  
  // バリアント別スタイル
  const variants = {
    default: hasError.value 
      ? 'border border-error-300 focus:border-error-500 focus:ring-error-500/20 bg-white dark:bg-secondary-800 dark:border-error-500'
      : 'border border-secondary-300 focus:border-primary-500 focus:ring-primary-500/20 bg-white dark:bg-secondary-800 dark:border-secondary-600 dark:focus:border-primary-400',
      
    outlined: hasError.value
      ? 'border-2 border-error-300 focus:border-error-500 bg-transparent'
      : 'border-2 border-secondary-300 focus:border-primary-500 bg-transparent dark:border-secondary-600',
      
    filled: hasError.value
      ? 'border border-error-300 focus:border-error-500 bg-error-50 focus:bg-white dark:bg-error-900/20 dark:border-error-500'
      : 'border border-secondary-200 focus:border-primary-500 bg-secondary-50 focus:bg-white dark:bg-secondary-800 dark:border-secondary-700'
  }
  
  return [
    ...base,
    sizes[props.size],
    variants[props.variant],
    
    // アイコンがある場合のパディング調整
    props.iconLeft ? 'pl-10' : '',
    (props.iconRight || (props.clearable && props.modelValue)) ? 'pr-10' : ''
  ]
})

// イベントハンドラー
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = props.type === 'number' ? Number(target.value) : target.value
  emit('update:modelValue', value)
}

const handleFocus = (event: FocusEvent) => {
  isFocused.value = true
  emit('focus', event)
}

const handleBlur = (event: FocusEvent) => {
  isFocused.value = false
  emit('blur', event)
}

const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
  inputRef.value?.focus()
}

// 外部からフォーカス可能にする
const focus = () => {
  inputRef.value?.focus()
}

const blur = () => {
  inputRef.value?.blur()
}

defineExpose({
  focus,
  blur,
  inputRef
})
</script>

<style scoped>
.input-help {
  @apply text-sm text-secondary-500 dark:text-secondary-400;
}

.input-error {
  @apply text-sm text-error-600 dark:text-error-400 font-medium;
}
</style>
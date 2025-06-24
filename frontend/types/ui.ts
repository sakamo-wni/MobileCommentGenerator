// UI コンポーネント用の型定義

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  as?: 'button' | 'a' | 'router-link' | 'nuxt-link'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
  iconLeft?: string
  iconRight?: string
  fullWidth?: boolean
  square?: boolean
}

export interface ButtonEmits {
  click: [event: MouseEvent]
}

export interface CardProps {
  variant?: 'default' | 'outlined' | 'elevated' | 'glass'
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  hoverable?: boolean
  clickable?: boolean
  title?: string
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
}

export interface CardEmits {
  click: [event: MouseEvent]
}

export interface InputProps {
  modelValue?: string | number
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search'
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
  required?: boolean
  autocomplete?: string
  label?: string
  helpText?: string
  errorMessage?: string
  iconLeft?: string
  iconRight?: string
  clearable?: boolean
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'outlined' | 'filled'
}

export interface InputEmits {
  'update:modelValue': [value: string | number]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
  clear: []
}

export interface LoadingProps {
  type?: 'spinner' | 'dots' | 'pulse' | 'skeleton'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  color?: 'primary' | 'secondary' | 'white' | 'current'
  text?: string
  showText?: boolean
  center?: boolean
  ariaLabel?: string
}

// 共通のユーティリティ型
export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
export type Variant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger'
export type Color = 'primary' | 'secondary' | 'success' | 'warning' | 'error'

// カラーバリアント型（Phase 1-4-1で定義した天気カラーに対応）
export type WeatherColor = 'sunny' | 'cloudy' | 'rainy' | 'snowy' | 'stormy' | 'foggy'

// UIコンポーネントの共通プロパティ
export interface BaseUIProps {
  class?: string | string[] | Record<string, boolean>
  style?: string | Record<string, string>
  id?: string
}

// フォームコンポーネントの基本インターフェース
export interface FormControlProps extends BaseUIProps {
  disabled?: boolean
  required?: boolean
  readonly?: boolean
  name?: string
}

// アクセシビリティ関連の型
export interface AriaProps {
  ariaLabel?: string
  ariaLabelledby?: string
  ariaDescribedby?: string
  ariaInvalid?: boolean
  ariaExpanded?: boolean
  ariaSelected?: boolean
  ariaChecked?: boolean
  ariaDisabled?: boolean
  ariaHidden?: boolean
  role?: string
}

// イベントハンドラーの型
export interface UIEventHandlers {
  onClick?: (event: MouseEvent) => void
  onFocus?: (event: FocusEvent) => void
  onBlur?: (event: FocusEvent) => void
  onKeydown?: (event: KeyboardEvent) => void
  onKeyup?: (event: KeyboardEvent) => void
}

// レスポンシブ対応の型
export type ResponsiveValue<T> = T | {
  sm?: T
  md?: T
  lg?: T
  xl?: T
}

// テーマ関連の型
export interface ThemeProps {
  theme?: 'light' | 'dark' | 'auto'
}

// アニメーション関連の型
export interface AnimationProps {
  animated?: boolean
  duration?: 'fast' | 'normal' | 'slow'
  easing?: 'ease-in' | 'ease-out' | 'ease-in-out'
}
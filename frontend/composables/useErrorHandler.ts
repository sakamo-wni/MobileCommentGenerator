import { ref } from 'vue'
import type { Ref } from 'vue'

export interface ErrorHandlerOptions {
  defaultMessage?: string
  logErrors?: boolean
}

export interface ApiError {
  message?: string
  code?: string
  response?: {
    data?: any
    status?: number
  }
}

export interface ErrorDetails {
  message: string
  code?: string
  timestamp: Date
  details?: any
}

// 型ガード関数
export const isApiError = (error: unknown): error is ApiError => {
  return (
    typeof error === 'object' &&
    error !== null &&
    ('message' in error || 'code' in error || 'response' in error)
  )
}

export const useErrorHandler = (options: ErrorHandlerOptions = {}) => {
  const {
    defaultMessage = 'エラーが発生しました',
    logErrors = true
  } = options

  const error = ref<ErrorDetails | null>(null)
  const isError = ref(false)

  const handleError = (err: unknown, customMessage?: string): ErrorDetails => {
    let errorMessage = customMessage || defaultMessage
    let errorCode: string | undefined
    let errorDetails: any

    // エラーの種類に応じて処理
    if (err instanceof Error) {
      errorMessage = customMessage || err.message
      errorDetails = {
        name: err.name,
        stack: err.stack
      }
    } else if (typeof err === 'string') {
      errorMessage = err
    } else if (isApiError(err)) {
      // APIエラーレスポンスの処理
      if (err.message) {
        errorMessage = customMessage || err.message
      }
      if (err.code) {
        errorCode = err.code
      }
      if (err.response?.data) {
        errorDetails = err.response.data
      }
      if (err.response?.status) {
        errorMessage = `${errorMessage} (Status: ${err.response.status})`
      }
    }

    const errorData: ErrorDetails = {
      message: errorMessage,
      code: errorCode,
      timestamp: new Date(),
      details: errorDetails
    }

    // エラー状態を更新
    error.value = errorData
    isError.value = true

    // コンソールにログ出力（本番環境では無効化）
    if (logErrors && process.env.NODE_ENV !== 'production') {
      console.error('[Error Handler]', errorData)
    }

    return errorData
  }

  const clearError = () => {
    error.value = null
    isError.value = false
  }

  const setError = (message: string, code?: string) => {
    error.value = {
      message,
      code,
      timestamp: new Date()
    }
    isError.value = true
  }

  return {
    error,
    isError,
    handleError,
    clearError,
    setError
  }
}

// 共通エラーメッセージ
export const ERROR_MESSAGES = {
  NETWORK: 'ネットワークエラーが発生しました。接続を確認してください。',
  TIMEOUT: 'リクエストがタイムアウトしました。',
  SERVER: 'サーバーエラーが発生しました。しばらく待ってから再度お試しください。',
  NOT_FOUND: 'リソースが見つかりませんでした。',
  UNAUTHORIZED: '認証が必要です。',
  FORBIDDEN: 'アクセス権限がありません。',
  VALIDATION: '入力内容に誤りがあります。',
  UNKNOWN: '予期しないエラーが発生しました。'
} as const

// HTTPステータスコードに基づくエラーメッセージマッピング
export const getErrorMessageByStatus = (status: number): string => {
  if (status >= 500) return ERROR_MESSAGES.SERVER
  if (status === 404) return ERROR_MESSAGES.NOT_FOUND
  if (status === 401) return ERROR_MESSAGES.UNAUTHORIZED
  if (status === 403) return ERROR_MESSAGES.FORBIDDEN
  if (status === 422 || status === 400) return ERROR_MESSAGES.VALIDATION
  if (status === 408) return ERROR_MESSAGES.TIMEOUT
  return ERROR_MESSAGES.UNKNOWN
}
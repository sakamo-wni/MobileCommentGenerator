// 基本的な型定義のみ（使用はまだしない）
export interface GenerationResult {
  success: boolean
  location: string
  comment?: string
  error?: string
  metadata?: any
  weather?: any
  adviceComment?: string
}

export interface BatchResult {
  success: boolean
  location: string
  comment?: string
  error?: string
  metadata?: any
  weather?: any
  adviceComment?: string
}
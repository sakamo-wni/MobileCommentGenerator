export interface BatchResult {
  success: boolean;
  location: string;
  comment?: string | null;
  error?: string | null;
  metadata?: Record<string, unknown> | null;
  weather?: Record<string, unknown> | null;
  adviceComment?: string | null;
  advice_comment?: string | null; // For API compatibility
  loading?: boolean;
}

export interface GenerationResult {
  success: boolean;
  location: string;
  comment?: string | null;
  error?: string | null;
  metadata?: Record<string, unknown> | null;
  weather?: Record<string, unknown> | null;
  adviceComment?: string | null;
  advice_comment?: string | null; // For API compatibility
}
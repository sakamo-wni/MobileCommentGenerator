export interface BatchResult {
  success: boolean;
  location: string;
  comment?: string;
  error?: string;
  metadata?: Record<string, unknown>;
  weather?: Record<string, unknown>;
  adviceComment?: string;
}

export interface GenerationResult {
  success: boolean;
  location: string;
  comment?: string;
  error?: string;
  metadata?: Record<string, unknown>;
  weather?: Record<string, unknown>;
  adviceComment?: string;
}
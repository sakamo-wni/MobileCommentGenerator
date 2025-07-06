// Batch processing configuration
export const BATCH_CONFIG = {
  // Number of locations to process concurrently
  CONCURRENT_LIMIT: 3,
  // Timeout for each location request (milliseconds)
  REQUEST_TIMEOUT: 30000,
} as const;
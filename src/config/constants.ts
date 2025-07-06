// Batch processing configuration
export const BATCH_CONFIG = {
  // Number of locations to process concurrently
  CONCURRENT_LIMIT: 3,
  // Timeout for each location request (milliseconds)
  REQUEST_TIMEOUT: 120000, // 2 minutes
  // Warning threshold for batch size
  WARN_BATCH_LOCATIONS: 10,
} as const;
// Batch processing configuration
export const BATCH_CONFIG = {
  // Number of locations to process concurrently
  CONCURRENT_LIMIT: 3,
  // Timeout for each location request (milliseconds)
  REQUEST_TIMEOUT: 120000, // 2 minutes
  // Warning threshold for batch size
  WARN_BATCH_LOCATIONS: 20,
} as const;

// Location data configuration
export const LOCATION_CONFIG = {
  // 期待される地点数
  EXPECTED_COUNT: 142,
} as const;
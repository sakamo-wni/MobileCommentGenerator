/**
 * フロントエンドとバックエンドで共有する共通設定
 */

export interface CommonConfig {
  api: {
    /** APIタイムアウト（ミリ秒） */
    timeout: number;
    /** リトライ回数 */
    retryCount: number;
    /** リトライ間隔（ミリ秒） */
    retryDelay: number;
  };
  batch: {
    /** 同時処理数の上限 */
    concurrentLimit: number;
    /** バッチリクエストのタイムアウト（ミリ秒） */
    requestTimeout: number;
    /** バッチサイズの警告閾値 */
    warnBatchSize: number;
  };
  date: {
    /** 日付フォーマット */
    format: string;
    /** タイムゾーン */
    timezone: string;
    /** 時刻フォーマット */
    timeFormat: string;
  };
  weather: {
    /** 高温の閾値（℃） */
    highTempThreshold: number;
    /** 低温の閾値（℃） */
    lowTempThreshold: number;
    /** 強雨の閾値（mm/h） */
    heavyRainThreshold: number;
    /** 強風の閾値（m/s） */
    strongWindThreshold: number;
    /** 予報取得時間（時間） */
    forecastHours: number;
  };
  ui: {
    /** ページあたりの表示件数 */
    itemsPerPage: number;
    /** デバウンス時間（ミリ秒） */
    debounceDelay: number;
    /** トースト表示時間（ミリ秒） */
    toastDuration: number;
  };
}

/**
 * デフォルトの共通設定
 */
export const DEFAULT_COMMON_CONFIG: CommonConfig = {
  api: {
    timeout: 30000, // 30秒
    retryCount: 3,
    retryDelay: 1000, // 1秒
  },
  batch: {
    concurrentLimit: 3,
    requestTimeout: 120000, // 2分
    warnBatchSize: 20,
  },
  date: {
    format: 'YYYY-MM-DD',
    timezone: 'Asia/Tokyo',
    timeFormat: 'HH:mm',
  },
  weather: {
    highTempThreshold: 30.0,
    lowTempThreshold: 10.0,
    heavyRainThreshold: 30.0,
    strongWindThreshold: 15.0,
    forecastHours: 12,
  },
  ui: {
    itemsPerPage: 20,
    debounceDelay: 300,
    toastDuration: 3000,
  },
};

/**
 * 環境別の設定上書き（DeepPartialで部分的な上書きを許可）
 */
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export const ENV_CONFIG_OVERRIDES: Record<string, DeepPartial<CommonConfig>> = {
  production: {
    api: {
      timeout: 60000, // 本番環境では60秒
      retryCount: 5,
    },
    batch: {
      concurrentLimit: 5, // 本番環境では並列度を上げる
    },
  },
  development: {
    ui: {
      debounceDelay: 500, // 開発環境では少し長めに
    },
  },
};

/**
 * 環境に応じた設定を取得
 */
export function getCommonConfig(env: string = 'development'): CommonConfig {
  const baseConfig = { ...DEFAULT_COMMON_CONFIG };
  const envOverrides = ENV_CONFIG_OVERRIDES[env] || {};
  
  // Deep merge
  return deepMerge(baseConfig, envOverrides) as CommonConfig;
}

/**
 * 深いマージを行うヘルパー関数
 */
function deepMerge(target: any, source: any): any {
  const result = { ...target };
  
  for (const key in source) {
    if (source.hasOwnProperty(key)) {
      if (source[key] instanceof Object && key in target) {
        result[key] = deepMerge(target[key], source[key]);
      } else {
        result[key] = source[key];
      }
    }
  }
  
  return result;
}

/**
 * 設定値のバリデーション
 */
export function validateCommonConfig(config: Partial<CommonConfig>): string[] {
  const errors: string[] = [];
  
  // API設定の検証
  if (config.api) {
    if (config.api.timeout !== undefined && config.api.timeout < 1000) {
      errors.push('API timeout must be at least 1000ms');
    }
    if (config.api.retryCount !== undefined && config.api.retryCount < 0) {
      errors.push('Retry count must be non-negative');
    }
  }
  
  // バッチ設定の検証
  if (config.batch) {
    if (config.batch.concurrentLimit !== undefined && config.batch.concurrentLimit < 1) {
      errors.push('Concurrent limit must be at least 1');
    }
  }
  
  // 天気設定の検証
  if (config.weather) {
    if (config.weather.highTempThreshold !== undefined && 
        config.weather.lowTempThreshold !== undefined &&
        config.weather.highTempThreshold <= config.weather.lowTempThreshold) {
      errors.push('High temperature threshold must be greater than low temperature threshold');
    }
  }
  
  return errors;
}
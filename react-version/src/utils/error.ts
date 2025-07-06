/**
 * エラーハンドリングのユーティリティ関数
 */

export interface ErrorDetails {
  error: unknown;
  context?: string;
}

/**
 * エラーからユーザーフレンドリーなメッセージを生成
 */
export function getErrorMessage(details: ErrorDetails): string {
  const { error, context } = details;
  
  if (!error) {
    return context ? `${context}で不明なエラーが発生しました` : '不明なエラーが発生しました';
  }
  
  // AbortErrorの場合（タイムアウト）
  if (error instanceof Error && error.name === 'AbortError') {
    return context ? `${context}がタイムアウトしました` : 'リクエストがタイムアウトしました';
  }
  
  // ネットワークエラー
  if (error instanceof Error && error.message.includes('fetch')) {
    return 'ネットワークエラーが発生しました。接続を確認してください';
  }
  
  // APIエラー
  if (typeof error === 'object' && error !== null && 'statusCode' in error) {
    const statusCode = (error as { statusCode: number }).statusCode;
    switch (statusCode) {
      case 400:
        return 'リクエストが不正です';
      case 401:
        return '認証エラーです';
      case 403:
        return 'アクセス権限がありません';
      case 404:
        return 'リソースが見つかりません';
      case 429:
        return 'リクエスト数が制限を超えました。しばらく待ってから再試行してください';
      case 500:
        return 'サーバーエラーが発生しました';
      case 502:
      case 503:
      case 504:
        return 'サーバーが一時的に利用できません';
      default:
        return `エラーが発生しました (${statusCode})`;
    }
  }
  
  // 一般的なErrorオブジェクト
  if (error instanceof Error && error.message) {
    return error.message;
  }
  
  // その他
  return context ? `${context}で予期しないエラーが発生しました` : '予期しないエラーが発生しました';
}

/**
 * エラーをコンソールにログ出力
 */
export function logError(error: unknown, context?: string): void {
  const timestamp = new Date().toISOString();
  console.error(`[${timestamp}]${context ? ` ${context}:` : ''}`, error);
}
/**
 * 日付フォーマットのユーティリティ関数
 */

/**
 * 日付を日本語のローカル形式でフォーマット
 * @param dateInput - フォーマットする日付（string | Date | number | undefined | null）
 * @returns フォーマットされた日付文字列（エラー時は「不明」）
 */
export function formatDateTime(dateInput: string | Date | number | undefined | null): string {
  if (!dateInput) return '不明';
  
  try {
    // 日付オブジェクトに変換
    let date: Date;
    
    if (typeof dateInput === 'string') {
      // ISO 8601形式の文字列を直接パース
      date = new Date(dateInput);
    } else if (dateInput instanceof Date) {
      date = dateInput;
    } else {
      // 数値（timestamp）の場合
      date = new Date(dateInput);
    }
    
    // 有効な日付か確認
    if (Number.isNaN(date.getTime())) {
      return '不明';
    }
    
    // 日本のローカル形式でフォーマット
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Tokyo'
    });
  } catch (error) {
    console.error('Date parsing error:', error);
    return '不明';
  }
}
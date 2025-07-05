"""
天気予報関連の定数定義

気象学的根拠に基づく温度閾値や判定基準を定義
"""

# 温度差閾値設定（気象学的根拠に基づく）
TEMP_DIFF_THRESHOLD_PREVIOUS_DAY = 5.0  # 前日比5℃: 人体が明確に体感できる温度差
TEMP_DIFF_THRESHOLD_12HOURS = 3.0  # 12時間前比3℃: 体調管理に影響する可能性がある基準値
DAILY_TEMP_RANGE_THRESHOLD_LARGE = 15.0  # 日較差15℃: 健康影響リスクが高まる閾値
DAILY_TEMP_RANGE_THRESHOLD_MEDIUM = 10.0  # 日較差10℃: 注意が必要な閾値

# 温度分類の閾値（気象庁の基準に基づく）
TEMP_THRESHOLD_HOT = 30.0  # 真夏日の基準
TEMP_THRESHOLD_WARM = 25.0  # 夏日の基準
TEMP_THRESHOLD_COOL = 10.0  # 肌寒く感じる温度
TEMP_THRESHOLD_COLD = 5.0  # 冬日に近い温度

# API設定のデフォルト値
DEFAULT_API_TIMEOUT = 30  # APIタイムアウト（秒）
DEFAULT_MAX_RETRIES = 3  # 最大リトライ回数
DEFAULT_RATE_LIMIT_DELAY = 0.1  # レート制限回避遅延（秒）
DEFAULT_CACHE_TTL = 300  # キャッシュTTL（5分）

# 予報設定のデフォルト値
DEFAULT_FORECAST_HOURS = 24  # デフォルト予報時間数
DEFAULT_FORECAST_HOURS_AHEAD = 0  # 現在時刻から予報を取得
MAX_FORECAST_HOURS = 168  # 最大予報時間（7日間）

# キャッシュ設定
DEFAULT_FORECAST_CACHE_RETENTION_DAYS = 7  # 予報キャッシュ保持日数

# 検証用の制限値
MAX_API_TIMEOUT = 300  # 最大APIタイムアウト（5分）

# ログレベルの有効な値
VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
"""天気関連の定数定義"""

# 気温閾値 (°C)
class TemperatureThresholds:
    """気温閾値の定数"""
    HOT_WEATHER = 30.0          # 暑い天気の閾値
    WARM_WEATHER = 25.0         # 暖かい天気の閾値
    COOL_WEATHER = 10.0         # 涼しい天気の閾値
    COLD_WEATHER = 5.0          # 寒い天気の閾値
    COLD_COMMENT_THRESHOLD = 12.0  # 寒さコメントの閾値
    
    # 気温差の閾値
    SIGNIFICANT_DAILY_DIFF = 5.0     # 前日との有意な気温差
    HOURLY_SIGNIFICANT_DIFF = 3.0    # 12時間での有意な気温差
    LARGE_DAILY_RANGE = 15.0         # 大きな日較差
    MEDIUM_DAILY_RANGE = 10.0        # 中程度の日較差

# 湿度閾値 (%)
class HumidityThresholds:
    """湿度閾値の定数"""
    HIGH_HUMIDITY = 80.0        # 高湿度の閾値
    LOW_HUMIDITY = 30.0         # 低湿度の閾値
    VERY_HIGH_HUMIDITY = 90.0   # 非常に高い湿度
    VERY_LOW_HUMIDITY = 20.0    # 非常に低い湿度

# 降水量閾値 (mm)
class PrecipitationThresholds:
    """降水量閾値の定数"""
    LIGHT_RAIN = 1.0            # 小雨の閾値
    MODERATE_RAIN = 5.0         # 中雨の閾値
    HEAVY_RAIN = 10.0           # 大雨の閾値
    VERY_HEAVY_RAIN = 30.0      # 激しい雨の閾値
    THUNDER_STRONG_THRESHOLD = 5.0  # 雷雨強弱判定の閾値

# 風速閾値 (m/s)
class WindSpeedThresholds:
    """風速閾値の定数"""
    LIGHT_BREEZE = 3.0          # 軽い風
    MODERATE_BREEZE = 7.0       # 中程度の風
    STRONG_BREEZE = 12.0        # 強い風
    GALE = 20.0                 # 強風

# データ検証の範囲
class DataValidationRanges:
    """データ検証用の値域"""
    MIN_TEMPERATURE = -50.0     # 最低気温
    MAX_TEMPERATURE = 60.0      # 最高気温
    MIN_HUMIDITY = 0.0          # 最低湿度
    MAX_HUMIDITY = 100.0        # 最高湿度
    MIN_WIND_SPEED = 0.0        # 最低風速
    MAX_WIND_SPEED = 200.0      # 最高風速（台風含む）
    MIN_PRECIPITATION = 0.0     # 最低降水量
    MAX_PRECIPITATION = 500.0   # 最高降水量（極端な場合）
    MIN_WIND_DIRECTION = 0.0    # 最小風向
    MAX_WIND_DIRECTION = 360.0  # 最大風向

# システム設定の定数
class SystemConstants:
    """システム設定の定数"""
    DEFAULT_COMMENT_LIMIT = 15          # デフォルトコメント文字数制限
    MAX_COMMENTS_PER_SEASON = 20        # 季節あたりの最大コメント数
    SEASONAL_CACHE_LIMIT = 3            # 季節別キャッシュの最大保持数
    DEFAULT_RECENT_COMMENTS_LIMIT = 100 # デフォルト最近コメント取得数
    
    # API設定
    DEFAULT_API_TIMEOUT = 30.0          # デフォルトAPIタイムアウト (秒)
    MAX_API_RETRIES = 3                 # API最大リトライ回数
    FORECAST_HOURS = 24                 # 予報時間 (時間)
    MAX_FORECAST_HOURS = 168            # 最大予報時間 (7日)
    CACHE_TTL = 300                     # キャッシュTTL (秒)
    FORECAST_CACHE_DAYS = 7             # 予報キャッシュ保持日数

# 文字列制限
class StringLimits:
    """文字列長の制限"""
    MAX_COMMENT_LENGTH = 50             # 最大コメント長
    WARNING_COMMENT_LENGTH = 15         # コメント長警告閾値
    MAX_LOCATION_NAME_LENGTH = 20       # 最大地点名長
    MAX_ERROR_MESSAGE_LENGTH = 200      # 最大エラーメッセージ長

# 温度関連の警告閾値
HEATSTROKE_WARNING_TEMP = 34.0  # 熱中症警戒開始温度
HEATSTROKE_SEVERE_TEMP = 35.0   # 熱中症厳重警戒温度
COLD_WARNING_TEMP = 15.0        # 防寒対策が不要になる温度

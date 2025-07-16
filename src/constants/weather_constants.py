"""Weather-related constants.

このモジュールは天気関連の定数を定義します。
関連する定数はクラスでグループ化されており、保守性と可読性を向上させています。
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TemperatureThresholds:
    """温度に関する閾値定数
    
    Attributes:
        MIN: 最低温度 (-50°C) - システムで扱える最低温度
        MAX: 最高温度 (60°C) - システムで扱える最高温度
        COMFORTABLE_MIN: 快適温度の下限 (10°C)
        COMFORTABLE_MAX: 快適温度の上限 (30°C)
        HEATSTROKE: 熱中症警戒温度 (35°C) - この温度以上で熱中症注意コメントを表示
    """
    MIN: float = -50.0
    MAX: float = 60.0
    COMFORTABLE_MIN: float = 10.0
    COMFORTABLE_MAX: float = 30.0
    HEATSTROKE: float = 35.0


@dataclass(frozen=True)
class HumidityThresholds:
    """湿度に関する閾値定数
    
    Attributes:
        MIN: 最低湿度 (0%)
        MAX: 最高湿度 (100%)
    """
    MIN: float = 0.0
    MAX: float = 100.0


@dataclass(frozen=True)
class WindThresholds:
    """風速に関する閾値定数
    
    Attributes:
        MIN: 最低風速 (0 m/s)
        MAX: 最高風速 (200 m/s) - 理論的な上限値
        STRONG: 強風判定閾値 (15 m/s) - この値以上で強風注意
        DIRECTION_MIN: 風向の最小値 (0度)
        DIRECTION_MAX: 風向の最大値 (360度)
    """
    MIN: float = 0.0
    MAX: float = 200.0
    STRONG: float = 15.0
    DIRECTION_MIN: int = 0
    DIRECTION_MAX: int = 360


@dataclass(frozen=True)
class PrecipitationThresholds:
    """降水量に関する閾値定数 (mm/h)
    
    Attributes:
        NONE: 降水なし判定値 (0.5mm)
        LIGHT: 小雨判定値 (0.1mm) - にわか雨の可能性
        LIGHT_RAIN: 軽い雨判定値 (2.0mm) - 傘の用意推奨
        MODERATE: 中程度の雨判定値 (5.0mm)
        HEAVY: 大雨判定値 (10.0mm) - 傘必須
        VERY_HEAVY: 非常に激しい雨判定値 (30.0mm) - 外出注意
    """
    NONE: float = 0.5
    LIGHT: float = 0.1
    LIGHT_RAIN: float = 2.0
    MODERATE: float = 5.0
    HEAVY: float = 10.0
    VERY_HEAVY: float = 30.0


@dataclass(frozen=True)
class CloudCoverageThresholds:
    """雲量に関する閾値定数 (%)
    
    Attributes:
        CLEAR: 快晴判定値 (20%)
        PARTLY_CLOUDY: 部分曇り判定値 (60%)
    """
    CLEAR: int = 20
    PARTLY_CLOUDY: int = 60


@dataclass(frozen=True)
class CommentGenerationConstants:
    """コメント生成に関する定数
    
    Attributes:
        MAX_LENGTH: コメントの最大文字数 (15文字) - 日本語での簡潔な表現に適した長さ
        CANDIDATE_LIMIT: LLMに渡す候補数 (10件) - 十分な選択肢を確保
        CONTINUOUS_RAIN_HOURS: 連続雨判定時間 (4時間) - にわか雨除外の基準
    """
    MAX_LENGTH: int = 15
    CANDIDATE_LIMIT: int = 10
    CONTINUOUS_RAIN_HOURS: int = 4


# インスタンスを作成（後方互換性のため）
TEMP = TemperatureThresholds()
HUMIDITY = HumidityThresholds()
WIND = WindThresholds()
PRECIP = PrecipitationThresholds()
CLOUD = CloudCoverageThresholds()
COMMENT = CommentGenerationConstants()

# 特殊な定数
SPECIAL_WEATHER_PRIORITY_THRESHOLD = 4  # 特別な天気の優先度閾値

# 後方互換性のためのエイリアス（非推奨）
# これらは将来のバージョンで削除予定
TEMPERATURE_MIN = TEMP.MIN
TEMPERATURE_MAX = TEMP.MAX
TEMPERATURE_COMFORTABLE_MIN = TEMP.COMFORTABLE_MIN
TEMPERATURE_COMFORTABLE_MAX = TEMP.COMFORTABLE_MAX
HEATSTROKE_THRESHOLD_TEMP = TEMP.HEATSTROKE

HUMIDITY_MIN = HUMIDITY.MIN
HUMIDITY_MAX = HUMIDITY.MAX

WIND_SPEED_MIN = WIND.MIN
WIND_SPEED_MAX = WIND.MAX
WIND_SPEED_THRESHOLD_STRONG = WIND.STRONG
WIND_DIRECTION_MIN_DEGREES = WIND.DIRECTION_MIN
WIND_DIRECTION_MAX_DEGREES = WIND.DIRECTION_MAX

PRECIPITATION_THRESHOLD_NONE = PRECIP.NONE
PRECIPITATION_THRESHOLD_LIGHT = PRECIP.LIGHT
PRECIPITATION_THRESHOLD_LIGHT_RAIN = PRECIP.LIGHT_RAIN
PRECIPITATION_THRESHOLD_MODERATE = PRECIP.MODERATE
PRECIPITATION_THRESHOLD_HEAVY = PRECIP.HEAVY
PRECIPITATION_THRESHOLD_VERY_HEAVY = PRECIP.VERY_HEAVY

CLEAR_WEATHER_CLOUD_COVERAGE_MAX = CLOUD.CLEAR
PARTLY_CLOUDY_CLOUD_COVERAGE_MAX = CLOUD.PARTLY_CLOUDY

COMMENT_MAX_LENGTH = COMMENT.MAX_LENGTH
COMMENT_CANDIDATE_LIMIT = COMMENT.CANDIDATE_LIMIT
CONTINUOUS_RAIN_THRESHOLD_HOURS = COMMENT.CONTINUOUS_RAIN_HOURS
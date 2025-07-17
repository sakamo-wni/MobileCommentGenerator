"""コメント安全性チェック機能"""

from .weather_consistency import WeatherConsistencyChecker
from .seasonal_appropriateness import SeasonalAppropriatenessChecker
from .rain_context import RainContextChecker
from .alternative_finder import AlternativeCommentFinder
from .types import CheckResult
from .constants import (
    CHANGEABLE_WEATHER_PATTERNS,
    SUNNY_KEYWORDS,
    SUNNY_WEATHER_DESCRIPTIONS,
    SHOWER_RAIN_PATTERNS,
    RAIN_ADVICE_PATTERNS,
    STORM_WEATHER_PATTERNS,
    PRECIPITATION_THRESHOLD_SUNNY,
    PRECIPITATION_THRESHOLD_RAIN,
    RAIN_INAPPROPRIATE_SUNNY,
    RAIN_INAPPROPRIATE_CLOUDY,
    SUNNY_INAPPROPRIATE_RAIN,
    SUNNY_INAPPROPRIATE_CLOUDY,
    CLOUDY_INAPPROPRIATE_SUN
)

__all__ = [
    # チェッカークラス
    'WeatherConsistencyChecker',
    'SeasonalAppropriatenessChecker', 
    'RainContextChecker',
    'AlternativeCommentFinder',
    # 型定義
    'CheckResult',
    # 定数
    'CHANGEABLE_WEATHER_PATTERNS',
    'SUNNY_KEYWORDS',
    'SUNNY_WEATHER_DESCRIPTIONS',
    'SHOWER_RAIN_PATTERNS',
    'RAIN_ADVICE_PATTERNS',
    'STORM_WEATHER_PATTERNS',
    'PRECIPITATION_THRESHOLD_SUNNY',
    'PRECIPITATION_THRESHOLD_RAIN',
    'RAIN_INAPPROPRIATE_SUNNY',
    'RAIN_INAPPROPRIATE_CLOUDY',
    'SUNNY_INAPPROPRIATE_RAIN',
    'SUNNY_INAPPROPRIATE_CLOUDY',
    'CLOUDY_INAPPROPRIATE_SUN'
]
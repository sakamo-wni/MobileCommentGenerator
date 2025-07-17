"""天気の一貫性チェックモジュール"""

from __future__ import annotations
import logging
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState
from .types import CheckResult
from .constants import (
    CHANGEABLE_WEATHER_PATTERNS,
    SUNNY_KEYWORDS,
    SUNNY_WEATHER_DESCRIPTIONS,
    PRECIPITATION_THRESHOLD_SUNNY
)

logger = logging.getLogger(__name__)

# 雨天に不適切な表現
RAIN_INAPPROPRIATE_SUNNY = ["晴れ", "快晴", "日差し", "太陽", "青空", "陽射し", "日向", "晴天"]
RAIN_INAPPROPRIATE_CLOUDY = ["雲が優勢", "雲が多", "どんより", "雲が厚", "曇り空", "グレーの空", "雲に覆われ", "穏やかな空"]

# 晴天に不適切な表現
SUNNY_INAPPROPRIATE_RAIN = ["雨", "雷雨", "降水", "傘", "濡れ", "豪雨", "にわか雨", "大雨", "激しい雨", "本格的な雨"]
SUNNY_INAPPROPRIATE_CLOUDY = ["雲が優勢", "雲が多", "どんより", "雲が厚", "曇り空", "グレーの空", "雲に覆われ"]

# 曇天に不適切な表現
CLOUDY_INAPPROPRIATE_SUN = ["強い日差し", "眩しい", "太陽がギラギラ", "日光が強", "日差しジリジリ", "照りつける", "燦々"]


class WeatherConsistencyChecker:
    """天気と表現の一貫性をチェックするクラス"""
    
    def check_sunny_weather_consistency(
        self, 
        weather_data: WeatherForecast, 
        weather_comment: str
    ) -> CheckResult:
        """晴天時の表現の一貫性をチェック"""
        if not any(sunny in weather_data.weather_description for sunny in SUNNY_WEATHER_DESCRIPTIONS):
            return CheckResult(False, "", [])
        
        if not weather_comment:
            return CheckResult(False, "", [])
        
        # 変わりやすい空表現チェック
        for pattern in CHANGEABLE_WEATHER_PATTERNS:
            if pattern in weather_comment:
                logger.warning(f"🚨 晴天時に「{pattern}」は不適切")
                return CheckResult(True, pattern, CHANGEABLE_WEATHER_PATTERNS)
        
        # 雨表現チェック（降水量も考慮）
        if weather_data.precipitation < PRECIPITATION_THRESHOLD_SUNNY:
            for pattern in SUNNY_INAPPROPRIATE_RAIN:
                if pattern in weather_comment:
                    logger.warning(f"🚨 晴天時に雨表現「{pattern}」は不適切")
                    return CheckResult(True, pattern, SUNNY_INAPPROPRIATE_RAIN)
        
        # 曇り表現チェック
        for pattern in SUNNY_INAPPROPRIATE_CLOUDY:
            if pattern in weather_comment:
                logger.warning(f"🚨 晴天時に曇り表現「{pattern}」は不適切")
                return CheckResult(True, pattern, SUNNY_INAPPROPRIATE_CLOUDY)
        
        return CheckResult(False, "", [])
    
    def check_rainy_weather_consistency(
        self, 
        weather_data: WeatherForecast, 
        weather_comment: str,
        advice_comment: str
    ) -> CheckResult:
        """雨天時の表現の一貫性をチェック"""
        if "雨" not in weather_data.weather_description:
            return CheckResult(False, "", [])
        
        if not weather_comment:
            return CheckResult(False, "", [])
        
        # 晴天表現チェック
        for pattern in RAIN_INAPPROPRIATE_SUNNY:
            if pattern in weather_comment:
                logger.warning(f"🚨 雨天時に晴天表現「{pattern}」は不適切")
                return CheckResult(True, pattern, RAIN_INAPPROPRIATE_SUNNY)
        
        # 曇り表現チェック
        for pattern in RAIN_INAPPROPRIATE_CLOUDY:
            if pattern in weather_comment:
                logger.warning(f"🚨 雨天時に曇り表現「{pattern}」は不適切")
                return CheckResult(True, pattern, RAIN_INAPPROPRIATE_CLOUDY)
        
        # 雨天で熱中症警告チェック
        if advice_comment and weather_data.temperature < 30.0 and "熱中症" in advice_comment:
            logger.warning(f"🚨 雨天+低温で熱中症警告は不適切")
            return CheckResult(True, "熱中症", ["熱中症"])
        
        # 大雨・嵐でムシムシチェック
        if ("大雨" in weather_data.weather_description or "嵐" in weather_data.weather_description) and "ムシムシ" in weather_comment:
            logger.warning(f"🚨 悪天候でムシムシコメントは不適切")
            return CheckResult(True, "ムシムシ", ["ムシムシ"])
        
        return CheckResult(False, "", [])
    
    def check_cloudy_weather_consistency(
        self, 
        weather_data: WeatherForecast, 
        weather_comment: str
    ) -> CheckResult:
        """曇天時の表現の一貫性をチェック"""
        if not any(cloud in weather_data.weather_description for cloud in ["曇", "くもり", "うすぐもり"]):
            return CheckResult(False, "", [])
        
        if not weather_comment:
            return CheckResult(False, "", [])
        
        # 強い日差し表現チェック
        for pattern in CLOUDY_INAPPROPRIATE_SUN:
            if pattern in weather_comment:
                logger.warning(f"🚨 曇天時に強い日差し表現「{pattern}」は不適切")
                return CheckResult(True, pattern, CLOUDY_INAPPROPRIATE_SUN)
        
        return CheckResult(False, "", [])
    
    def check_weather_stability(
        self,
        weather_comment: str,
        state: CommentGenerationState
    ) -> CheckResult:
        """天気の安定性と表現の一貫性をチェック"""
        if not state or not hasattr(state, 'generation_metadata') or not weather_comment:
            return CheckResult(False, "", [])
        
        period_forecasts = state.generation_metadata.get('period_forecasts', [])
        if len(period_forecasts) < 4:
            return CheckResult(False, "", [])
        
        # 全て同じ天気条件かチェック
        weather_conditions = [f.weather_description for f in period_forecasts if hasattr(f, 'weather_description')]
        if len(set(weather_conditions)) == 1:  # 全て同じ天気
            changeable_patterns = ["変わりやすい", "天気急変", "不安定", "変化", "急変", "めまぐるしく"]
            for pattern in changeable_patterns:
                if pattern in weather_comment:
                    logger.warning(f"🚨 安定した天気で「{pattern}」は不適切")
                    return CheckResult(True, pattern, changeable_patterns)
        
        return CheckResult(False, "", [])
"""雨天コンテキストチェックモジュール"""

from __future__ import annotations
import logging
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import PastComment, CommentType
from src.constants.weather_constants import COMMENT
from .types import CheckResult
from .constants import (
    SHOWER_RAIN_PATTERNS,
    RAIN_ADVICE_PATTERNS,
    STORM_WEATHER_PATTERNS,
    PRECIPITATION_THRESHOLD_RAIN
)

logger = logging.getLogger(__name__)


class RainContextChecker:
    """雨天関連のコンテキストをチェックするクラス"""
    
    def check_continuous_rain_context(
        self,
        weather_comment: str,
        state: CommentGenerationState
    ) -> CheckResult:
        """連続雨時のコンテキストをチェック"""
        if not weather_comment or not self._check_continuous_rain(state):
            return CheckResult(False, "", [])
        
        # 連続雨時に「にわか雨」表現は不適切
        for pattern in SHOWER_RAIN_PATTERNS:
            if pattern in weather_comment:
                logger.warning(f"🚨 連続雨時に「{pattern}」は不適切")
                return CheckResult(True, pattern, SHOWER_RAIN_PATTERNS)
        
        return CheckResult(False, "", [])
    
    def _check_continuous_rain(self, state: CommentGenerationState) -> bool:
        """連続雨かどうかをチェック"""
        if not state or not hasattr(state, 'generation_metadata') or not state.generation_metadata:
            return False
            
        period_forecasts = state.generation_metadata.get('period_forecasts', [])
        if not period_forecasts:
            return False
        
        # 天気が「雨」または降水量が0.1mm以上の時間をカウント
        rain_hours = 0
        for f in period_forecasts:
            if hasattr(f, 'weather') and '雨' in str(f.weather):
                rain_hours += 1
            elif hasattr(f, 'weather_description') and '雨' in f.weather_description:
                rain_hours += 1
            elif hasattr(f, 'precipitation') and f.precipitation >= PRECIPITATION_THRESHOLD_RAIN:
                rain_hours += 1
        
        is_continuous_rain = rain_hours >= COMMENT.CONTINUOUS_RAIN_HOURS
        
        if is_continuous_rain:
            logger.info(f"🚨 連続雨を検出: {rain_hours}時間の雨（CONTINUOUS_RAIN_HOURS={COMMENT.CONTINUOUS_RAIN_HOURS}）")
            # デバッグ情報
            for f in period_forecasts[:5]:  # 最初の5件のみログ出力
                if hasattr(f, 'datetime'):
                    time_str = f.datetime.strftime('%H時')
                    weather = getattr(f, 'weather', getattr(f, 'weather_description', '不明'))
                    precip = getattr(f, 'precipitation', 0)
                    logger.debug(f"  {time_str}: {weather}, 降水量{precip}mm")
        
        return is_continuous_rain
    
    def is_rain_advice_appropriate(self, advice_comment: str) -> bool:
        """アドバイスが雨天に適しているかチェック"""
        if not advice_comment:
            return False
        
        return any(pattern in advice_comment for pattern in RAIN_ADVICE_PATTERNS)
    
    def is_storm_weather_comment(self, weather_comment: str) -> bool:
        """悪天候コメントかどうかチェック"""
        if not weather_comment:
            return False
        
        return any(pattern in weather_comment for pattern in STORM_WEATHER_PATTERNS)
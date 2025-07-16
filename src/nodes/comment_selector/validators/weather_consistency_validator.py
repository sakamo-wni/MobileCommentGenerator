"""天気の一貫性チェックバリデーター"""

import logging
from typing import Any

from src.config.config import get_weather_constants
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState
from src.utils.weather_classifier import classify_weather_type, count_weather_type_changes

logger = logging.getLogger(__name__)

# 定数を取得
WEATHER_CHANGE_THRESHOLD = get_weather_constants().WEATHER_CHANGE_THRESHOLD


class WeatherConsistencyValidator:
    """天気の一貫性関連のバリデーション"""
    
    def is_sunny_weather_with_changeable_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """晴れの天気なのに変わりやすい天気のコメントが含まれているか判定"""
        # 晴れの天気かチェック
        description = weather_data.weather_description.lower()
        if not any(word in description for word in ["晴", "快晴", "sunny", "clear", "fine"]):
            return False
        
        # 0mm降水の晴れであることを確認
        has_rain = any(h.precipitation > 0 for h in weather_data.hourly_forecasts)
        if has_rain:
            return False
        
        # 変わりやすい天気のパターン
        changeable_patterns = [
            "変わりやすい", "不安定", "変化", "急な雨", "急変",
            "天気の急変", "変わり", "一時的", "ところにより",
            "崩れ", "下り坂"
        ]
        
        comment_lower = comment_text.lower()
        return any(pattern in comment_lower for pattern in changeable_patterns)
    
    def is_cloudy_weather_with_sunshine_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """曇りの天気なのに日差しが強いコメントが含まれているか判定"""
        # 曇りの天気かチェック
        description = weather_data.weather_description.lower()
        if not any(word in description for word in ["曇", "くもり", "cloudy", "overcast"]):
            return False
        
        # 日差しに関するパターン
        sunshine_patterns = [
            "日差しが強", "紫外線が強", "日焼け", "強い日差し",
            "カンカン照り", "炎天下", "日中の日差し",
            "まぶしい", "ギラギラ", "照りつけ"
        ]
        
        comment_lower = comment_text.lower()
        return any(pattern in comment_lower for pattern in sunshine_patterns)
    
    def is_no_rain_weather_with_rain_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """雨が降らない天気なのに雨具や雨対策のコメントが含まれているか判定"""
        # 降水量をチェック
        max_precipitation = max((h.precipitation for h in weather_data.hourly_forecasts), default=0)
        
        # 降水量が0.5mm未満の場合のみチェック
        if max_precipitation >= 0.5:
            return False
        
        # 雨具・雨対策のパターン
        rain_patterns = [
            "傘", "レインコート", "雨具", "雨対策",
            "濡れ", "雨に備え", "雨の心配", "雨が降り",
            "にわか雨", "通り雨", "雨脚", "本降り"
        ]
        
        return any(pattern in comment_text for pattern in rain_patterns)
    
    def is_stable_weather_with_unstable_comment(self, comment_text: str, weather_data: WeatherForecast, state: CommentGenerationState | None = None) -> bool:
        """安定した天気なのに不安定なコメントが含まれているか判定"""
        # 現在の天気が本当に安定しているかチェック
        is_stable = self._check_full_day_stability(weather_data, state)
        
        if not is_stable:
            return False
        
        # 不安定な天気を示唆するパターン
        unstable_patterns = [
            "変わりやすい", "不安定", "急変", "急な雨",
            "にわか雨", "通り雨", "一時的", "ところにより",
            "崩れ", "下り坂", "悪化", "荒れ", "大荒れ"
        ]
        
        return any(pattern in comment_text for pattern in unstable_patterns)
    
    def _check_full_day_stability(self, weather_data: WeatherForecast, state: CommentGenerationState | None = None) -> bool:
        """24時間の天気が安定しているかチェック"""
        # 当日の安定性チェック
        max_precipitation = max((h.precipitation for h in weather_data.hourly_forecasts), default=0)
        if max_precipitation > 0.5:
            return False
        
        # 時間ごとの天気タイプ
        weather_types = [classify_weather_type(h) for h in weather_data.hourly_forecasts]
        unique_types = set(weather_types)
        type_changes = count_weather_type_changes(weather_types)
        
        # 単一天気タイプまたは変化が少ない
        if len(unique_types) == 1 or type_changes <= 1:
            # 翌日の予報も確認
            next_day_forecasts = self._extract_next_day_forecasts(state)
            
            if next_day_forecasts:
                weather_type = list(unique_types)[0] if unique_types else 'unknown'
                return self._check_single_weather_type_stability(weather_type, next_day_forecasts)
            
            return True
        
        return False
    
    def _extract_next_day_forecasts(self, state: CommentGenerationState | None) -> list[WeatherForecast]:
        """翌日の天気予報を抽出"""
        if not state or not hasattr(state, "weather_history") or not state.weather_history:
            return []
        
        next_day_forecasts = []
        
        # weather_historyから翌日のデータを探す
        for entry in state.weather_history:
            if not entry:
                continue
                
            # entryがWeatherForecastの場合
            if hasattr(entry, "hourly_forecasts"):
                # 翌日のデータかチェック（簡易的に）
                if entry != state.weather_data:
                    next_day_forecasts.append(entry)
                continue
            
            # entryが辞書の場合
            if isinstance(entry, dict):
                weather_info = entry.get("weather_info") or entry.get("weather_data")
                if weather_info and hasattr(weather_info, "hourly_forecasts"):
                    if weather_info != state.weather_data:
                        next_day_forecasts.append(weather_info)
        
        return next_day_forecasts[:1]  # 最初の1日分のみ
    
    def _check_single_weather_type_stability(self, weather_type: str, next_day_forecasts: list[WeatherForecast]) -> bool:
        """単一天気タイプの安定性をチェック"""
        if weather_type not in ['sunny', 'cloudy']:
            return False
        
        for forecast in next_day_forecasts:
            next_types = [classify_weather_type(h) for h in forecast.hourly_forecasts[:12]]  # 翌日の午前中
            
            # 翌日も同じ天気タイプが継続
            if all(t == weather_type for t in next_types):
                return True
            
            # 晴れ/曇りの組み合わせは許容
            if weather_type in ['sunny', 'cloudy'] and all(t in ['sunny', 'cloudy'] for t in next_types):
                return True
        
        return False
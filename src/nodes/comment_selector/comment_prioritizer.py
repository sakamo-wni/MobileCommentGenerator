"""コメントの優先順位付け機能"""

from __future__ import annotations
import logging
from typing import Any
from dataclasses import dataclass

from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast
from src.config.config_loader import load_config

logger = logging.getLogger(__name__)

# 設定ファイルから閾値を読み込み
_weather_config = load_config('weather_thresholds', validate=False)
EXTREME_HEAT_THRESHOLD = _weather_config.get('temperature', {}).get('extreme_heat_threshold', 35.0)

# 雨判定の閾値
RAIN_THRESHOLD = 0.5  # 0.5mm/h以上を雨として扱う


@dataclass
class PrioritizedComments:
    """優先順位付けされたコメントのコンテナ"""
    severe_matched: list[dict[str, Any]]
    weather_matched: list[dict[str, Any]]
    others: list[dict[str, Any]]


class CommentPrioritizer:
    """コメントの優先順位付けを行うクラス"""
    
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        """設定を読み込み"""
        try:
            config = load_config('weather_thresholds', validate=False)
            self.limit = config.get('generation', {}).get('weather_candidates_limit', 100)
            
            # 候補比率を取得
            ratios = config.get('generation', {}).get('candidate_ratios', {})
            self.severe_ratio = ratios.get('severe_weather', 0.4)
            self.weather_ratio = ratios.get('weather_matched', 0.4)
            self.others_ratio = ratios.get('others', 0.2)
        except Exception as e:
            logger.debug(f"設定ファイル読み込みエラー: {e}")
            # デフォルト値
            self.limit = 100
            self.severe_ratio, self.weather_ratio, self.others_ratio = 0.4, 0.4, 0.2
    
    def prioritize_comment(
        self,
        comment: PastComment,
        weather_data: WeatherForecast,
        has_rain_in_timeline: bool,
        max_temp_in_timeline: float,
        comment_validator: Any
    ) -> str | None:
        """コメントの優先度カテゴリを判定
        
        Returns:
            'severe', 'weather_matched', 'others', またはNone（除外）
        """
        # 1. 雨天時の最優先処理
        is_raining = weather_data.precipitation >= RAIN_THRESHOLD or (
            has_rain_in_timeline and 
            any(word in weather_data.weather_description.lower() for word in ["雨", "rain", "shower"])
        )
        
        if is_raining:
            rain_keywords = ["雨", "傘", "濡れ", "降水", "にわか雨", "雷雨"]
            if any(keyword in comment.comment_text for keyword in rain_keywords):
                logger.info(f"雨天時のコメントを最優先に: '{comment.comment_text}' "
                          f"(現在降水量: {weather_data.precipitation}mm, 時系列に雨: {has_rain_in_timeline})")
                return 'severe'
        
        # 2. 高温時の最優先処理
        if weather_data.temperature >= EXTREME_HEAT_THRESHOLD or max_temp_in_timeline >= EXTREME_HEAT_THRESHOLD:
            heat_keywords = ["熱中症", "水分補給", "涼しい", "冷房", "暑さ対策", "猛暑", "高温"]
            if any(keyword in comment.comment_text for keyword in heat_keywords):
                logger.debug(f"高温時（最高{max_temp_in_timeline}℃）のコメントを最優先に: '{comment.comment_text}'")
                return 'severe'
        
        # 3. 通常の悪天候時の処理
        from src.config.config import get_severe_weather_config
        severe_config = get_severe_weather_config()
        
        if severe_config.is_severe_weather(weather_data.weather_condition):
            if comment_validator.is_severe_weather_appropriate(comment.comment_text, weather_data):
                return 'severe'
            elif comment_validator.is_weather_matched(comment.weather_condition, weather_data.weather_description):
                return 'weather_matched'
            else:
                return 'others'
        else:
            # 晴天時に雨のコメントを除外
            if "晴" in weather_data.weather_description and weather_data.precipitation < 0.1:
                rain_keywords = ["雨", "雷雨", "降水", "傘", "濡れ", "豪雨", "にわか雨"]
                if any(keyword in comment.comment_text for keyword in rain_keywords):
                    logger.debug(f"晴天時に雨のコメントを除外: '{comment.comment_text}'")
                    return None
            
            # 曇天時に強い日差しのコメントを除外
            if "曇" in weather_data.weather_description:
                sunshine_keywords = ["強い日差し", "眩しい", "日光", "紫外線が強", "日焼け", "太陽がギラギラ"]
                if any(keyword in comment.comment_text for keyword in sunshine_keywords):
                    logger.debug(f"曇天時に強い日差しのコメントを除外: '{comment.comment_text}'")
                    return None
            
            if comment_validator.is_weather_matched(comment.weather_condition, weather_data.weather_description):
                return 'weather_matched'
            else:
                return 'others'
    
    def apply_limits(self, prioritized: PrioritizedComments) -> list[dict[str, Any]]:
        """優先順位に基づいて制限を適用
        
        Args:
            prioritized: 優先順位付けされたコメント
            
        Returns:
            制限が適用されたコメントリスト
        """
        # 各カテゴリの制限を計算
        severe_limit = int(self.limit * self.severe_ratio)
        weather_limit = int(self.limit * self.weather_ratio) 
        others_limit = self.limit - severe_limit - weather_limit
        
        candidates = (
            prioritized.severe_matched[:severe_limit] + 
            prioritized.weather_matched[:weather_limit] + 
            prioritized.others[:others_limit]
        )
        
        logger.info(f"天気コメント候補: severe={len(prioritized.severe_matched)}件, "
                   f"weather={len(prioritized.weather_matched)}件, "
                   f"others={len(prioritized.others)}件")
        logger.info(f"選択された候補数: {len(candidates)}件 (制限: {self.limit}件)")
        
        return candidates
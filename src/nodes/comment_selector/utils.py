"""コメント選択のユーティリティ関数"""

import logging
from typing import Dict, Any, Optional, List
from functools import lru_cache

from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState
from src.config.config_loader import load_config

logger = logging.getLogger(__name__)

# 設定ファイルから閾値を読み込み
_weather_config = load_config('weather_thresholds', validate=False)
EXTREME_HEAT_THRESHOLD = _weather_config.get('temperature', {}).get('extreme_heat_threshold', 35.0)


class CommentUtils:
    """コメント選択に関するユーティリティクラス"""
    
    @staticmethod
    @lru_cache(maxsize=128)
    def _get_weather_summary(cache_key: str, period_forecasts_tuple: tuple) -> tuple:
        """天気サマリーを取得（LRUキャッシュ付き）"""
        has_rain_in_timeline = False
        max_temp_in_timeline = 0.0
        
        # タプルの各要素は(precipitation, temperature)のペア
        for precipitation, temperature in period_forecasts_tuple:
            if precipitation > 0:
                has_rain_in_timeline = True
            if temperature > max_temp_in_timeline:
                max_temp_in_timeline = temperature
        
        return has_rain_in_timeline, max_temp_in_timeline
    
    def prepare_weather_candidates(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast,
        weather_validator,
        comment_validator,
        target_datetime,
        state: Optional[CommentGenerationState] = None
    ) -> List[Dict[str, Any]]:
        """天気コメント候補を準備"""
        candidates = []
        severe_matched = []
        weather_matched = []
        others = []
        
        for i, comment in enumerate(comments):
            # バリデーターによる除外チェック（強化版）
            is_valid, reason = weather_validator.validate_comment(comment, weather_data)
            if not is_valid:
                logger.debug(f"バリデーター除外: '{comment.comment_text}' - 理由: {reason}")
                continue
            
            # 晴天時の「変わりやすい」表現の追加チェック（強化）
            if comment_validator.is_sunny_weather_with_changeable_comment(comment.comment_text, weather_data):
                logger.debug(f"晴天時不適切表現を強制除外: '{comment.comment_text}'")
                continue
            
            # 曇り天気時の日差し表現の追加チェック
            if comment_validator.is_cloudy_weather_with_sunshine_comment(comment.comment_text, weather_data):
                logger.debug(f"曇り天気時の日差し表現を強制除外: '{comment.comment_text}'")
                continue
            
            # 降水なし時の雨・雷表現の追加チェック
            if comment_validator.is_no_rain_weather_with_rain_comment(comment.comment_text, weather_data):
                logger.debug(f"降水なし時の雨・雷表現を強制除外: '{comment.comment_text}'")
                continue
            
            # 月に不適切な季節表現のチェック
            if comment_validator.is_inappropriate_seasonal_comment(comment.comment_text, target_datetime):
                logger.debug(f"月に不適切な季節表現を強制除外: '{comment.comment_text}'")
                continue
            
            # 安定した天気での急変表現の追加チェック
            if comment_validator.is_stable_weather_with_unstable_comment(comment.comment_text, weather_data, state):
                logger.debug(f"安定天気時の急変表現を強制除外: '{comment.comment_text}'")
                continue
                
            # 旧式の除外チェック（後方互換）
            if comment_validator.should_exclude_weather_comment(comment.comment_text, weather_data):
                logger.debug(f"天気条件不適合のため除外: '{comment.comment_text}'")
                continue
                
            candidate = self._create_candidate_dict(
                len(severe_matched) + len(weather_matched) + len(others), 
                comment, 
                original_index=i
            )
            
            # 特別な優先順位付け（雨天時・高温時の最優先処理）
            is_prioritized = False
            
            # period_forecastsから4時点のデータを確認（最初に一度だけ実行）
            has_rain_in_timeline = False
            max_temp_in_timeline = weather_data.temperature  # デフォルトは現在の温度
            
            # stateから事前計算された値を取得（LRUキャッシュ使用）
            cache_key = f"{weather_data.datetime}_{weather_data.location_id if hasattr(weather_data, 'location_id') else ''}"
            
            if state and hasattr(state, 'generation_metadata'):
                period_forecasts = state.generation_metadata.get('period_forecasts', [])
                logger.debug(f"period_forecastsを取得: {len(period_forecasts)}件")
                if period_forecasts:
                    # タプルを使用して効率的にキャッシュ
                    period_forecasts_tuple = tuple(
                        (getattr(f, 'precipitation', 0), getattr(f, 'temperature', 0))
                        for f in period_forecasts
                    )
                    
                    # LRUキャッシュを使用して取得
                    has_rain_in_timeline, max_temp_in_timeline = self._get_weather_summary(
                        cache_key, period_forecasts_tuple
                    )
                    
                    if has_rain_in_timeline:
                        logger.debug(f"4時点予報で雨を検出（LRUキャッシュ使用）")
                else:
                    # period_forecastsが空の場合、weather_timelineをフォールバック
                    weather_timeline = state.generation_metadata.get('weather_timeline', {})
                    future_forecasts = weather_timeline.get('future_forecasts', [])
                    for forecast in future_forecasts:
                        if forecast.get('precipitation', 0) > 0:
                            has_rain_in_timeline = True
                            break
            
            # 1. 雨天時の最優先処理（単一時点または時系列データで雨がある場合）
            if weather_data.precipitation > 0 or has_rain_in_timeline:
                rain_keywords = ["雨", "傘", "濡れ", "降水", "にわか雨", "雷雨"]
                if any(keyword in comment.comment_text for keyword in rain_keywords):
                    severe_matched.append(candidate)  # 雨天時は最優先カテゴリに入れる
                    is_prioritized = True
                    logger.info(f"雨天時のコメントを最優先に: '{comment.comment_text}' (現在降水量: {weather_data.precipitation}mm, 時系列に雨: {has_rain_in_timeline})")
            
            # 2. 高温時（設定温度以上）の最優先処理（4時点の最高気温を考慮）
            if not is_prioritized and (weather_data.temperature >= EXTREME_HEAT_THRESHOLD or max_temp_in_timeline >= EXTREME_HEAT_THRESHOLD):
                heat_keywords = ["熱中症", "水分補給", "涼しい", "冷房", "暑さ対策", "猛暑", "高温"]
                if any(keyword in comment.comment_text for keyword in heat_keywords):
                    severe_matched.append(candidate)  # 高温時も最優先カテゴリに入れる
                    is_prioritized = True
                    logger.debug(f"高温時（最高{max_temp_in_timeline}℃）のコメントを最優先に: '{comment.comment_text}'")
            
            # 3. 通常の悪天候時の処理
            if not is_prioritized:
                from src.config.severe_weather_config import get_severe_weather_config
                severe_config = get_severe_weather_config()
                
                if severe_config.is_severe_weather(weather_data.weather_condition):
                    if comment_validator.is_severe_weather_appropriate(comment.comment_text, weather_data):
                        severe_matched.append(candidate)
                    elif comment_validator.is_weather_matched(comment.weather_condition, weather_data.weather_description):
                        weather_matched.append(candidate)
                    else:
                        others.append(candidate)
                else:
                    if comment_validator.is_weather_matched(comment.weather_condition, weather_data.weather_description):
                        weather_matched.append(candidate)
                    else:
                        others.append(candidate)
        
        
        # 優先順位順に結合（設定ファイルから制限を取得）
        from src.config.config_loader import load_config
        try:
            config = load_config('weather_thresholds', validate=False)
            limit = config.get('generation', {}).get('weather_candidates_limit', 100)
        except (FileNotFoundError, KeyError, Exception) as e:
            logger.debug(f"設定ファイル読み込みエラー: {e}")
            limit = 100  # デフォルト値
        
        # 設定ファイルから候補比率を取得
        try:
            ratios = config.get('generation', {}).get('candidate_ratios', {})
            severe_ratio = ratios.get('severe_weather', 0.4)
            weather_ratio = ratios.get('weather_matched', 0.4)
            others_ratio = ratios.get('others', 0.2)
        except (AttributeError, NameError, Exception) as e:
            # デフォルト比率（悪天候40%, 天気マッチ40%, その他20%）
            severe_ratio, weather_ratio, others_ratio = 0.4, 0.4, 0.2
        
        # 各カテゴリの制限を計算
        severe_limit = int(limit * severe_ratio)
        weather_limit = int(limit * weather_ratio) 
        others_limit = limit - severe_limit - weather_limit
        
        candidates = (severe_matched[:severe_limit] + weather_matched[:weather_limit] + others[:others_limit])
        
        return candidates
    
    def prepare_advice_candidates(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast,
        weather_validator,
        comment_validator,
        target_datetime
    ) -> List[Dict[str, Any]]:
        """アドバイスコメント候補を準備"""
        candidates = []
        
        for i, comment in enumerate(comments):
            # バリデーターによる除外チェック
            is_valid, reason = weather_validator.validate_comment(comment, weather_data)
            if not is_valid:
                logger.debug(f"アドバイスバリデーター除外: '{comment.comment_text}' - 理由: {reason}")
                continue
            
            # 曇り天気時の日差し表現の追加チェック（アドバイスも同様）
            if comment_validator.is_cloudy_weather_with_sunshine_comment(comment.comment_text, weather_data):
                logger.debug(f"曇り天気時の日差し表現を強制除外（アドバイス）: '{comment.comment_text}'")
                continue
            
            # 降水なし時の雨・雷表現の追加チェック（アドバイスも同様）
            if comment_validator.is_no_rain_weather_with_rain_comment(comment.comment_text, weather_data):
                logger.debug(f"降水なし時の雨・雷表現を強制除外（アドバイス）: '{comment.comment_text}'")
                continue
            
            # 月に不適切な季節表現のチェック（アドバイスも同様）
            if comment_validator.is_inappropriate_seasonal_comment(comment.comment_text, target_datetime):
                logger.debug(f"月に不適切な季節表現を強制除外（アドバイス）: '{comment.comment_text}'")
                continue
                
            # 旧式の除外チェック（後方互換）
            if comment_validator.should_exclude_advice_comment(comment.comment_text, weather_data):
                logger.debug(f"アドバイス条件不適合のため除外: '{comment.comment_text}'")
                continue
                
            candidate = self._create_candidate_dict(len(candidates), comment, original_index=i)
            candidates.append(candidate)
            
            # 設定ファイルから制限を取得
            from src.config.config_loader import load_config
            try:
                config = load_config('weather_thresholds', validate=False)
                limit = config.get('generation', {}).get('advice_candidates_limit', 100)
            except (FileNotFoundError, KeyError, Exception) as e:
                logger.debug(f"設定ファイル読み込みエラー（アドバイス）: {e}")
                limit = 100  # デフォルト値
            
            if len(candidates) >= limit:
                break
        
        return candidates
    
    def _create_candidate_dict(self, index: int, comment: PastComment, original_index: int) -> Dict[str, Any]:
        """候補辞書を作成"""
        return {
            'index': index,
            'original_index': original_index,
            'comment': comment.comment_text,
            'comment_object': comment,
            'weather_condition': comment.weather_condition,
            'usage_count': comment.usage_count,
            'evaluation_mode': getattr(comment, 'evaluation_mode', 'standard'),
        }
"""コメント選択のユーティリティ関数"""

import logging
from typing import Dict, Any, Optional, List

from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState

logger = logging.getLogger(__name__)


class CommentUtils:
    """コメント選択に関するユーティリティクラス"""
    
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
        rain_priority = []  # 雨天時の優先候補
        severe_matched = []
        weather_matched = []
        others = []
        
        for i, comment in enumerate(comments):
            # バリデーターによる除外チェック（強化版）
            is_valid, reason = weather_validator.validate_comment(comment, weather_data)
            if not is_valid:
                logger.info(f"バリデーター除外: '{comment.comment_text}' - 理由: {reason}")
                continue
            
            # 晴天時の「変わりやすい」表現の追加チェック（強化）
            if comment_validator.is_sunny_weather_with_changeable_comment(comment.comment_text, weather_data):
                logger.info(f"晴天時不適切表現を強制除外: '{comment.comment_text}'")
                continue
            
            # 曇り天気時の日差し表現の追加チェック
            if comment_validator.is_cloudy_weather_with_sunshine_comment(comment.comment_text, weather_data):
                logger.info(f"曇り天気時の日差し表現を強制除外: '{comment.comment_text}'")
                continue
            
            # 降水なし時の雨・雷表現の追加チェック
            if comment_validator.is_no_rain_weather_with_rain_comment(comment.comment_text, weather_data):
                logger.info(f"降水なし時の雨・雷表現を強制除外: '{comment.comment_text}'")
                continue
            
            # 月に不適切な季節表現のチェック
            if comment_validator.is_inappropriate_seasonal_comment(comment.comment_text, target_datetime):
                logger.info(f"月に不適切な季節表現を強制除外: '{comment.comment_text}'")
                continue
            
            # 安定した天気での急変表現の追加チェック
            if comment_validator.is_stable_weather_with_unstable_comment(comment.comment_text, weather_data, state):
                logger.info(f"安定天気時の急変表現を強制除外: '{comment.comment_text}'")
                continue
                
            # 旧式の除外チェック（後方互換）
            if comment_validator.should_exclude_weather_comment(comment.comment_text, weather_data):
                logger.debug(f"天気条件不適合のため除外: '{comment.comment_text}'")
                continue
                
            candidate = self._create_candidate_dict(
                len(rain_priority) + len(severe_matched) + len(weather_matched) + len(others), 
                comment, 
                original_index=i
            )
            
            # 雨天時の特別な優先順位付け（現在または将来の予報を考慮）
            has_rain_now = weather_data.precipitation > 0
            has_rain_forecast = False
            max_future_precipitation = 0.0
            
            # 将来の予報データをチェック
            if hasattr(weather_data, 'hourly_forecasts') and weather_data.hourly_forecasts:
                logger.info(f"予報データ数: {len(weather_data.hourly_forecasts)}")
                for forecast in weather_data.hourly_forecasts:
                    if hasattr(forecast, 'precipitation_mm') and forecast.precipitation_mm > 0:
                        has_rain_forecast = True
                        max_future_precipitation = max(max_future_precipitation, forecast.precipitation_mm)
                        logger.info(f"雨予報検出: {forecast.datetime if hasattr(forecast, 'datetime') else '時刻不明'} - {forecast.precipitation_mm}mm")
                    elif hasattr(forecast, 'precipitation') and forecast.precipitation > 0:
                        has_rain_forecast = True
                        max_future_precipitation = max(max_future_precipitation, forecast.precipitation)
                        logger.info(f"雨予報検出: {forecast.datetime if hasattr(forecast, 'datetime') else '時刻不明'} - {forecast.precipitation}mm")
            
            if has_rain_now or has_rain_forecast:
                rain_keywords = ["雨", "降雨", "雨が", "にわか雨", "雨模様", "雨音", "雨降り", "傘"]
                if any(keyword in comment.comment_text for keyword in rain_keywords):
                    rain_priority.append(candidate)
                    logger.debug(f"雨天時優先候補に追加: '{comment.comment_text}' (現在雨: {has_rain_now}, 予報雨: {has_rain_forecast}, 最大降水量: {max_future_precipitation}mm)")
                    continue
            
            # 悪天候時の特別な優先順位付け
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
        except:
            limit = 100  # デフォルト値
        
        # 雨天時は雨関連コメントを最優先（現在または将来の予報を考慮）
        has_rain = weather_data.precipitation > 0
        if hasattr(weather_data, 'hourly_forecasts') and weather_data.hourly_forecasts:
            has_rain = has_rain or any(
                (hasattr(f, 'precipitation_mm') and f.precipitation_mm > 0) or 
                (hasattr(f, 'precipitation') and f.precipitation > 0) 
                for f in weather_data.hourly_forecasts
            )
        
        if has_rain and rain_priority:
            # 雨天時は雨関連候補を50%以上確保
            rain_limit = max(limit // 2, len(rain_priority))
            remaining_limit = limit - min(len(rain_priority), rain_limit)
            
            # 残りの枠を他のカテゴリに配分
            if remaining_limit > 0:
                severe_limit = min(len(severe_matched), remaining_limit // 3)
                weather_limit = min(len(weather_matched), remaining_limit // 3)
                others_limit = remaining_limit - severe_limit - weather_limit
                
                candidates = (rain_priority[:rain_limit] + 
                            severe_matched[:severe_limit] + 
                            weather_matched[:weather_limit] + 
                            others[:others_limit])
            else:
                candidates = rain_priority[:limit]
                
            logger.info(f"雨天時の候補配分 - 雨優先: {len(rain_priority[:rain_limit])}, " +
                       f"悪天候: {len(severe_matched[:severe_limit]) if remaining_limit > 0 else 0}, " +
                       f"天気マッチ: {len(weather_matched[:weather_limit]) if remaining_limit > 0 else 0}, " +
                       f"その他: {len(others[:others_limit]) if remaining_limit > 0 else 0}")
        else:
            # 通常時の配分
            # 設定ファイルから候補比率を取得
            try:
                ratios = config.get('generation', {}).get('candidate_ratios', {})
                severe_ratio = ratios.get('severe_weather', 0.4)
                weather_ratio = ratios.get('weather_matched', 0.4)
                others_ratio = ratios.get('others', 0.2)
            except:
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
        rain_priority = []  # 雨天時の優先候補
        candidates = []
        
        for i, comment in enumerate(comments):
            # バリデーターによる除外チェック
            is_valid, reason = weather_validator.validate_comment(comment, weather_data)
            if not is_valid:
                logger.info(f"アドバイスバリデーター除外: '{comment.comment_text}' - 理由: {reason}")
                continue
            
            # 曇り天気時の日差し表現の追加チェック（アドバイスも同様）
            if comment_validator.is_cloudy_weather_with_sunshine_comment(comment.comment_text, weather_data):
                logger.info(f"曇り天気時の日差し表現を強制除外（アドバイス）: '{comment.comment_text}'")
                continue
            
            # 降水なし時の雨・雷表現の追加チェック（アドバイスも同様）
            if comment_validator.is_no_rain_weather_with_rain_comment(comment.comment_text, weather_data):
                logger.info(f"降水なし時の雨・雷表現を強制除外（アドバイス）: '{comment.comment_text}'")
                continue
            
            # 月に不適切な季節表現のチェック（アドバイスも同様）
            if comment_validator.is_inappropriate_seasonal_comment(comment.comment_text, target_datetime):
                logger.info(f"月に不適切な季節表現を強制除外（アドバイス）: '{comment.comment_text}'")
                continue
                
            # 旧式の除外チェック（後方互換）
            if comment_validator.should_exclude_advice_comment(comment.comment_text, weather_data):
                logger.debug(f"アドバイス条件不適合のため除外: '{comment.comment_text}'")
                continue
                
            candidate = self._create_candidate_dict(len(rain_priority) + len(candidates), comment, original_index=i)
            
            # 雨天時の特別な優先順位付け（現在または将来の予報を考慮）
            has_rain_now = weather_data.precipitation > 0
            has_rain_forecast = False
            
            # 将来の予報データをチェック
            if hasattr(weather_data, 'hourly_forecasts') and weather_data.hourly_forecasts:
                for forecast in weather_data.hourly_forecasts:
                    if (hasattr(forecast, 'precipitation_mm') and forecast.precipitation_mm > 0) or \
                       (hasattr(forecast, 'precipitation') and forecast.precipitation > 0):
                        has_rain_forecast = True
                        break
            
            if has_rain_now or has_rain_forecast:
                rain_keywords = ["傘", "雨具", "雨対策", "濡れ", "レインコート", "雨よけ", "雨宿り"]
                if any(keyword in comment.comment_text for keyword in rain_keywords):
                    rain_priority.append(candidate)
                    logger.debug(f"雨天時優先アドバイス候補に追加: '{comment.comment_text}' (現在雨: {has_rain_now}, 予報雨: {has_rain_forecast})")
                    continue
            
            candidates.append(candidate)
            
        # 設定ファイルから制限を取得
        from src.config.config_loader import load_config
        try:
            config = load_config('weather_thresholds', validate=False)
            limit = config.get('generation', {}).get('advice_candidates_limit', 100)
        except:
            limit = 100  # デフォルト値
        
        # 雨天時は雨関連アドバイスを最優先（現在または将来の予報を考慮）
        has_rain = weather_data.precipitation > 0
        if hasattr(weather_data, 'hourly_forecasts') and weather_data.hourly_forecasts:
            has_rain = has_rain or any(
                (hasattr(f, 'precipitation_mm') and f.precipitation_mm > 0) or 
                (hasattr(f, 'precipitation') and f.precipitation > 0) 
                for f in weather_data.hourly_forecasts
            )
        
        if has_rain and rain_priority:
            # 雨天時は雨関連候補を50%以上確保
            rain_limit = max(limit // 2, len(rain_priority))
            remaining_limit = limit - min(len(rain_priority), rain_limit)
            
            if remaining_limit > 0:
                final_candidates = rain_priority[:rain_limit] + candidates[:remaining_limit]
            else:
                final_candidates = rain_priority[:limit]
                
            logger.info(f"雨天時のアドバイス候補配分 - 雨優先: {len(rain_priority[:rain_limit])}, " +
                       f"その他: {len(candidates[:remaining_limit]) if remaining_limit > 0 else 0}")
            return final_candidates
        else:
            return candidates[:limit]
    
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
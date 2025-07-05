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
                logger.info(f"バリデーター除外: '{comment.comment_text}' - 理由: {reason}")
                continue
            
            # 晴天時の「変わりやすい」表現の追加チェック（強化）
            if comment_validator.is_sunny_weather_with_changeable_comment(comment.comment_text, weather_data):
                logger.info(f"晴天時不適切表現を強制除外: '{comment.comment_text}'")
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
                len(severe_matched) + len(weather_matched) + len(others), 
                comment, 
                original_index=i
            )
            
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
        comment_validator
    ) -> List[Dict[str, Any]]:
        """アドバイスコメント候補を準備"""
        candidates = []
        
        for i, comment in enumerate(comments):
            # バリデーターによる除外チェック
            is_valid, reason = weather_validator.validate_comment(comment, weather_data)
            if not is_valid:
                logger.info(f"アドバイスバリデーター除外: '{comment.comment_text}' - 理由: {reason}")
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
            except:
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
"""コメント選択のユーティリティ関数（リファクタリング版）"""

from __future__ import annotations
import logging
from typing import Any

from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState
from src.config.config_loader import load_config

from .weather_summary import WeatherSummaryGenerator
from .comment_prioritizer import CommentPrioritizer, PrioritizedComments
from .candidate_builder import CandidateBuilder

logger = logging.getLogger(__name__)


class CommentUtils:
    """コメント選択に関するユーティリティクラス（リファクタリング版）"""
    
    def __init__(self):
        self.weather_summary_generator = WeatherSummaryGenerator()
        self.comment_prioritizer = CommentPrioritizer()
        self.candidate_builder = CandidateBuilder()
    
    def prepare_weather_candidates(
        self, 
        comments: list[PastComment], 
        weather_data: WeatherForecast,
        weather_validator,
        comment_validator,
        target_datetime,
        state: CommentGenerationState | None = None
    ) -> list[dict[str, Any]]:
        """天気コメント候補を準備"""
        # 優先順位付けされたコメントを格納
        prioritized = PrioritizedComments(
            severe_matched=[],
            weather_matched=[],
            others=[]
        )
        
        # 天気サマリーを取得
        has_rain_in_timeline, max_temp_in_timeline, _ = self.weather_summary_generator.analyze_weather_timeline(
            weather_data, state
        )
        
        for i, comment in enumerate(comments):
            # バリデーション処理
            if not self._validate_comment(
                comment, weather_data, weather_validator, 
                comment_validator, target_datetime, state, is_advice=False
            ):
                continue
            
            # 候補辞書を作成
            candidate = self.candidate_builder.create_candidate_dict(
                len(prioritized.severe_matched) + len(prioritized.weather_matched) + len(prioritized.others), 
                comment, 
                original_index=i
            )
            
            # 優先度を判定
            priority = self.comment_prioritizer.prioritize_comment(
                comment, weather_data, has_rain_in_timeline, 
                max_temp_in_timeline, comment_validator
            )
            
            if priority is None:
                continue  # 除外
            elif priority == 'severe':
                prioritized.severe_matched.append(candidate)
            elif priority == 'weather_matched':
                prioritized.weather_matched.append(candidate)
            else:
                prioritized.others.append(candidate)
        
        # 制限を適用して最終的な候補リストを作成
        candidates = self.comment_prioritizer.apply_limits(prioritized)
        
        if not candidates:
            logger.error("天気コメント候補が0件です")
            logger.error(f"元のコメント数: {len(comments)}件")
            logger.error(f"天気情報: {weather_data.weather_description}, "
                        f"気温: {weather_data.temperature}°C, "
                        f"降水量: {weather_data.precipitation}mm")
        
        return candidates
    
    def prepare_advice_candidates(
        self, 
        comments: list[PastComment], 
        weather_data: WeatherForecast,
        weather_validator,
        comment_validator,
        target_datetime
    ) -> list[dict[str, Any]]:
        """アドバイスコメント候補を準備"""
        candidates = []
        
        # 設定ファイルから制限を取得
        try:
            config = load_config('weather_thresholds', validate=False)
            limit = config.get('generation', {}).get('advice_candidates_limit', 100)
        except Exception as e:
            logger.debug(f"設定ファイル読み込みエラー（アドバイス）: {e}")
            limit = 100  # デフォルト値
        
        for i, comment in enumerate(comments):
            # バリデーション処理
            if not self._validate_comment(
                comment, weather_data, weather_validator, 
                comment_validator, target_datetime, None, is_advice=True
            ):
                continue
            
            candidate = self.candidate_builder.create_candidate_dict(
                len(candidates), comment, original_index=i
            )
            candidates.append(candidate)
            
            if len(candidates) >= limit:
                break
        
        logger.info(f"アドバイスコメント候補: {len(candidates)}件 (制限: {limit}件)")
        
        if not candidates:
            logger.error("アドバイスコメント候補が0件です")
            logger.error(f"元のコメント数: {len(comments)}件")
            logger.error(f"天気情報: {weather_data.weather_description}, "
                        f"気温: {weather_data.temperature}°C, "
                        f"降水量: {weather_data.precipitation}mm")
        
        return candidates
    
    def _validate_comment(
        self,
        comment: PastComment,
        weather_data: WeatherForecast,
        weather_validator,
        comment_validator,
        target_datetime,
        state: CommentGenerationState | None,
        is_advice: bool
    ) -> bool:
        """コメントのバリデーションを実行
        
        Returns:
            True: 有効なコメント
            False: 除外すべきコメント
        """
        comment_type = "アドバイス" if is_advice else ""
        
        # バリデーターによる除外チェック
        is_valid, reason = weather_validator.validate_comment(comment, weather_data)
        if not is_valid:
            logger.debug(f"{comment_type}バリデーター除外: '{comment.comment_text}' - 理由: {reason}")
            return False
        
        # 晴天時の「変わりやすい」表現の追加チェック（天気コメントのみ）
        if not is_advice and comment_validator.is_sunny_weather_with_changeable_comment(
            comment.comment_text, weather_data
        ):
            logger.debug(f"晴天時不適切表現を強制除外: '{comment.comment_text}'")
            return False
        
        # 曇り天気時の日差し表現の追加チェック
        if comment_validator.is_cloudy_weather_with_sunshine_comment(
            comment.comment_text, weather_data
        ):
            logger.debug(f"曇り天気時の日差し表現を強制除外{comment_type}: '{comment.comment_text}'")
            return False
        
        # 降水なし時の雨・雷表現の追加チェック
        if comment_validator.is_no_rain_weather_with_rain_comment(
            comment.comment_text, weather_data
        ):
            logger.debug(f"降水なし時の雨・雷表現を強制除外{comment_type}: '{comment.comment_text}'")
            return False
        
        # 月に不適切な季節表現のチェック
        if comment_validator.is_inappropriate_seasonal_comment(
            comment.comment_text, target_datetime
        ):
            logger.debug(f"月に不適切な季節表現を強制除外{comment_type}: '{comment.comment_text}'")
            return False
        
        # 安定した天気での急変表現の追加チェック（天気コメントのみ）
        if not is_advice and comment_validator.is_stable_weather_with_unstable_comment(
            comment.comment_text, weather_data, state
        ):
            logger.debug(f"安定天気時の急変表現を強制除外: '{comment.comment_text}'")
            return False
        
        # 雨天時の花粉表現の追加チェック
        if comment_validator.is_rain_weather_with_pollen_comment(
            comment.comment_text, weather_data
        ):
            logger.debug(f"雨天時の花粉表現を強制除外{comment_type}: '{comment.comment_text}'")
            return False
        
        # 旧式の除外チェック（後方互換）
        if is_advice:
            if comment_validator.should_exclude_advice_comment(comment.comment_text, weather_data):
                logger.debug(f"アドバイス条件不適合のため除外: '{comment.comment_text}'")
                return False
        else:
            if comment_validator.should_exclude_weather_comment(comment.comment_text, weather_data):
                logger.debug(f"天気条件不適合のため除外: '{comment.comment_text}'")
                return False
        
        return True
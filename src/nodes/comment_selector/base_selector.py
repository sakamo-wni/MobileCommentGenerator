"""コメント選択の基本クラス"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import CommentType, PastComment
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.config.config import get_severe_weather_config

from .llm_selector import LLMCommentSelector
from .validation import CommentValidator
from .utils import CommentUtils

logger = logging.getLogger(__name__)


class CommentSelector:
    """コメント選択クラス"""
    
    def __init__(self, llm_manager: LLMManager, validator: WeatherCommentValidator):
        self.llm_manager = llm_manager
        self.validator = validator
        self.severe_config = get_severe_weather_config()
        self.llm_selector = LLMCommentSelector(llm_manager)
        self.comment_validator = CommentValidator(validator, self.severe_config)
        self.utils = CommentUtils()
    
    def select_optimal_comment_pair(
        self, 
        weather_comments: List[PastComment], 
        advice_comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None,
        exclude_weather_comment: Optional[str] = None,
        exclude_advice_comment: Optional[str] = None
    ) -> Optional[CommentPair]:
        """最適なコメントペアを選択"""
        
        # 事前フィルタリング
        filtered_weather = self.validator.get_weather_appropriate_comments(
            weather_comments, weather_data, CommentType.WEATHER_COMMENT, limit=500
        )
        filtered_advice = self.validator.get_weather_appropriate_comments(
            advice_comments, weather_data, CommentType.ADVICE, limit=500
        )
        
        # 除外対象のコメントを削除
        if exclude_weather_comment:
            original_count = len(filtered_weather)
            filtered_weather = [c for c in filtered_weather 
                             if c.comment_text.strip() != exclude_weather_comment.strip()]
            logger.info(f"天気コメントから前回の生成結果を除外: '{exclude_weather_comment}' (除外前: {original_count}件 → 除外後: {len(filtered_weather)}件)")
            
        if exclude_advice_comment:
            original_count = len(filtered_advice)
            filtered_advice = [c for c in filtered_advice 
                             if c.comment_text.strip() != exclude_advice_comment.strip()]
            logger.info(f"アドバイスコメントから前回の生成結果を除外: '{exclude_advice_comment}' (除外前: {original_count}件 → 除外後: {len(filtered_advice)}件)")
        
        logger.info(f"フィルタリング結果 - 天気: {len(weather_comments)} -> {len(filtered_weather)}")
        logger.info(f"フィルタリング結果 - アドバイス: {len(advice_comments)} -> {len(filtered_advice)}")
        
        # デバッグ: 元のコメント数と内容を確認
        logger.debug(f"元の天気コメント総数: {len(weather_comments)}")
        logger.debug(f"元のアドバイスコメント総数: {len(advice_comments)}")
        
        # 最適なコメントを選択
        best_weather = self._select_best_weather_comment(
            filtered_weather, weather_data, location_name, target_datetime, state
        )
        best_advice = self._select_best_advice_comment(
            filtered_advice, weather_data, location_name, target_datetime, state
        )
        
        if not best_weather or not best_advice:
            return None
            
        # ペア作成前の最終バリデーション
        if not self.comment_validator.validate_comment_pair(best_weather, best_advice, weather_data, state):
            # 重複回避のための代替選択を試行
            alternative_pair = self._select_alternative_non_duplicate_pair(
                filtered_weather, filtered_advice, weather_data, location_name, target_datetime, state
            )
            if alternative_pair:
                return alternative_pair
            
            # 代替選択も失敗した場合はフォールバック処理
            return self._fallback_comment_selection(
                weather_comments, advice_comments, weather_data, state
            )
        
        return CommentPair(
            weather_comment=best_weather,
            advice_comment=best_advice,
            similarity_score=1.0,
            selection_reason="LLMによる最適選択",
        )
    
    def _select_best_weather_comment(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """天気コメントの選択"""
        if not comments:
            return None
            
        # 天気コメント用の候補を準備
        candidates = self.utils.prepare_weather_candidates(
            comments, weather_data, self.validator, self.comment_validator, target_datetime, state
        )
        
        if not candidates:
            logger.warning("適切な天気コメント候補が見つかりません")
            return None
            
        # LLMで選択
        return self.llm_selector.llm_select_comment(
            candidates, weather_data, location_name, target_datetime, CommentType.WEATHER_COMMENT, state
        )
    
    def _select_best_advice_comment(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """アドバイスコメントの選択"""
        if not comments:
            return None
            
        # アドバイス用の候補を準備
        candidates = self.utils.prepare_advice_candidates(
            comments, weather_data, self.validator, self.comment_validator, target_datetime
        )
        
        if not candidates:
            logger.warning("適切なアドバイス候補が見つかりません")
            return None
            
        # LLMで選択
        return self.llm_selector.llm_select_comment(
            candidates, weather_data, location_name, target_datetime, CommentType.ADVICE, state
        )
    
    def _fallback_comment_selection(
        self,
        weather_comments: List[PastComment],
        advice_comments: List[PastComment],
        weather_data: WeatherForecast,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[CommentPair]:
        """フォールバック選択処理"""
        logger.warning("フォールバック選択を実行")
        
        # 雨の場合の特別処理
        if weather_data.precipitation > 0:
            weather_comment = self._find_rain_appropriate_weather_comment(weather_comments, weather_data, state)
            advice_comment = self._find_rain_appropriate_advice_comment(advice_comments, state)
            
            if weather_comment and advice_comment:
                return CommentPair(
                    weather_comment=weather_comment,
                    advice_comment=advice_comment,
                    similarity_score=0.5,
                    selection_reason="雨天時フォールバック"
                )
        
        # 最後の手段：バリデーションを通過するコメントを探す
        valid_weather_comment = None
        valid_advice_comment = None
        
        # 天気コメントから有効なものを探す
        for comment in weather_comments:
            is_valid, _ = self.validator.validate_comment(comment, weather_data)
            if is_valid:
                valid_weather_comment = comment
                break
        
        # アドバイスコメントから有効なものを探す  
        for comment in advice_comments:
            is_valid, _ = self.validator.validate_comment(comment, weather_data)
            if is_valid:
                valid_advice_comment = comment
                break
        
        if valid_weather_comment and valid_advice_comment:
            return CommentPair(
                weather_comment=valid_weather_comment,
                advice_comment=valid_advice_comment,
                similarity_score=0.3,
                selection_reason="最終フォールバック（検証済み）"
            )
        
        # どうしても見つからない場合は、最低限海岸関連のチェックだけ行う
        if weather_comments and advice_comments:
            # 海岸バリデータがある場合は使用
            if hasattr(self.validator, 'coastal_validator') and self.validator.coastal_validator:
                for weather_comment in weather_comments:
                    coastal_check = self.validator.coastal_validator.validate(weather_comment, weather_data)
                    if coastal_check[0]:  # 海岸チェックを通過
                        for advice_comment in advice_comments:
                            coastal_check_advice = self.validator.coastal_validator.validate(advice_comment, weather_data)
                            if coastal_check_advice[0]:  # アドバイスも海岸チェックを通過
                                logger.warning("最終フォールバック：海岸チェックのみ通過したコメントを使用")
                                return CommentPair(
                                    weather_comment=weather_comment,
                                    advice_comment=advice_comment,
                                    similarity_score=0.2,
                                    selection_reason="最終フォールバック（海岸チェックのみ）"
                                )
            
            # 本当に最後の手段
            logger.error("すべてのバリデーションを通過するコメントが見つかりません。最初のコメントを使用します。")
            return CommentPair(
                weather_comment=weather_comments[0],
                advice_comment=advice_comments[0],
                similarity_score=0.1,
                selection_reason="最終フォールバック（検証なし）"
            )
            
        return None
    
    def _find_rain_appropriate_weather_comment(
        self, 
        comments: List[PastComment],
        weather_data: WeatherForecast,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """雨に適した天気コメントを探す（降水量に応じた表現の妥当性をチェック）"""
        rain_keywords = ["雨", "降水", "にわか雨", "傘"]
        
        # 連続雨かどうかを判定
        is_continuous_rain = False
        rain_hours = 0
        if state and hasattr(state, 'period_forecasts') and state.period_forecasts:
            rain_hours = sum(1 for f in state.period_forecasts if f.weather == "雨")
            is_continuous_rain = rain_hours >= 4  # 4時間すべて雨
        
        # 降水量に基づく不適切な表現のチェック
        for comment in comments:
            if any(keyword in comment.comment_text for keyword in rain_keywords):
                # 降水量が10mm/h未満の場合、強雨表現は不適切
                if weather_data.precipitation < 10.0:
                    strong_rain_expressions = ["強雨", "激しい雨", "土砂降り", "豪雨", "大雨", "どしゃ降り", "ザーザー"]
                    if any(expr in comment.comment_text for expr in strong_rain_expressions):
                        logger.debug(f"降水量{weather_data.precipitation}mm/hに対して過度な表現のためスキップ: {comment.comment_text}")
                        continue
                
                # 降水量が5mm/h未満の場合、中程度の雨表現も不適切
                if weather_data.precipitation < 5.0:
                    moderate_rain_expressions = ["本降り", "しっかりとした雨", "まとまった雨"]
                    if any(expr in comment.comment_text for expr in moderate_rain_expressions):
                        logger.debug(f"降水量{weather_data.precipitation}mm/hに対して過度な表現のためスキップ: {comment.comment_text}")
                        continue
                
                # 連続雨の場合、にわか雨表現は不適切
                if is_continuous_rain:
                    temporary_rain_expressions = ["にわか雨", "一時的な雨", "急な雨", "突然の雨"]
                    if any(expr in comment.comment_text for expr in temporary_rain_expressions):
                        logger.debug(f"連続雨（{rain_hours}時間）に対して不適切な一時的表現のためスキップ: {comment.comment_text}")
                        continue
                
                return comment
        
        # 適切な雨コメントが見つからない場合、一般的な雨コメントを返す
        return comments[0] if comments else None
    
    def _find_rain_appropriate_advice_comment(
        self, 
        comments: List[PastComment],
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """雨に適したアドバイスコメントを探す"""
        rain_advice_keywords = ["傘", "雨具", "濡れ", "雨対策"]
        
        # 連続雨かどうかを判定
        is_continuous_rain = False
        rain_hours = 0
        if state and hasattr(state, 'period_forecasts') and state.period_forecasts:
            rain_hours = sum(1 for f in state.period_forecasts if f.weather == "雨")
            is_continuous_rain = rain_hours >= 4  # 4時間すべて雨
        
        for comment in comments:
            if any(keyword in comment.comment_text for keyword in rain_advice_keywords):
                # 連続雨の場合、「傘があると安心」のような表現は不適切
                if is_continuous_rain:
                    mild_umbrella_expressions = ["傘があると安心", "傘がお守り", "念のため傘", "折りたたみ傘"]
                    if any(expr in comment.comment_text for expr in mild_umbrella_expressions):
                        logger.debug(f"連続雨（{rain_hours}時間）に対して不適切な控えめな傘表現のためスキップ: {comment.comment_text}")
                        continue
                
                return comment
        
        return comments[0] if comments else None
    
    def _select_alternative_non_duplicate_pair(
        self,
        weather_comments: List[PastComment],
        advice_comments: List[PastComment],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[CommentPair]:
        """重複を回避する代替ペア選択"""
        logger.info("重複回避のための代替コメントペア選択を開始")
        
        # 複数の候補を生成して重複しないペアを探す
        weather_candidates = self.utils.prepare_weather_candidates(
            weather_comments, weather_data, self.validator, self.comment_validator, target_datetime, state
        )
        advice_candidates = self.utils.prepare_advice_candidates(
            advice_comments, weather_data, self.validator, self.comment_validator, target_datetime
        )
        
        # 上位候補から順に試行（最大10回）
        max_attempts = min(10, len(weather_candidates), len(advice_candidates))
        
        for attempt in range(max_attempts):
            try:
                # 天気コメント候補を選択（異なるものを順番に試す）
                weather_idx = attempt % len(weather_candidates)
                weather_candidate = weather_candidates[weather_idx]['comment_object']
                
                # アドバイス候補を選択
                advice_idx = attempt % len(advice_candidates)
                advice_candidate = advice_candidates[advice_idx]['comment_object']
                
                # 包括的バリデーションチェック（新しい一貫性チェック含む）
                if self.comment_validator.validate_comment_pair(weather_candidate, advice_candidate, weather_data, state):
                    logger.info(f"代替ペア選択成功 (試行{attempt+1}): 天気='{weather_candidate.comment_text}', アドバイス='{advice_candidate.comment_text}'")
                    return CommentPair(
                        weather_comment=weather_candidate,
                        advice_comment=advice_candidate,
                        similarity_score=0.8,  # 代替選択なので若干低めのスコア
                        selection_reason=f"重複回避代替選択（試行{attempt+1}回目）"
                    )
                
                logger.debug(f"試行{attempt+1}: 重複または無効 - 天気='{weather_candidate.comment_text}', アドバイス='{advice_candidate.comment_text}'")
                
            except Exception as e:
                logger.warning(f"代替選択試行{attempt+1}でエラー: {e}")
                continue
        
        logger.warning("重複しない代替ペアの選択に失敗")
        return None
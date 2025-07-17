"""一貫性バリデータ - コメントペアの一貫性を検証（リファクタリング版）"""

from __future__ import annotations
import logging
from typing import Any
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from src.data.comment_generation_state import CommentGenerationState
from src.utils.validators.duplication_checker import DuplicationChecker
from .base_validator import BaseValidator
from .weather_reality_validator import WeatherRealityValidator
from .temperature_symptom_validator import TemperatureSymptomValidator
from .tone_consistency_validator import ToneConsistencyValidator
from .umbrella_redundancy_validator import UmbrellaRedundancyValidator
from .time_temperature_validator import TimeTemperatureValidator

logger = logging.getLogger(__name__)


class ConsistencyValidator(BaseValidator):
    """天気コメントとアドバイスの一貫性を検証"""
    
    def __init__(self):
        super().__init__()
        # 各種バリデータを初期化
        self.weather_reality_validator = WeatherRealityValidator()
        self.temperature_symptom_validator = TemperatureSymptomValidator()
        self.tone_consistency_validator = ToneConsistencyValidator()
        self.umbrella_redundancy_validator = UmbrellaRedundancyValidator()
        self.time_temperature_validator = TimeTemperatureValidator()
        self.duplication_checker = DuplicationChecker()
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> tuple[bool, str]:
        """単一コメントの検証（ConsistencyValidatorでは実装しない）"""
        # ConsistencyValidatorはペアの一貫性をチェックするため、
        # 単一コメントの検証は常にTrueを返す
        return True, "単一コメントのチェックは他のバリデータで実施"
    
    def validate_comment_pair_consistency(
        self, 
        weather_comment: str, 
        advice_comment: str, 
        weather_data: WeatherForecast,
        state: CommentGenerationState | None = None
    ) -> tuple[bool, str]:
        """
        天気コメントとアドバイスの一貫性を包括的にチェック
        
        Returns:
            (is_consistent, reason): 一貫性チェック結果とその理由
        """
        # 1. 天気と現実の矛盾チェック
        weather_reality_check = self.weather_reality_validator.check_weather_reality_contradiction(
            weather_comment, weather_data
        )
        if not weather_reality_check[0]:
            return weather_reality_check
        
        # 2. 温度と症状の矛盾チェック
        temp_symptom_check = self.temperature_symptom_validator.check_temperature_symptom_contradiction(
            weather_comment, advice_comment, weather_data
        )
        if not temp_symptom_check[0]:
            return temp_symptom_check
        
        # 3. 重複・類似表現チェック
        duplication_check = self._check_content_duplication(
            weather_comment, advice_comment
        )
        if not duplication_check[0]:
            return duplication_check
        
        # 4. 矛盾する態度・トーンチェック
        tone_check = self.tone_consistency_validator.check_tone_contradiction(
            weather_comment, advice_comment, weather_data
        )
        if not tone_check[0]:
            return tone_check
        
        # 5. 傘コメントの重複チェック
        umbrella_check = self.umbrella_redundancy_validator.check_umbrella_redundancy(
            weather_comment, advice_comment, weather_data
        )
        if not umbrella_check[0]:
            return umbrella_check
        
        # 6. 時間帯と温度の矛盾チェック
        time_temp_check = self.time_temperature_validator.check_time_temperature_contradiction(
            weather_comment, advice_comment, weather_data, state
        )
        if not time_temp_check[0]:
            return time_temp_check
        
        return True, "一貫性チェック合格"
    
    def _check_content_duplication(
        self, 
        weather_comment: str, 
        advice_comment: str
    ) -> tuple[bool, str]:
        """
        内容の重複をチェック（DuplicationCheckerに委譲）
        
        Args:
            weather_comment: 天気コメント
            advice_comment: アドバイスコメント
            
        Returns:
            (is_consistent, reason): 一貫性チェック結果とその理由
        """
        # DuplicationCheckerの各種メソッドを使用
        checkers = [
            (self.duplication_checker.check_repetitive_concepts, "繰り返し概念"),
            (self.duplication_checker.check_text_similarity, "高い類似度"),
            (self.duplication_checker.check_keyword_duplication, "キーワード重複"),
            (self.duplication_checker.check_semantic_contradiction, "意味的矛盾"),
            (self.duplication_checker.check_similar_expressions, "類似表現"),
            (self.duplication_checker.check_umbrella_duplication, "傘関連重複"),
            (self.duplication_checker.check_character_similarity, "文字類似度")
        ]
        
        for checker_func, error_type in checkers:
            if checker_func(weather_comment, advice_comment):
                return False, f"{error_type}が検出されました"
        
        return True, ""
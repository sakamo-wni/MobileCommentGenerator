"""コメントバリデーションロジック（リファクタリング版）"""

from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from src.config.config import get_weather_constants
from src.constants.content_constants import SEVERE_WEATHER_PATTERNS, FORBIDDEN_PHRASES
from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.utils.weather_classifier import classify_weather_type
from src.utils.validators.pollen_validator import PollenValidator
from src.utils.validators.llm_duplication_validator import LLMDuplicationValidator

# バリデーターモジュールをインポート
from .validators.duplication_validator import DuplicationValidator
from .validators.weather_consistency_validator import WeatherConsistencyValidator
from .validators.seasonal_validator import SeasonalValidator
from .validators.yaml_config_validator import YamlConfigValidator

logger = logging.getLogger(__name__)


class CommentValidator:
    """コメントバリデーションクラス（リファクタリング版）"""
    
    def __init__(self, validator: WeatherCommentValidator, severe_config, validators=None):
        self.validator = validator
        self.severe_config = severe_config
        
        # 各種バリデーターの初期化（依存性注入パターン）
        if validators:
            self.duplication_validator = validators.get('duplication', DuplicationValidator())
            self.weather_consistency_validator = validators.get('weather_consistency', WeatherConsistencyValidator())
            self.seasonal_validator = validators.get('seasonal', SeasonalValidator())
            self.yaml_config_validator = validators.get('yaml_config', YamlConfigValidator())
            self.pollen_validator = validators.get('pollen', PollenValidator())
        else:
            self.duplication_validator = DuplicationValidator()
            self.weather_consistency_validator = WeatherConsistencyValidator()
            self.seasonal_validator = SeasonalValidator()
            self.yaml_config_validator = YamlConfigValidator()
            self.pollen_validator = PollenValidator()
        
        # LLMバリデータの初期化（APIキーが利用可能な場合のみ）
        self.llm_validator = None
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY")
        logger.debug(f"GEMINI_API_KEY: {'設定済み' if api_key else '未設定'}")
        if api_key:
            try:
                self.llm_validator = LLMDuplicationValidator(api_key)
                logger.debug("LLM重複検証バリデータを初期化しました")
            except Exception as e:
                logger.warning(f"LLMバリデータの初期化に失敗: {e}")
                self.llm_validator = None
        else:
            logger.debug("GEMINI_API_KEYが設定されていないため、LLM重複検証は無効です")
    
    def validate_comment_pair(
        self,
        weather_comment: str,
        advice_comment: str,
        past_comment: PastComment | None,
        weather_data: WeatherForecast,
        target_datetime: Any,
        state: CommentGenerationState | None = None
    ) -> dict[str, bool]:
        """コメントペアのバリデーション"""
        results = {}
        
        # 重複チェック
        is_duplicate = self.duplication_validator.is_duplicate_content(weather_comment, advice_comment)
        results["duplicate_content"] = is_duplicate
        
        # LLMによる重複チェック（利用可能な場合）
        if self.llm_validator and not is_duplicate:
            try:
                is_llm_duplicate = self.llm_validator.check_duplication(weather_comment, advice_comment)
                results["llm_duplicate"] = is_llm_duplicate
            except Exception as e:
                logger.warning(f"LLM重複チェックでエラー: {e}")
                results["llm_duplicate"] = False
        else:
            results["llm_duplicate"] = is_duplicate
        
        # 過去コメントとの重複チェック
        if past_comment:
            results["past_duplicate"] = (
                weather_comment == past_comment.weather_comment or
                advice_comment == past_comment.advice_comment
            )
        else:
            results["past_duplicate"] = False
        
        # 天気の一貫性チェック
        consistency_validator = self.weather_consistency_validator
        results["sunny_changeable"] = consistency_validator.is_sunny_weather_with_changeable_comment(weather_comment, weather_data)
        results["cloudy_sunshine"] = consistency_validator.is_cloudy_weather_with_sunshine_comment(weather_comment, weather_data)
        results["no_rain_rain_gear"] = consistency_validator.is_no_rain_weather_with_rain_comment(weather_comment, weather_data)
        results["stable_unstable"] = consistency_validator.is_stable_weather_with_unstable_comment(weather_comment, weather_data, state)
        
        # 季節の妥当性チェック
        results["inappropriate_season"] = self.seasonal_validator.is_inappropriate_seasonal_comment(
            weather_comment + " " + advice_comment, target_datetime
        )
        
        # 花粉チェック
        results["rain_pollen"] = self.is_rain_weather_with_pollen_comment(advice_comment, weather_data)
        
        # 悪天候時の適切性
        results["severe_weather_appropriate"] = self.is_severe_weather_appropriate(weather_comment, weather_data)
        
        # YAML設定による除外チェック
        results["weather_excluded"] = self.yaml_config_validator.should_exclude_weather_comment(weather_comment, weather_data)
        results["advice_excluded"] = self.yaml_config_validator.should_exclude_advice_comment(advice_comment, weather_data)
        
        return results
    
    def is_rain_weather_with_pollen_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """雨天時に花粉関連のコメントが含まれているかチェック"""
        location = getattr(weather_data, 'location_id', None)
        return self.pollen_validator.is_inappropriate_pollen_comment(
            comment_text, weather_data, weather_data.datetime, location
        )
    
    def is_severe_weather_appropriate(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """コメントが極端な天候に適切かチェック"""
        return any(pattern in comment_text for pattern in SEVERE_WEATHER_PATTERNS)
    
    def is_weather_matched(self, comment_condition: str | None, weather_description: str) -> bool:
        """コメントの天気条件と実際の天気が一致するかチェック"""
        if not comment_condition:
            return True
        
        comment_cond_lower = comment_condition.lower()
        weather_desc_lower = weather_description.lower()
        
        # 晴れの判定
        if any(word in comment_cond_lower for word in ["晴", "sunny", "clear"]):
            return any(word in weather_desc_lower for word in ["晴", "sunny", "clear"])
        
        # 曇りの判定
        if any(word in comment_cond_lower for word in ["曇", "cloud", "overcast"]):
            return any(word in weather_desc_lower for word in ["曇", "cloud", "overcast"])
        
        # 雨の判定
        if any(word in comment_cond_lower for word in ["雨", "rain", "shower"]):
            return any(word in weather_desc_lower for word in ["雨", "rain", "shower"])
        
        # その他の場合は部分一致
        return comment_cond_lower in weather_desc_lower
    
    # 以下は既存のメソッドへの委譲
    def _is_duplicate_content(self, weather_text: str, advice_text: str) -> bool:
        """重複チェック（後方互換性のため）"""
        return self.duplication_validator.is_duplicate_content(weather_text, advice_text)
    
    def is_sunny_weather_with_changeable_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """晴れの天気なのに変わりやすい天気のコメント（後方互換性のため）"""
        return self.weather_consistency_validator.is_sunny_weather_with_changeable_comment(comment_text, weather_data)
    
    def is_cloudy_weather_with_sunshine_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """曇りの天気なのに日差しが強いコメント（後方互換性のため）"""
        return self.weather_consistency_validator.is_cloudy_weather_with_sunshine_comment(comment_text, weather_data)
    
    def is_no_rain_weather_with_rain_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """雨が降らない天気なのに雨具のコメント（後方互換性のため）"""
        return self.weather_consistency_validator.is_no_rain_weather_with_rain_comment(comment_text, weather_data)
    
    def is_inappropriate_seasonal_comment(self, comment_text: str, target_datetime) -> bool:
        """季節に不適切なコメント（後方互換性のため）"""
        return self.seasonal_validator.is_inappropriate_seasonal_comment(comment_text, target_datetime)
    
    def is_stable_weather_with_unstable_comment(self, comment_text: str, weather_data: WeatherForecast, state: CommentGenerationState | None = None) -> bool:
        """安定した天気なのに不安定なコメント（後方互換性のため）"""
        return self.weather_consistency_validator.is_stable_weather_with_unstable_comment(comment_text, weather_data, state)
    
    def should_exclude_weather_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """天気コメントを除外すべきか（後方互換性のため）"""
        return self.yaml_config_validator.should_exclude_weather_comment(comment_text, weather_data)
    
    def should_exclude_advice_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """アドバイスコメントを除外すべきか（後方互換性のため）"""
        return self.yaml_config_validator.should_exclude_advice_comment(comment_text, weather_data)
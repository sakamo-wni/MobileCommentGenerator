"""
基底評価クラス

すべての評価基準の共通インターフェースを定義
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import re

from src.data.evaluation_criteria import (
    EvaluationCriteria,
    CriterionScore,
    EvaluationContext,
)
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast
from src.algorithms.evaluators.evaluator_config import EvaluatorConfig


class BaseEvaluator(ABC):
    """
    評価基準の基底クラス
    """
    
    def __init__(self, weight: float, config: Optional[EvaluatorConfig] = None):
        """
        初期化
        
        Args:
            weight: この評価基準の重み
            config: 評価器の設定（省略時はデフォルト設定を使用）
        """
        self.weight = weight
        self.config = config or EvaluatorConfig()
        
        # 互換性のため個別の属性も保持
        self.evaluation_mode = self.config.evaluation_mode
        self.enabled_checks = self.config.enabled_checks
    
    @abstractmethod
    def evaluate(
        self, 
        comment_pair: CommentPair, 
        context: EvaluationContext, 
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """
        コメントペアを評価
        
        Args:
            comment_pair: 評価対象のコメントペア
            context: 評価コンテキスト
            weather_data: 天気データ
            
        Returns:
            評価スコア
        """
        pass
    
    @property
    @abstractmethod
    def criterion(self) -> EvaluationCriteria:
        """評価基準を返す"""
        pass
    
    # 共通ユーティリティメソッド
    
    def safe_get_weather_desc(self, weather_data: WeatherForecast) -> str:
        """天気説明を安全に取得"""
        return getattr(weather_data, 'weather_description', '')
    
    def safe_get_temperature(self, weather_data: WeatherForecast) -> Optional[float]:
        """気温を安全に取得"""
        return getattr(weather_data, 'temperature', None)
    
    def safe_get_weather_condition(self, weather_data: WeatherForecast) -> str:
        """天気条件を安全に取得"""
        return getattr(weather_data, 'weather_condition', '')
    
    def has_weather_attribute(self, weather_data: WeatherForecast, attribute: str) -> bool:
        """天気データが特定の属性を持つかチェック"""
        return hasattr(weather_data, attribute)
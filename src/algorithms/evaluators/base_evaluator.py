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
)
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast


class BaseEvaluator(ABC):
    """
    評価基準の基底クラス
    """
    
    def __init__(self, weight: float, evaluation_mode: str = "relaxed", enabled_checks: List[str] = None):
        """
        初期化
        
        Args:
            weight: この評価基準の重み
            evaluation_mode: 評価モード ("strict", "moderate", "relaxed")
            enabled_checks: 有効化するチェック項目のリスト
        """
        self.weight = weight
        self.evaluation_mode = evaluation_mode
        self.enabled_checks = enabled_checks or []
    
    @abstractmethod
    def evaluate(
        self, 
        comment_pair: CommentPair, 
        context: Any, 
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
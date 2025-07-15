"""
評価器の設定クラス

各評価器で使用する設定を一元管理
"""

from dataclasses import dataclass, field
from typing import Any

@dataclass
class EvaluatorConfig:
    """
    評価器の共通設定
    """
    evaluation_mode: str = "relaxed"
    enabled_checks: list[str] = field(default_factory=lambda: ["extreme_inappropriate"])
    
    # パターン設定
    inappropriate_patterns: list[str] = field(default_factory=list)
    contradiction_patterns: list[dict[str, list[str]]] = field(default_factory=list)
    positive_expressions: list[str] = field(default_factory=list)
    engagement_elements: list[str] = field(default_factory=list)
    
    # 閾値設定
    thresholds: dict[str, float] = field(default_factory=lambda: {
        "total_score": 0.3,
        "appropriateness": 0.2,
        "consistency": 0.2
    })
    
    @classmethod
    def from_config_loader(cls, config_loader, evaluation_mode: str) -> 'EvaluatorConfig':
        """
        EvaluationConfigLoaderから設定を作成
        """
        mode_config = config_loader.get_mode_config(evaluation_mode)
        
        return cls(
            evaluation_mode=evaluation_mode,
            enabled_checks=mode_config.get("enabled_checks", ["extreme_inappropriate"]),
            inappropriate_patterns=config_loader.get_inappropriate_patterns(evaluation_mode),
            contradiction_patterns=config_loader.get_contradiction_patterns(evaluation_mode),
            positive_expressions=config_loader.get_positive_expressions(),
            engagement_elements=config_loader.get_engagement_elements(),
            thresholds=mode_config.get("thresholds", {
                "total_score": 0.3,
                "appropriateness": 0.2,
                "consistency": 0.2
            })
        )
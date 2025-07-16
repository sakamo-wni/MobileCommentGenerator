"""
評価基準と結果のデータクラス

コメント候補の評価に使用するデータ構造
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
from enum import Enum


class EvaluationCriteria(Enum):
    """評価基準の種類"""

    RELEVANCE = "relevance"  # 関連性
    CREATIVITY = "creativity"  # 創造性
    NATURALNESS = "naturalness"  # 自然さ
    APPROPRIATENESS = "appropriateness"  # 適切性
    ENGAGEMENT = "engagement"  # エンゲージメント
    CLARITY = "clarity"  # 明確性
    CONSISTENCY = "consistency"  # 一貫性
    ORIGINALITY = "originality"  # オリジナリティ


@dataclass
class CriterionScore:
    """
    個別評価基準のスコア

    Attributes:
        criterion: 評価基準
        score: スコア (0.0-1.0)
        weight: 重み (0.0-1.0)
        reason: スコアの理由
        details: 詳細情報
    """

    criterion: EvaluationCriteria
    score: float
    weight: float = 1.0
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初期化後の検証"""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"スコアは0.0-1.0の範囲である必要があります: {self.score}")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"重みは0.0-1.0の範囲である必要があります: {self.weight}")

    @property
    def weighted_score(self) -> float:
        """重み付きスコアを取得"""
        return self.score * self.weight

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "criterion": self.criterion.value,
            "score": self.score,
            "weight": self.weight,
            "weighted_score": self.weighted_score,
            "reason": self.reason,
            "details": self.details,
        }


@dataclass
class EvaluationResult:
    """
    評価結果

    Attributes:
        is_valid: 検証結果（合格/不合格）
        total_score: 総合スコア
        criterion_scores: 各基準のスコア
        passed_criteria: 合格した基準
        failed_criteria: 不合格の基準
        suggestions: 改善提案
        metadata: メタデータ
    """

    is_valid: bool
    total_score: float
    criterion_scores: list[CriterionScore]
    passed_criteria: list[EvaluationCriteria] = field(default_factory=list)
    failed_criteria: list[EvaluationCriteria] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初期化後の処理"""
        # 合格/不合格基準の自動分類
        if not self.passed_criteria and not self.failed_criteria:
            for score in self.criterion_scores:
                if score.score >= 0.7:  # 閾値
                    self.passed_criteria.append(score.criterion)
                else:
                    self.failed_criteria.append(score.criterion)

    @property
    def pass_rate(self) -> float:
        """合格率を計算"""
        total = len(self.passed_criteria) + len(self.failed_criteria)
        return len(self.passed_criteria) / total if total > 0 else 0.0

    @property
    def average_score(self) -> float:
        """平均スコアを計算"""
        if not self.criterion_scores:
            return 0.0
        return sum(s.score for s in self.criterion_scores) / len(self.criterion_scores)

    def get_score_by_criterion(self, criterion: EvaluationCriteria) -> CriterionScore | None:
        """特定の基準のスコアを取得"""
        for score in self.criterion_scores:
            if score.criterion == criterion:
                return score
        return None

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "is_valid": self.is_valid,
            "total_score": self.total_score,
            "average_score": self.average_score,
            "pass_rate": self.pass_rate,
            "criterion_scores": [s.to_dict() for s in self.criterion_scores],
            "passed_criteria": [c.value for c in self.passed_criteria],
            "failed_criteria": [c.value for c in self.failed_criteria],
            "suggestions": self.suggestions,
            "metadata": self.metadata,
        }


@dataclass
class EvaluationContext:
    """
    評価コンテキスト

    Attributes:
        weather_condition: 天気条件
        location: 地点
        target_datetime: 対象日時
        user_preferences: ユーザー設定
        history: 過去の評価履歴
        weather_stability: 天気の安定性 ('stable' または 'unstable')
    """

    weather_condition: str
    location: str
    target_datetime: datetime
    user_preferences: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    weather_stability: str | None = None

    def get_preference(self, key: str, default: Any = None) -> Any:
        """ユーザー設定を取得"""
        return self.user_preferences.get(key, default)

    def add_history(self, evaluation: dict[str, Any]):
        """評価履歴を追加"""
        self.history.append({"timestamp": datetime.now().isoformat(), "evaluation": evaluation})

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "weather_condition": self.weather_condition,
            "location": self.location,
            "target_datetime": self.target_datetime.isoformat(),
            "user_preferences": self.user_preferences,
            "history_count": len(self.history),
        }


# デフォルト評価重み（緩和版）
DEFAULT_CRITERION_WEIGHTS = {
    EvaluationCriteria.APPROPRIATENESS: 0.40,  # 不適切表現の排除を最重視
    EvaluationCriteria.CONSISTENCY: 0.25,     # 矛盾・重複チェックを重視
    EvaluationCriteria.RELEVANCE: 0.20,       # 天気との関連性（緩く評価）
    EvaluationCriteria.NATURALNESS: 0.10,     # 自然さ（基本的なチェックのみ）
    EvaluationCriteria.CLARITY: 0.03,         # 明確性（緩く評価）
    EvaluationCriteria.ENGAGEMENT: 0.01,      # エンゲージメント（最小限）
    EvaluationCriteria.CREATIVITY: 0.005,     # 創造性（最小限）
    EvaluationCriteria.ORIGINALITY: 0.005,    # オリジナリティ（最小限）
}


def create_default_weights() -> dict[EvaluationCriteria, float]:
    """デフォルトの評価重みを作成"""
    return DEFAULT_CRITERION_WEIGHTS.copy()

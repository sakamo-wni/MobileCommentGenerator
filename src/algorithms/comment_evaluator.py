"""
コメント候補評価エンジン

コメントの品質を多角的に評価する機能
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import re
import logging
from datetime import datetime

from src.data.evaluation_criteria import (
    EvaluationCriteria,
    CriterionScore,
    EvaluationResult,
    EvaluationContext,
    DEFAULT_CRITERION_WEIGHTS,
)
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast
from src.config.evaluation_config_loader import EvaluationConfigLoader

# 各評価モジュールをインポート
from src.algorithms.evaluators import (
    RelevanceEvaluator,
    CreativityEvaluator,
    NaturalnessEvaluator,
    AppropriatenessEvaluator,
    EngagementEvaluator,
    ClarityEvaluator,
    ConsistencyEvaluator,
    OriginalityEvaluator,
)

logger = logging.getLogger(__name__)


class CommentEvaluator:
    """
    コメント候補を評価するクラス
    """

    def __init__(
        self, 
        weights: Optional[Dict[EvaluationCriteria, float]] = None,
        evaluation_mode: str = "relaxed"
    ):
        """
        初期化

        Args:
            weights: 評価基準の重み（Noneの場合はデフォルト使用）
            evaluation_mode: 評価モード ("strict", "moderate", "relaxed")
        """
        self.weights = weights or DEFAULT_CRITERION_WEIGHTS.copy()
        self.evaluation_mode = evaluation_mode
        
        # 設定ローダーを初期化
        self.config_loader = EvaluationConfigLoader()
        
        # モード別設定を取得
        self.mode_config = self.config_loader.get_mode_config(evaluation_mode)
        self.thresholds = self.mode_config.get("thresholds", {
            "total_score": 0.3,
            "appropriateness": 0.2, 
            "consistency": 0.2
        })
        self.enabled_checks = self.mode_config.get("enabled_checks", ["extreme_inappropriate"])
        
        # パターンを設定から読み込む
        self.inappropriate_patterns = self.config_loader.get_inappropriate_patterns(evaluation_mode)
        self.contradiction_patterns = self.config_loader.get_contradiction_patterns(evaluation_mode)
        self.positive_expressions = self.config_loader.get_positive_expressions()
        self.engagement_elements = self.config_loader.get_engagement_elements()
        
        # 各評価器を初期化
        self._initialize_evaluators()
        
        logger.info(f"CommentEvaluator initialized with mode: {evaluation_mode}")

    def _initialize_evaluators(self):
        """各評価器を初期化"""
        self.evaluators = {
            EvaluationCriteria.RELEVANCE: RelevanceEvaluator(
                weight=self.weights[EvaluationCriteria.RELEVANCE],
                evaluation_mode=self.evaluation_mode,
                enabled_checks=self.enabled_checks
            ),
            EvaluationCriteria.CREATIVITY: CreativityEvaluator(
                weight=self.weights[EvaluationCriteria.CREATIVITY],
                evaluation_mode=self.evaluation_mode,
                enabled_checks=self.enabled_checks
            ),
            EvaluationCriteria.NATURALNESS: NaturalnessEvaluator(
                weight=self.weights[EvaluationCriteria.NATURALNESS],
                evaluation_mode=self.evaluation_mode,
                enabled_checks=self.enabled_checks
            ),
            EvaluationCriteria.APPROPRIATENESS: AppropriatenessEvaluator(
                weight=self.weights[EvaluationCriteria.APPROPRIATENESS],
                evaluation_mode=self.evaluation_mode,
                enabled_checks=self.enabled_checks,
                inappropriate_patterns=self.inappropriate_patterns
            ),
            EvaluationCriteria.ENGAGEMENT: EngagementEvaluator(
                weight=self.weights[EvaluationCriteria.ENGAGEMENT],
                evaluation_mode=self.evaluation_mode,
                enabled_checks=self.enabled_checks,
                engagement_elements=self.engagement_elements,
                positive_expressions=self.positive_expressions
            ),
            EvaluationCriteria.CLARITY: ClarityEvaluator(
                weight=self.weights[EvaluationCriteria.CLARITY],
                evaluation_mode=self.evaluation_mode,
                enabled_checks=self.enabled_checks
            ),
            EvaluationCriteria.CONSISTENCY: ConsistencyEvaluator(
                weight=self.weights[EvaluationCriteria.CONSISTENCY],
                evaluation_mode=self.evaluation_mode,
                enabled_checks=self.enabled_checks,
                contradiction_patterns=self.contradiction_patterns
            ),
            EvaluationCriteria.ORIGINALITY: OriginalityEvaluator(
                weight=self.weights[EvaluationCriteria.ORIGINALITY],
                evaluation_mode=self.evaluation_mode,
                enabled_checks=self.enabled_checks
            ),
        }

    def evaluate_comment_pair(
        self, comment_pair: CommentPair, context: EvaluationContext, weather_data: WeatherForecast
    ) -> EvaluationResult:
        """
        コメントペアを評価

        Args:
            comment_pair: 評価対象のコメントペア
            context: 評価コンテキスト
            weather_data: 天気データ

        Returns:
            評価結果
        """
        criterion_scores = []

        # 各評価基準でスコアリング
        for criterion in EvaluationCriteria:
            score = self._evaluate_criterion(criterion, comment_pair, context, weather_data)
            criterion_scores.append(score)

        # 総合スコアを計算
        total_score = self._calculate_total_score(criterion_scores)

        # 検証結果を判定
        is_valid = self._determine_validity(criterion_scores, total_score)

        # 改善提案を生成
        suggestions = self._generate_suggestions(criterion_scores, comment_pair)

        # 評価結果を作成
        result = EvaluationResult(
            is_valid=is_valid,
            total_score=total_score,
            criterion_scores=criterion_scores,
            suggestions=suggestions,
            metadata={
                "evaluated_at": datetime.now().isoformat(),
                "weather_condition": weather_data.weather_description,
                "location": context.location,
            },
        )

        return result

    def _evaluate_criterion(
        self,
        criterion: EvaluationCriteria,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast,
    ) -> CriterionScore:
        """個別の評価基準でスコアリング"""
        evaluator = self.evaluators.get(criterion)
        if not evaluator:
            logger.warning(f"評価基準 {criterion} の評価器が見つかりません")
            return CriterionScore(
                criterion=criterion,
                score=0.5,
                weight=self.weights.get(criterion, 1.0),
                reason="評価器が未実装",
            )

        return evaluator.evaluate(comment_pair, context, weather_data)

    # ヘルパーメソッド

    def _calculate_total_score(self, criterion_scores: List[CriterionScore]) -> float:
        """総合スコアを計算"""
        total_weighted = sum(score.weighted_score for score in criterion_scores)
        total_weight = sum(score.weight for score in criterion_scores)
        return total_weighted / total_weight if total_weight > 0 else 0.0

    def _determine_validity(
        self, criterion_scores: List[CriterionScore], total_score: float
    ) -> bool:
        """検証結果を判定（モードに応じた基準）"""
        # 総合スコアが閾値以上
        if total_score < self.thresholds.get("total_score", 0.3):
            return False

        # 最重要基準: 適切性チェック
        appropriateness_score = next(
            (s for s in criterion_scores if s.criterion == EvaluationCriteria.APPROPRIATENESS), 
            None
        )
        if appropriateness_score and appropriateness_score.score < self.thresholds.get("appropriateness", 0.2):
            return False

        # 一貫性チェック
        consistency_score = next(
            (s for s in criterion_scores if s.criterion == EvaluationCriteria.CONSISTENCY), 
            None
        )
        if consistency_score and consistency_score.score < self.thresholds.get("consistency", 0.2):
            return False

        return True

    def _generate_suggestions(
        self, criterion_scores: List[CriterionScore], comment_pair: CommentPair
    ) -> List[str]:
        """改善提案を生成"""
        suggestions = []

        # 低スコアの基準に対する提案
        for score in criterion_scores:
            if score.score < 0.5:
                suggestion = self._get_suggestion_for_criterion(
                    score.criterion, score.score, comment_pair
                )
                if suggestion:
                    suggestions.append(suggestion)

        return suggestions

    def _get_suggestion_for_criterion(
        self, criterion: EvaluationCriteria, score: float, comment_pair: CommentPair
    ) -> Optional[str]:
        """基準別の改善提案"""
        suggestions_map = {
            EvaluationCriteria.RELEVANCE: "天気条件や気温により適した表現を使用してください",
            EvaluationCriteria.CREATIVITY: "比喩や感情表現を加えてより創造的にしてください",
            EvaluationCriteria.NATURALNESS: "より自然な日本語表現を心がけてください",
            EvaluationCriteria.APPROPRIATENESS: "不適切な表現を避け、ポジティブな内容にしてください",
            EvaluationCriteria.ENGAGEMENT: "親しみやすい表現や装飾を追加してください",
            EvaluationCriteria.CLARITY: "より具体的で明確な表現を使用してください",
            EvaluationCriteria.CONSISTENCY: "天気コメントとアドバイスのトーンを統一してください",
            EvaluationCriteria.ORIGINALITY: "より独自性のある表現を考えてください",
        }

        return suggestions_map.get(criterion)
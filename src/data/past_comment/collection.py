"""
過去コメントコレクション

過去コメントの集合を管理し、フィルタリング・分析機能を提供
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from src.data.past_comment.models import PastComment, CommentType
from src.data.past_comment.similarity import SimilarityCalculator
from src.data.past_comment.filters import CommentFilter


class PastCommentCollection:
    """過去コメントのコレクションを管理するクラス

    Attributes:
        comments: PastCommentインスタンスのリスト
    """

    def __init__(self, comments: Optional[List[PastComment]] = None):
        """コンストラクタ

        Args:
            comments: 初期コメントリスト
        """
        self.comments = comments or []
        self._filter = CommentFilter()
        self._similarity_calculator = SimilarityCalculator()

    def filter_by_location(
        self, locations: List[str], fuzzy: bool = True
    ) -> "PastCommentCollection":
        """地点名でフィルタリング

        Args:
            locations: 対象地点名のリスト
            fuzzy: あいまい一致を許可するか

        Returns:
            PastCommentCollection: フィルタリングされた新しいコレクション
        """
        filtered_comments = self._filter.filter_by_location(self.comments, locations, fuzzy)
        return PastCommentCollection(filtered_comments)

    def filter_by_weather_condition(
        self, weather_conditions: List[str], fuzzy: bool = True
    ) -> "PastCommentCollection":
        """天気条件でフィルタリング

        Args:
            weather_conditions: 対象天気条件のリスト
            fuzzy: あいまい一致を許可するか

        Returns:
            PastCommentCollection: フィルタリングされた新しいコレクション
        """
        filtered_comments = self._filter.filter_by_weather_condition(
            self.comments, weather_conditions, fuzzy
        )
        return PastCommentCollection(filtered_comments)

    def filter_by_comment_type(self, comment_type: CommentType) -> "PastCommentCollection":
        """コメントタイプでフィルタリング

        Args:
            comment_type: 対象のコメントタイプ

        Returns:
            PastCommentCollection: フィルタリングされた新しいコレクション
        """
        filtered_comments = self._filter.filter_by_comment_type(self.comments, comment_type)
        return PastCommentCollection(filtered_comments)

    def filter_by_type(self, comment_type: CommentType) -> "PastCommentCollection":
        """filter_by_comment_typeのエイリアス（後方互換性のため）

        Args:
            comment_type: 対象のコメントタイプ

        Returns:
            PastCommentCollection: フィルタリングされた新しいコレクション
        """
        return self.filter_by_comment_type(comment_type)

    def get_similar_comments(
        self,
        target_weather: str,
        target_temp: Optional[float] = None,
        target_humidity: Optional[float] = None,
        target_datetime: Optional[datetime] = None,
        threshold: float = 0.6,
        limit: Optional[int] = None,
    ) -> List[PastComment]:
        """類似度の高いコメントを取得

        Args:
            target_weather: 対象の天気条件
            target_temp: 対象の気温
            target_humidity: 対象の湿度
            target_datetime: 対象の日時
            threshold: 類似度の閾値（0.0-1.0）
            limit: 取得する最大件数

        Returns:
            List[PastComment]: 類似度の高い順にソートされたコメントリスト
        """
        scored_comments = []
        for comment in self.comments:
            score = self._similarity_calculator.calculate_similarity_score(
                comment, target_weather, target_temp, target_humidity, target_datetime
            )
            if score >= threshold:
                scored_comments.append((score, comment))

        # スコアの降順でソート
        scored_comments.sort(key=lambda x: x[0], reverse=True)

        # limitが指定されている場合は上位のみ返す
        if limit:
            return [comment for _, comment in scored_comments[:limit]]
        else:
            return [comment for _, comment in scored_comments]

    def get_by_type_and_similarity(
        self,
        comment_type: CommentType,
        target_weather: str,
        target_temp: Optional[float] = None,
        target_humidity: Optional[float] = None,
        target_datetime: Optional[datetime] = None,
        threshold: float = 0.6,
        limit: Optional[int] = None,
    ) -> List[PastComment]:
        """コメントタイプでフィルタリングし、類似度の高いコメントを取得

        Args:
            comment_type: 対象のコメントタイプ
            target_weather: 対象の天気条件
            target_temp: 対象の気温
            target_humidity: 対象の湿度
            target_datetime: 対象の日時
            threshold: 類似度の閾値（0.0-1.0）
            limit: 取得する最大件数

        Returns:
            List[PastComment]: 類似度の高い順にソートされたコメントリスト
        """
        # まずコメントタイプでフィルタリング
        filtered_collection = self.filter_by_comment_type(comment_type)

        # 類似度の高いコメントを取得
        return filtered_collection.get_similar_comments(
            target_weather, target_temp, target_humidity, target_datetime, threshold, limit
        )

    def get_statistics(self) -> Dict[str, Any]:
        """コレクションの統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        if not self.comments:
            return {
                "total_count": 0,
                "by_type": {},
                "by_location": {},
                "by_weather": {},
                "temperature_stats": {},
            }

        # タイプ別カウント
        type_counts = {}
        for comment in self.comments:
            type_name = comment.comment_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # 地点別カウント
        location_counts = {}
        for comment in self.comments:
            location_counts[comment.location] = location_counts.get(comment.location, 0) + 1

        # 天気別カウント
        weather_counts = {}
        for comment in self.comments:
            weather_counts[comment.weather_condition] = (
                weather_counts.get(comment.weather_condition, 0) + 1
            )

        # 気温統計
        temperatures = [c.temperature for c in self.comments if c.temperature is not None]
        temp_stats = {}
        if temperatures:
            temp_stats = {
                "min": min(temperatures),
                "max": max(temperatures),
                "avg": sum(temperatures) / len(temperatures),
                "count": len(temperatures),
            }

        return {
            "total_count": len(self.comments),
            "by_type": type_counts,
            "by_location": location_counts,
            "by_weather": weather_counts,
            "temperature_stats": temp_stats,
        }

    def to_dict(self) -> Dict[str, Any]:
        """コレクション全体を辞書形式に変換

        Returns:
            Dict[str, Any]: コレクションの辞書表現
        """
        return {
            "comments": [comment.to_dict() for comment in self.comments],
            "count": len(self.comments),
            "statistics": self.get_statistics(),
        }
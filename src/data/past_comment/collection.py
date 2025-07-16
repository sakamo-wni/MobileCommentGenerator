"""過去コメントのコレクション管理"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from collections import Counter

from .models import PastComment, CommentType
from .similarity import calculate_similarity_score


@dataclass
class PastCommentCollection:
    """過去コメントのコレクションを管理するクラス
    
    複数の過去コメントをまとめて扱い、フィルタリングや統計情報の取得を行う
    """
    
    comments: list[PastComment] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        return len(self.comments)
    
    def __iter__(self):
        return iter(self.comments)
    
    def filter_by_location(
        self, 
        location: str, 
        fuzzy: bool = False
    ) -> "PastCommentCollection":
        """地点名でフィルタリング
        
        Args:
            location: 地点名
            fuzzy: あいまい検索を有効にするか
            
        Returns:
            フィルタリングされたコレクション
        """
        if fuzzy:
            # あいまい検索: 部分一致を許可
            filtered = [
                c for c in self.comments 
                if location.lower() in c.location.lower() 
                or c.location.lower() in location.lower()
            ]
        else:
            # 完全一致
            filtered = [
                c for c in self.comments 
                if c.location.lower() == location.lower()
            ]
        
        return PastCommentCollection(comments=filtered, metadata=self.metadata.copy())
    
    def filter_by_weather_condition(
        self, 
        condition: str, 
        fuzzy: bool = True
    ) -> "PastCommentCollection":
        """天気状況でフィルタリング
        
        Args:
            condition: 天気状況
            fuzzy: あいまい検索を有効にするか
            
        Returns:
            フィルタリングされたコレクション
        """
        from .similarity import matches_weather_condition
        
        filtered = [
            c for c in self.comments
            if matches_weather_condition(c.weather_condition, condition, fuzzy)
        ]
        
        return PastCommentCollection(comments=filtered, metadata=self.metadata.copy())
    
    def filter_by_comment_type(self, comment_type: CommentType) -> "PastCommentCollection":
        """コメントタイプでフィルタリング
        
        Args:
            comment_type: コメントタイプ
            
        Returns:
            フィルタリングされたコレクション
        """
        filtered = [
            c for c in self.comments
            if c.comment_type == comment_type
        ]
        
        return PastCommentCollection(comments=filtered, metadata=self.metadata.copy())
    
    def filter_by_type(self, comment_type: CommentType) -> "PastCommentCollection":
        """コメントタイプでフィルタリング（エイリアス）"""
        return self.filter_by_comment_type(comment_type)
    
    def get_similar_comments(
        self,
        weather_condition: str,
        temperature: float | None = None,
        humidity: float | None = None,
        threshold: float = 0.7,
        limit: int | None = None,
    ) -> list[tuple[PastComment, float]]:
        """類似コメントを取得
        
        Args:
            weather_condition: 対象の天気状況
            temperature: 対象の気温
            humidity: 対象の湿度
            threshold: 類似度の閾値（0.0〜1.0）
            limit: 返却する最大件数
            
        Returns:
            (コメント, 類似度スコア)のタプルのリスト
        """
        scored_comments = []
        
        for comment in self.comments:
            score = calculate_similarity_score(
                comment.weather_condition,
                comment.temperature,
                comment.humidity,
                weather_condition,
                temperature,
                humidity,
            )
            
            if score >= threshold:
                scored_comments.append((comment, score))
        
        # スコアの降順でソート
        scored_comments.sort(key=lambda x: x[1], reverse=True)
        
        if limit:
            return scored_comments[:limit]
        
        return scored_comments
    
    def get_by_type_and_similarity(
        self,
        comment_type: CommentType,
        weather_condition: str,
        temperature: float | None = None,
        limit: int = 5,
    ) -> list[PastComment]:
        """タイプと類似度でコメントを取得
        
        Args:
            comment_type: コメントタイプ
            weather_condition: 対象の天気状況
            temperature: 対象の気温
            limit: 返却する最大件数
            
        Returns:
            類似度の高い順のコメントリスト
        """
        # タイプでフィルタリング
        filtered = self.filter_by_comment_type(comment_type)
        
        # 類似コメントを取得
        similar_comments = filtered.get_similar_comments(
            weather_condition,
            temperature,
            threshold=0.0,  # 全てのスコアを取得
            limit=limit,
        )
        
        # コメントのみを返す
        return [comment for comment, _ in similar_comments]
    
    def get_statistics(self) -> dict[str, Any]:
        """コレクションの統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        if not self.comments:
            return {
                "total_count": 0,
                "location_count": {},
                "weather_condition_count": {},
                "comment_type_count": {},
                "average_length": 0,
                "temperature_range": (None, None),
            }
        
        # 各種カウント
        location_count = Counter(c.location for c in self.comments)
        weather_count = Counter(c.weather_condition for c in self.comments)
        type_count = Counter(c.comment_type.value for c in self.comments)
        
        # 文字数統計
        lengths = [c.get_character_count() for c in self.comments]
        avg_length = sum(lengths) / len(lengths)
        
        # 気温範囲
        temps = [c.temperature for c in self.comments if c.temperature is not None]
        temp_range = (min(temps), max(temps)) if temps else (None, None)
        
        return {
            "total_count": len(self.comments),
            "location_count": dict(location_count),
            "weather_condition_count": dict(weather_count),
            "comment_type_count": dict(type_count),
            "average_length": avg_length,
            "temperature_range": temp_range,
            "metadata": self.metadata,
        }
    
    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "comments": [c.to_dict() for c in self.comments],
            "metadata": self.metadata,
            "statistics": self.get_statistics(),
        }
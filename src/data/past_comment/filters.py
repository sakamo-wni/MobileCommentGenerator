"""
フィルタリング機能モジュール

過去コメントのフィルタリング関連機能
"""

from typing import List, Optional
from datetime import datetime, timedelta

from src.data.past_comment.models import PastComment, CommentType
from src.data.past_comment.similarity import SimilarityCalculator


class CommentFilter:
    """コメントのフィルタリング機能を提供するクラス"""
    
    def __init__(self):
        self.similarity_calculator = SimilarityCalculator()
    
    def filter_by_location(
        self, comments: List[PastComment], locations: List[str], fuzzy: bool = True
    ) -> List[PastComment]:
        """地点名でフィルタリング

        Args:
            comments: フィルタリング対象のコメントリスト
            locations: 対象地点名のリスト
            fuzzy: あいまい一致を許可するか

        Returns:
            List[PastComment]: フィルタリングされたコメントリスト
        """
        if not locations:
            return comments

        filtered = []
        for comment in comments:
            if fuzzy:
                # あいまい一致: 部分一致でOK
                if any(
                    loc.lower() in comment.location.lower() or comment.location.lower() in loc.lower()
                    for loc in locations
                ):
                    filtered.append(comment)
            else:
                # 完全一致
                if comment.location in locations:
                    filtered.append(comment)

        return filtered

    def filter_by_weather_condition(
        self, comments: List[PastComment], weather_conditions: List[str], fuzzy: bool = True
    ) -> List[PastComment]:
        """天気条件でフィルタリング

        Args:
            comments: フィルタリング対象のコメントリスト
            weather_conditions: 対象天気条件のリスト
            fuzzy: あいまい一致を許可するか

        Returns:
            List[PastComment]: フィルタリングされたコメントリスト
        """
        if not weather_conditions:
            return comments

        filtered = []
        for comment in comments:
            for condition in weather_conditions:
                if self.similarity_calculator.matches_weather_condition(comment, condition, fuzzy):
                    filtered.append(comment)
                    break

        return filtered

    def filter_by_comment_type(
        self, comments: List[PastComment], comment_type: CommentType
    ) -> List[PastComment]:
        """コメントタイプでフィルタリング

        Args:
            comments: フィルタリング対象のコメントリスト
            comment_type: 対象のコメントタイプ

        Returns:
            List[PastComment]: フィルタリングされたコメントリスト
        """
        return [comment for comment in comments if comment.comment_type == comment_type]

    def filter_by_date_range(
        self, comments: List[PastComment], start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[PastComment]:
        """日付範囲でフィルタリング

        Args:
            comments: フィルタリング対象のコメントリスト
            start_date: 開始日時（含む）
            end_date: 終了日時（含む）

        Returns:
            List[PastComment]: フィルタリングされたコメントリスト
        """
        filtered = []
        for comment in comments:
            if start_date and comment.datetime < start_date:
                continue
            if end_date and comment.datetime > end_date:
                continue
            filtered.append(comment)
        
        return filtered

    def filter_by_temperature_range(
        self, comments: List[PastComment], min_temp: Optional[float] = None, max_temp: Optional[float] = None
    ) -> List[PastComment]:
        """気温範囲でフィルタリング

        Args:
            comments: フィルタリング対象のコメントリスト
            min_temp: 最低気温（含む）
            max_temp: 最高気温（含む）

        Returns:
            List[PastComment]: フィルタリングされたコメントリスト
        """
        filtered = []
        for comment in comments:
            if comment.temperature is None:
                continue
            if min_temp is not None and comment.temperature < min_temp:
                continue
            if max_temp is not None and comment.temperature > max_temp:
                continue
            filtered.append(comment)
        
        return filtered

    def filter_by_text_contains(
        self, comments: List[PastComment], keywords: List[str], case_sensitive: bool = False
    ) -> List[PastComment]:
        """テキストに特定のキーワードを含むコメントをフィルタリング

        Args:
            comments: フィルタリング対象のコメントリスト
            keywords: 検索キーワードのリスト
            case_sensitive: 大文字小文字を区別するか

        Returns:
            List[PastComment]: フィルタリングされたコメントリスト
        """
        if not keywords:
            return comments

        filtered = []
        for comment in comments:
            comment_text = comment.comment_text if case_sensitive else comment.comment_text.lower()
            for keyword in keywords:
                search_keyword = keyword if case_sensitive else keyword.lower()
                if search_keyword in comment_text:
                    filtered.append(comment)
                    break
        
        return filtered

    def filter_valid_comments(self, comments: List[PastComment]) -> List[PastComment]:
        """有効なコメントのみをフィルタリング

        Args:
            comments: フィルタリング対象のコメントリスト

        Returns:
            List[PastComment]: 有効なコメントのリスト
        """
        return [comment for comment in comments if comment.is_valid()]

    def filter_within_length_limit(
        self, comments: List[PastComment], max_length: int = 15
    ) -> List[PastComment]:
        """文字数制限内のコメントをフィルタリング

        Args:
            comments: フィルタリング対象のコメントリスト
            max_length: 最大文字数

        Returns:
            List[PastComment]: 文字数制限内のコメントリスト
        """
        return [comment for comment in comments if comment.is_within_length_limit(max_length)]
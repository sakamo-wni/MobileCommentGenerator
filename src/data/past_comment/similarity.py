"""
類似度計算モジュール

過去コメントと現在の天気条件の類似度を計算する機能
"""

from typing import Optional
from datetime import datetime

from src.data.past_comment.models import PastComment


class SimilarityCalculator:
    """コメントの類似度を計算するクラス"""
    
    @staticmethod
    def calculate_similarity_score(
        comment: PastComment,
        target_weather: str,
        target_temp: Optional[float] = None,
        target_humidity: Optional[float] = None,
        target_datetime: Optional[datetime] = None,
    ) -> float:
        """現在の天気条件との類似度スコアを計算

        Args:
            comment: 評価対象のコメント
            target_weather: 対象の天気条件
            target_temp: 対象の気温
            target_humidity: 対象の湿度
            target_datetime: 対象の日時

        Returns:
            float: 類似度スコア (0.0-1.0)
        """
        score = 0.0
        weight_sum = 0.0

        # 天気条件の類似度（最重要: 重み0.4）
        if comment.matches_weather_condition(target_weather):
            score += 0.4
        weight_sum += 0.4

        # 気温の類似度（重み0.3）
        if target_temp is not None and comment.temperature is not None:
            temp_diff = abs(comment.temperature - target_temp)
            # 温度差が小さいほど高スコア
            temp_score = max(0, 1 - temp_diff / 20)  # 20度差で0になる
            score += temp_score * 0.3
            weight_sum += 0.3

        # 湿度の類似度（重み0.1）
        if target_humidity is not None and comment.humidity is not None:
            humidity_diff = abs(comment.humidity - target_humidity)
            humidity_score = max(0, 1 - humidity_diff / 50)  # 50%差で0になる
            score += humidity_score * 0.1
            weight_sum += 0.1

        # 時刻の類似度（重み0.1）
        if target_datetime is not None:
            hour_diff = abs(comment.datetime.hour - target_datetime.hour)
            # 時刻の差を0-12の範囲に正規化
            if hour_diff > 12:
                hour_diff = 24 - hour_diff
            time_score = max(0, 1 - hour_diff / 12)
            score += time_score * 0.1
            weight_sum += 0.1

        # 月の類似度（重み0.1）
        if target_datetime is not None:
            month_diff = abs(comment.datetime.month - target_datetime.month)
            # 月の差を0-6の範囲に正規化
            if month_diff > 6:
                month_diff = 12 - month_diff
            month_score = max(0, 1 - month_diff / 6)
            score += month_score * 0.1
            weight_sum += 0.1

        # 重みの合計で正規化
        if weight_sum > 0:
            return score / weight_sum
        else:
            return 0.0
    
    @staticmethod
    def matches_weather_condition(comment: PastComment, target_condition: str, fuzzy: bool = True) -> bool:
        """天気条件が一致するかチェック

        Args:
            comment: チェック対象のコメント
            target_condition: 対象の天気条件
            fuzzy: あいまい一致を許可するか

        Returns:
            bool: 一致する場合True
        """
        if not fuzzy:
            return comment.weather_condition == target_condition

        # あいまい一致のための正規化
        comment_weather = comment.weather_condition.lower().strip()
        target_weather = target_condition.lower().strip()

        # 完全一致
        if comment_weather == target_weather:
            return True

        # 部分一致チェック
        # 例: "晴れ" と "晴れ時々曇り" をマッチさせる
        weather_keywords = ["晴", "曇", "雨", "雪"]
        for keyword in weather_keywords:
            if keyword in comment_weather and keyword in target_weather:
                return True

        # 類似パターンの定義
        similar_patterns = [
            (["快晴", "晴天"], ["晴れ", "晴"]),
            (["小雨", "弱い雨"], ["雨", "降水"]),
            (["大雨", "豪雨"], ["雨", "強い雨"]),
            (["曇り", "くもり"], ["曇", "薄曇"]),
        ]

        for pattern_group in similar_patterns:
            for patterns in pattern_group:
                if any(p in comment_weather for p in patterns) and any(
                    p in target_weather for p in patterns
                ):
                    return True

        return False
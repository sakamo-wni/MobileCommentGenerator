"""
コメント類似度計算エンジン

天気条件やセマンティック類似度を計算する機能
"""

from __future__ import annotations
import math
from typing import Any
from datetime import datetime
import logging

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment

logger = logging.getLogger(__name__)


class CommentSimilarityCalculator:
    """
    コメントの類似度を計算するクラス
    """

    # 天気条件の類似度マッピング
    WEATHER_SIMILARITY_MATRIX = {
        "晴れ": {"晴れ": 1.0, "曇り": 0.5, "雨": 0.2, "雪": 0.1},
        "曇り": {"晴れ": 0.5, "曇り": 1.0, "雨": 0.6, "雪": 0.3},
        "雨": {"晴れ": 0.2, "曇り": 0.6, "雨": 1.0, "雪": 0.4},
        "雪": {"晴れ": 0.1, "曇り": 0.3, "雨": 0.4, "雪": 1.0},
    }

    def __init__(self):
        """初期化"""
        self._tfidf_vectorizer = None
        self._weather_keywords = self._load_weather_keywords()

    def calculate_weather_similarity(
        self, current_weather: WeatherForecast, past_comment: PastComment
    ) -> float:
        """
        天気条件の類似度を計算

        Args:
            current_weather: 現在の天気予報
            past_comment: 過去のコメント

        Returns:
            類似度スコア (0.0-1.0)
        """
        score = 0.0

        # 天気条件の類似度
        if past_comment.weather_condition:
            current_condition = self._normalize_weather_condition(
                current_weather.weather_description
            )
            past_condition = self._normalize_weather_condition(past_comment.weather_condition)

            if current_condition in self.WEATHER_SIMILARITY_MATRIX:
                if past_condition in self.WEATHER_SIMILARITY_MATRIX[current_condition]:
                    score = self.WEATHER_SIMILARITY_MATRIX[current_condition][past_condition]

        return score

    def calculate_temperature_similarity(
        self, current_temp: float, past_temp: float | None
    ) -> float:
        """
        気温の類似度を計算

        Args:
            current_temp: 現在の気温
            past_temp: 過去の気温

        Returns:
            類似度スコア (0.0-1.0)
        """
        if past_temp is None:
            return 0.5  # 気温データがない場合は中間値

        # 温度差に基づく類似度計算（10度差で0.0になる）
        temp_diff = abs(current_temp - past_temp)
        similarity = max(0.0, 1.0 - (temp_diff / 10.0))

        return similarity

    def calculate_semantic_similarity(self, current_context: str, past_comment_text: str) -> float:
        """
        セマンティック類似度を計算

        Args:
            current_context: 現在のコンテキスト
            past_comment_text: 過去のコメントテキスト

        Returns:
            類似度スコア (0.0-1.0)
        """
        # 簡易的なキーワードベースの類似度計算
        # 実際の実装ではTF-IDFやBERTなどを使用

        current_keywords = self._extract_keywords(current_context)
        comment_keywords = self._extract_keywords(past_comment_text)

        if not current_keywords or not comment_keywords:
            return 0.0

        # Jaccard係数で類似度を計算
        intersection = len(current_keywords & comment_keywords)
        union = len(current_keywords | comment_keywords)

        return intersection / union if union > 0 else 0.0

    def calculate_temporal_similarity(
        self, current_datetime: datetime, past_datetime: datetime | None
    ) -> float:
        """
        時間的類似度を計算

        Args:
            current_datetime: 現在の日時
            past_datetime: 過去のコメント日時

        Returns:
            類似度スコア (0.0-1.0)
        """
        if not past_datetime:
            return 0.5

        # 時間帯の類似度（朝・昼・夜）
        current_hour = current_datetime.hour
        past_hour = past_datetime.hour

        current_period = self._get_time_period(current_hour)
        past_period = self._get_time_period(past_hour)

        if current_period == past_period:
            return 1.0
        elif abs(current_hour - past_hour) <= 3:
            return 0.7
        else:
            return 0.3

    def calculate_location_similarity(self, current_location: str, past_location: str) -> float:
        """
        地点の類似度を計算

        Args:
            current_location: 現在の地点
            past_location: 過去のコメント地点

        Returns:
            類似度スコア (0.0-1.0)
        """
        # 正規化
        current_norm = self._normalize_location(current_location)
        past_norm = self._normalize_location(past_location)

        # 完全一致
        if current_norm == past_norm:
            return 1.0

        # 部分一致（都道府県レベル）
        if self._is_same_prefecture(current_norm, past_norm):
            return 0.7

        # 地方レベル
        if self._is_same_region(current_norm, past_norm):
            return 0.4

        return 0.1

    def calculate_composite_similarity(
        self,
        current_weather: WeatherForecast,
        past_comment: PastComment,
        current_datetime: datetime,
        current_location: str,
    ) -> dict[str, float]:
        """
        総合的な類似度を計算

        Returns:
            各類似度スコアを含む辞書
        """
        weather_sim = self.calculate_weather_similarity(current_weather, past_comment)
        temp_sim = self.calculate_temperature_similarity(
            current_weather.temperature, past_comment.temperature
        )
        semantic_sim = self.calculate_semantic_similarity(
            f"{current_weather.weather_description} {current_weather.temperature}度",
            past_comment.comment_text,
        )
        temporal_sim = self.calculate_temporal_similarity(current_datetime, past_comment.datetime)
        location_sim = self.calculate_location_similarity(current_location, past_comment.location)

        return {
            "weather_similarity": weather_sim,
            "temperature_similarity": temp_sim,
            "semantic_similarity": semantic_sim,
            "temporal_similarity": temporal_sim,
            "location_similarity": location_sim,
            "total_score": (
                weather_sim * 0.3
                + temp_sim * 0.2
                + semantic_sim * 0.2
                + temporal_sim * 0.2
                + location_sim * 0.1
            ),
        }

    # ヘルパーメソッド

    def _normalize_weather_condition(self, condition: str) -> str:
        """天気条件を正規化"""
        condition_lower = condition.lower()

        if "晴" in condition or "sunny" in condition_lower:
            return "晴れ"
        elif "曇" in condition or "cloud" in condition_lower:
            return "曇り"
        elif "雨" in condition or "rain" in condition_lower:
            return "雨"
        elif "雪" in condition or "snow" in condition_lower:
            return "雪"
        else:
            return condition

    def _load_weather_keywords(self) -> set:
        """天気関連キーワードを読み込み"""
        return {
            "晴れ",
            "曇り",
            "雨",
            "雪",
            "風",
            "暖かい",
            "寒い",
            "涼しい",
            "暑い",
            "快適",
            "爽やか",
            "じめじめ",
            "カラッと",
            "ひんやり",
            "ぽかぽか",
        }

    def _extract_keywords(self, text: str) -> set:
        """テキストからキーワードを抽出"""
        # 簡易実装：天気関連キーワードのみ抽出
        keywords = set()
        for keyword in self._weather_keywords:
            if keyword in text:
                keywords.add(keyword)
        return keywords

    def _get_time_period(self, hour: int) -> str:
        """時間帯を取得"""
        if 5 <= hour < 10:
            return "朝"
        elif 10 <= hour < 17:
            return "昼"
        elif 17 <= hour < 21:
            return "夕"
        else:
            return "夜"

    def _normalize_location(self, location: str) -> str:
        """地点名を正規化"""
        # 空白除去、小文字化など
        return location.strip().replace(" ", "").replace("　", "")

    def _is_same_prefecture(self, loc1: str, loc2: str) -> bool:
        """同じ都道府県かチェック"""
        # 簡易実装
        prefectures = ["北海道", "東京", "大阪", "福岡", "沖縄"]
        for pref in prefectures:
            if pref in loc1 and pref in loc2:
                return True
        return False

    def _is_same_region(self, loc1: str, loc2: str) -> bool:
        """同じ地方かチェック"""
        # 簡易実装
        regions = {
            "北海道": ["北海道"],
            "東北": ["青森", "岩手", "宮城", "秋田", "山形", "福島"],
            "関東": ["東京", "神奈川", "埼玉", "千葉", "茨城", "栃木", "群馬"],
            "九州": ["福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島"],
        }

        for region, prefs in regions.items():
            if any(pref in loc1 for pref in prefs) and any(pref in loc2 for pref in prefs):
                return True
        return False

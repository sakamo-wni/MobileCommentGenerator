"""
過去コメントデータ管理

ローカルCSVファイルから取得する過去コメントデータの構造化と管理を行う
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class CommentType(Enum):
    """コメントタイプの列挙型"""

    WEATHER_COMMENT = "weather_comment"  # 天気コメント
    ADVICE = "advice"  # アドバイス
    UNKNOWN = "unknown"  # 不明


@dataclass
class PastComment:
    """過去コメントデータを表すデータクラス

    Attributes:
        location: 地点名
        datetime: 投稿日時
        weather_condition: 天気状況
        comment_text: コメント本文
        comment_type: コメントタイプ
        temperature: 気温（℃, オプション）
        weather_code: 天気コード（オプション）
        humidity: 湿度（%, オプション）
        wind_speed: 風速（m/s, オプション）
        precipitation: 降水量（mm, オプション）
        source_file: 元ファイル名（トレーサビリティ用）
        raw_data: 元のJSONデータ
    """

    location: str
    datetime: datetime
    weather_condition: str
    comment_text: str
    comment_type: CommentType
    temperature: Optional[float] = None
    weather_code: Optional[str] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    precipitation: Optional[float] = None
    source_file: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    usage_count: Optional[int] = None

    def __post_init__(self):
        """データクラス初期化後の検証処理"""
        # コメント本文の検証
        if not self.comment_text or not self.comment_text.strip():
            raise ValueError("コメント本文が空です")

        # 文字数制限チェック（警告レベル）
        if len(self.comment_text) > 15:
            # 15文字を超える場合は警告（過去データなので例外は発生させない）
            pass

        # 地点名の検証
        if not self.location or not self.location.strip():
            raise ValueError("地点名が空です")

        # 天気状況の検証
        if not self.weather_condition or not self.weather_condition.strip():
            raise ValueError("天気状況が空です")

        # 気温の妥当性チェック（設定されている場合のみ）
        if self.temperature is not None:
            if not -50 <= self.temperature <= 60:
                raise ValueError(f"異常な気温値: {self.temperature}℃")

        # 湿度の妥当性チェック（設定されている場合のみ）
        if self.humidity is not None:
            if not 0 <= self.humidity <= 100:
                raise ValueError(f"異常な湿度値: {self.humidity}%")

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            過去コメントデータの辞書
        """
        return {
            "location": self.location,
            "datetime": self.datetime.isoformat(),
            "weather_condition": self.weather_condition,
            "comment_text": self.comment_text,
            "comment_type": (
                self.comment_type.value
                if hasattr(self.comment_type, "value")
                else str(self.comment_type)
            ),
            "temperature": self.temperature,
            "weather_code": self.weather_code,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "precipitation": self.precipitation,
            "source_file": self.source_file,
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], source_file: Optional[str] = None) -> "PastComment":
        """辞書から PastComment オブジェクトを作成

        Args:
            data: 過去コメントデータの辞書
            source_file: 元ファイル名

        Returns:
            PastComment オブジェクト
        """
        # datetime文字列を datetime オブジェクトに変換
        if isinstance(data.get("datetime"), str):
            datetime_obj = datetime.fromisoformat(data["datetime"].replace("Z", "+00:00"))
        elif isinstance(data.get("datetime"), datetime):
            datetime_obj = data["datetime"]
        else:
            # datetimeが不正な場合はデフォルト値を使用
            datetime_obj = datetime.now()

        # comment_type の変換
        comment_type_str = data.get("comment_type", "unknown")
        try:
            comment_type = CommentType(comment_type_str)
        except ValueError:
            comment_type = CommentType.UNKNOWN

        return cls(
            location=data.get("location", ""),
            datetime=datetime_obj,
            weather_condition=data.get("weather_condition", ""),
            comment_text=data.get("comment_text", ""),
            comment_type=comment_type,
            temperature=data.get("temperature"),
            weather_code=data.get("weather_code"),
            humidity=data.get("humidity"),
            wind_speed=data.get("wind_speed"),
            precipitation=data.get("precipitation"),
            source_file=source_file,
            raw_data=data.copy(),
            usage_count=data.get("usage_count"),
        )

    def matches_weather_condition(self, target_condition: str, fuzzy: bool = True) -> bool:
        """天気状況が一致するかチェック

        Args:
            target_condition: 対象の天気状況
            fuzzy: あいまい検索を行うか

        Returns:
            一致する場合True
        """
        if not fuzzy:
            return self.weather_condition == target_condition

        # あいまい検索（部分一致）
        condition_lower = self.weather_condition.lower()
        target_lower = target_condition.lower()

        # 完全一致
        if condition_lower == target_lower:
            return True

        # 部分一致
        if target_lower in condition_lower or condition_lower in target_lower:
            return True

        # 天気状況の類似度判定
        weather_synonyms = {
            "晴れ": ["快晴", "晴天", "clear", "sunny"],
            "曇り": ["曇天", "cloudy", "曇り空"],
            "雨": ["降雨", "rain", "rainy", "小雨", "大雨"],
            "雪": ["降雪", "snow", "snowy", "小雪", "大雪"],
            "霧": ["fog", "foggy", "かすみ"],
            "風": ["wind", "windy", "強風", "微風"],
        }

        for base_condition, synonyms in weather_synonyms.items():
            if base_condition in condition_lower or any(syn in condition_lower for syn in synonyms):
                if base_condition in target_lower or any(syn in target_lower for syn in synonyms):
                    return True

        return False

    def calculate_similarity_score(
        self,
        target_weather_condition: str,
        target_temperature: Optional[float] = None,
        target_location: Optional[str] = None,
    ) -> float:
        """類似度スコアを計算

        Args:
            target_weather_condition: 対象の天気状況
            target_temperature: 対象の気温
            target_location: 対象の地点

        Returns:
            類似度スコア（0.0-1.0）
        """
        score = 0.0

        # 天気状況の類似度（50%の重み）
        if self.matches_weather_condition(target_weather_condition):
            score += 0.5

        # 気温の類似度（30%の重み）
        if self.temperature is not None and target_temperature is not None:
            temp_diff = abs(self.temperature - target_temperature)
            # 温度差が10度以内なら類似とみなす
            if temp_diff <= 10:
                temp_score = max(0, (10 - temp_diff) / 10)
                score += 0.3 * temp_score

        # 地点の類似度（20%の重み）
        if target_location is not None:
            if self.location == target_location:
                score += 0.2
            elif target_location in self.location or self.location in target_location:
                score += 0.1

        return min(1.0, score)

    def get_character_count(self) -> int:
        """コメントの文字数を取得

        Returns:
            文字数
        """
        return len(self.comment_text)

    def is_within_length_limit(self, max_length: int = 15) -> bool:
        """文字数制限内かチェック

        Args:
            max_length: 最大文字数

        Returns:
            制限内の場合True
        """
        return self.get_character_count() <= max_length

    def is_valid(self) -> bool:
        """コメントが有効かチェック

        Returns:
            有効な場合True
        """
        # コメント本文が空でないか
        if not self.comment_text or not self.comment_text.strip():
            return False

        # 地点名が空でないか
        if not self.location or not self.location.strip():
            return False

        # 天気状況が空でないか
        if not self.weather_condition or not self.weather_condition.strip():
            return False

        # 気温の妥当性（設定されている場合のみ）
        if self.temperature is not None:
            if not -50 <= self.temperature <= 60:
                return False

        # 湿度の妥当性（設定されている場合のみ）
        if self.humidity is not None:
            if not 0 <= self.humidity <= 100:
                return False

        return True


@dataclass
class PastCommentCollection:
    """過去コメントのコレクションを管理するクラス

    Attributes:
        comments: 過去コメントのリスト
        source_period: データの期間（YYYYMM形式）
        loaded_at: データ読み込み日時
    """

    comments: List[PastComment]
    source_period: Optional[str] = None
    loaded_at: datetime = field(default_factory=datetime.now)

    def filter_by_location(
        self, location: str, exact_match: bool = False
    ) -> "PastCommentCollection":
        """地点でフィルタリング

        Args:
            location: 地点名
            exact_match: 完全一致かどうか

        Returns:
            フィルタリングされたコレクション
        """
        if exact_match:
            filtered_comments = [c for c in self.comments if c.location == location]
        else:
            location_lower = location.lower()
            filtered_comments = [
                c
                for c in self.comments
                if location_lower in c.location.lower() or c.location.lower() in location_lower
            ]

        return PastCommentCollection(
            comments=filtered_comments, source_period=self.source_period, loaded_at=self.loaded_at
        )

    def filter_by_weather_condition(
        self, condition: str, fuzzy: bool = True
    ) -> "PastCommentCollection":
        """天気状況でフィルタリング

        Args:
            condition: 天気状況
            fuzzy: あいまい検索かどうか

        Returns:
            フィルタリングされたコレクション
        """
        filtered_comments = [
            c for c in self.comments if c.matches_weather_condition(condition, fuzzy)
        ]

        return PastCommentCollection(
            comments=filtered_comments, source_period=self.source_period, loaded_at=self.loaded_at
        )

    def filter_by_comment_type(self, comment_type: CommentType) -> "PastCommentCollection":
        """コメントタイプでフィルタリング

        Args:
            comment_type: コメントタイプ

        Returns:
            フィルタリングされたコレクション
        """
        filtered_comments = [c for c in self.comments if c.comment_type == comment_type]

        return PastCommentCollection(
            comments=filtered_comments, source_period=self.source_period, loaded_at=self.loaded_at
        )

    def filter_by_type(self, comment_type: CommentType) -> "PastCommentCollection":
        """コメントタイプでフィルタリング（エイリアス）

        Args:
            comment_type: コメントタイプ

        Returns:
            フィルタリングされたコレクション
        """
        return self.filter_by_comment_type(comment_type)

    def get_similar_comments(
        self,
        target_weather_condition: str,
        target_temperature: Optional[float] = None,
        target_location: Optional[str] = None,
        min_similarity: float = 0.3,
        max_results: int = 10,
    ) -> List[PastComment]:
        """類似コメントを取得

        Args:
            target_weather_condition: 対象の天気状況
            target_temperature: 対象の気温
            target_location: 対象の地点
            min_similarity: 最小類似度
            max_results: 最大結果数

        Returns:
            類似度順にソートされたコメントリスト
        """
        # 類似度を計算
        comment_scores = []
        for comment in self.comments:
            score = comment.calculate_similarity_score(
                target_weather_condition, target_temperature, target_location
            )
            if score >= min_similarity:
                comment_scores.append((comment, score))

        # 類似度でソート（降順）
        comment_scores.sort(key=lambda x: x[1], reverse=True)

        # 指定数まで返す
        return [comment for comment, score in comment_scores[:max_results]]

    def get_by_type_and_similarity(
        self,
        comment_type: CommentType,
        target_weather_condition: str,
        target_temperature: Optional[float] = None,
        target_location: Optional[str] = None,
        max_results: int = 5,
    ) -> List[PastComment]:
        """タイプと類似度で絞り込み

        Args:
            comment_type: コメントタイプ
            target_weather_condition: 対象の天気状況
            target_temperature: 対象の気温
            target_location: 対象の地点
            max_results: 最大結果数

        Returns:
            フィルタリングされたコメントリスト
        """
        # まずタイプでフィルタリング
        type_filtered = self.filter_by_comment_type(comment_type)

        # 類似度で絞り込み
        return type_filtered.get_similar_comments(
            target_weather_condition, target_temperature, target_location, max_results=max_results
        )

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得

        Returns:
            統計情報の辞書
        """
        if not self.comments:
            return {}

        # タイプ別集計
        type_counts = {}
        for comment_type in CommentType:
            type_counts[comment_type.value] = sum(
                1 for c in self.comments if c.comment_type == comment_type
            )

        # 地点別集計
        location_counts = {}
        for comment in self.comments:
            location_counts[comment.location] = location_counts.get(comment.location, 0) + 1

        # 文字数統計
        char_counts = [c.get_character_count() for c in self.comments]

        return {
            "total_comments": len(self.comments),
            "type_distribution": type_counts,
            "location_distribution": dict(
                sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "character_stats": {
                "min_length": min(char_counts) if char_counts else 0,
                "max_length": max(char_counts) if char_counts else 0,
                "avg_length": sum(char_counts) / len(char_counts) if char_counts else 0,
                "within_15_chars": sum(1 for c in char_counts if c <= 15),
            },
            "source_period": self.source_period,
            "loaded_at": self.loaded_at.isoformat(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            コレクションデータの辞書
        """
        return {
            "comments": [c.to_dict() for c in self.comments],
            "source_period": self.source_period,
            "loaded_at": self.loaded_at.isoformat(),
            "statistics": self.get_statistics(),
        }


if __name__ == "__main__":
    # テスト用コード
    sample_data = {
        "location": "東京",
        "datetime": "2024-06-05T12:00:00+09:00",
        "weather_condition": "晴れ",
        "comment_text": "爽やかな朝ですね",
        "comment_type": "weather_comment",
        "temperature": 22.5,
        "weather_code": "100",
    }

    # PastCommentオブジェクトの作成テスト
    comment = PastComment.from_dict(sample_data)
    print(f"コメント: {comment.comment_text}")
    print(f"文字数: {comment.get_character_count()}")
    print(f"類似度 (晴れ, 25度): {comment.calculate_similarity_score('晴れ', 25.0, '東京')}")

    # コレクションのテスト
    collection = PastCommentCollection(comments=[comment])
    stats = collection.get_statistics()
    print(f"統計情報: {stats}")

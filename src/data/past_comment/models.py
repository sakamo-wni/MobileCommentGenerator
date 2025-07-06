"""
過去コメントのモデル定義

CommentTypeとPastCommentクラスの定義
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
    
    # インデックス用の日時フィールド（検索高速化のため）
    _indexed_datetime: Optional[datetime] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """フィールドの追加処理"""
        # datetimeがstrの場合は変換
        if isinstance(self.datetime, str):
            try:
                self.datetime = datetime.fromisoformat(self.datetime)
            except ValueError:
                # ISO形式でない場合の処理
                from dateutil import parser

                self.datetime = parser.parse(self.datetime)

        # CommentTypeが文字列の場合は変換
        if isinstance(self.comment_type, str):
            try:
                self.comment_type = CommentType(self.comment_type)
            except ValueError:
                self.comment_type = CommentType.UNKNOWN

        # インデックス用の日時フィールドを設定
        self._indexed_datetime = self.datetime

    @property
    def text(self) -> str:
        """コメントテキストのエイリアス（後方互換性のため）"""
        return self.comment_text

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "location": self.location,
            "datetime": self.datetime.isoformat(),
            "weather_condition": self.weather_condition,
            "comment_text": self.comment_text,
            "comment_type": self.comment_type.value,
            "temperature": self.temperature,
            "weather_code": self.weather_code,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "precipitation": self.precipitation,
            "source_file": self.source_file,
            "raw_data": self.raw_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], source_file: Optional[str] = None) -> "PastComment":
        """辞書形式からPastCommentインスタンスを作成"""
        # データのコピーを作成（元データを変更しないため）
        data_copy = data.copy()

        # source_fileが指定されていれば追加
        if source_file:
            data_copy["source_file"] = source_file

        # raw_dataとして元のデータを保存
        data_copy["raw_data"] = data.copy()

        # テキストフィールドの正規化
        if "text" in data_copy and "comment_text" not in data_copy:
            data_copy["comment_text"] = data_copy.pop("text")
        elif "text" in data_copy and "comment_text" in data_copy:
            # 両方ある場合はtextを削除
            data_copy.pop("text")

        # comment_typeフィールドの正規化
        if "type" in data_copy and "comment_type" not in data_copy:
            data_copy["comment_type"] = data_copy.pop("type")
        elif "type" in data_copy and "comment_type" in data_copy:
            # 両方ある場合はtypeを削除
            data_copy.pop("type")

        # 必須フィールドのデフォルト値設定
        if "comment_type" not in data_copy:
            data_copy["comment_type"] = CommentType.UNKNOWN

        # 天気条件フィールドの正規化
        if "weather" in data_copy and "weather_condition" not in data_copy:
            data_copy["weather_condition"] = data_copy.pop("weather")
        elif "weather" in data_copy and "weather_condition" in data_copy:
            data_copy.pop("weather")

        # datetimeフィールドの処理
        if "date" in data_copy and "datetime" not in data_copy:
            data_copy["datetime"] = data_copy.pop("date")

        # オプションフィールドのキー名正規化
        field_mapping = {
            "temp": "temperature",
            "humid": "humidity",
            "wind": "wind_speed",
            "precip": "precipitation",
        }

        for old_key, new_key in field_mapping.items():
            if old_key in data_copy and new_key not in data_copy:
                data_copy[new_key] = data_copy.pop(old_key)

        return cls(**data_copy)

    def get_character_count(self) -> int:
        """コメントの文字数を取得

        Returns:
            int: コメントの文字数
        """
        return len(self.comment_text)

    def is_within_length_limit(self, max_length: int = 15) -> bool:
        """コメントが指定文字数以内かチェック

        Args:
            max_length: 最大文字数（デフォルト: 15）

        Returns:
            bool: 文字数制限内の場合True
        """
        return self.get_character_count() <= max_length

    def is_valid(self) -> bool:
        """コメントの基本的な妥当性をチェック

        Returns:
            bool: 妥当な場合True
        """
        # 必須フィールドのチェック
        if not all(
            [
                self.location,
                self.datetime,
                self.weather_condition,
                self.comment_text,
                self.comment_type,
            ]
        ):
            return False

        # コメントタイプが不明でないことをチェック
        if self.comment_type == CommentType.UNKNOWN:
            return False

        # コメントテキストが空でないことをチェック
        if not self.comment_text.strip():
            return False

        # 文字数制限チェック（15文字）
        if not self.is_within_length_limit():
            return False

        return True
    
    def matches_weather_condition(self, target_condition: str, fuzzy: bool = True) -> bool:
        """天気条件が一致するかチェック

        Args:
            target_condition: 対象の天気条件
            fuzzy: あいまい一致を許可するか

        Returns:
            bool: 一致する場合True
        """
        # SimilarityCalculatorに委譲
        from src.data.past_comment.similarity import SimilarityCalculator
        return SimilarityCalculator.matches_weather_condition(self, target_condition, fuzzy)
    
    def calculate_similarity_score(
        self,
        target_weather: str,
        target_temp: Optional[float] = None,
        target_humidity: Optional[float] = None,
        target_datetime: Optional[datetime] = None,
    ) -> float:
        """現在の天気条件との類似度スコアを計算

        Args:
            target_weather: 対象の天気条件
            target_temp: 対象の気温
            target_humidity: 対象の湿度
            target_datetime: 対象の日時

        Returns:
            float: 類似度スコア (0.0-1.0)
        """
        # SimilarityCalculatorに委譲
        from src.data.past_comment.similarity import SimilarityCalculator
        return SimilarityCalculator.calculate_similarity_score(
            self, target_weather, target_temp, target_humidity, target_datetime
        )
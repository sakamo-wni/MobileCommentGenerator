"""過去コメントのデータモデル"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum


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
    temperature: float | None = None
    weather_code: str | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    precipitation: float | None = None
    source_file: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    # 天気・アドバイスの分離されたコメント（オプション）
    weather_comment: str | None = None
    advice_comment: str | None = None

    def __post_init__(self):
        """データ初期化後の処理"""
        # JSONエンコード可能な形式に変換
        if isinstance(self.datetime, datetime):
            self.datetime_str = self.datetime.isoformat()
        elif hasattr(self, "datetime_str"):
            # 既にdatetime_strがある場合はそれを使用
            pass
        else:
            # datetime型でもstrでもない場合は現在時刻を使用
            self.datetime = datetime.now()
            self.datetime_str = self.datetime.isoformat()

        # comment_typeがstrの場合の処理
        if isinstance(self.comment_type, str):
            try:
                self.comment_type = CommentType(self.comment_type)
            except ValueError:
                self.comment_type = CommentType.UNKNOWN

        # テキストのクリーニング
        self.comment_text = self._clean_text(self.comment_text)
        if self.weather_comment:
            self.weather_comment = self._clean_text(self.weather_comment)
        if self.advice_comment:
            self.advice_comment = self._clean_text(self.advice_comment)

    @staticmethod
    def _clean_text(text: str) -> str:
        """テキストをクリーニング"""
        if not text:
            return ""
        # 改行の正規化と前後の空白削除
        return text.replace("\\n", "\n").strip()

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        result = {
            "location": self.location,
            "datetime": self.datetime.isoformat() if isinstance(self.datetime, datetime) else str(self.datetime),
            "weather_condition": self.weather_condition,
            "comment_text": self.comment_text,
            "comment_type": self.comment_type.value,
            "temperature": self.temperature,
            "weather_code": self.weather_code,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "precipitation": self.precipitation,
            "source_file": self.source_file,
        }

        # オプションフィールドの追加
        if self.weather_comment:
            result["weather_comment"] = self.weather_comment
        if self.advice_comment:
            result["advice_comment"] = self.advice_comment

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any], source_file: str | None = None) -> "PastComment":
        """辞書形式から変換"""
        # datetimeの変換
        if "datetime" in data:
            if isinstance(data["datetime"], str):
                # ISOフォーマットから変換
                dt = datetime.fromisoformat(data["datetime"].replace("Z", "+00:00"))
            else:
                dt = data["datetime"]
        else:
            # デフォルト値
            dt = datetime.now()

        # comment_typeの変換
        comment_type_str = data.get("comment_type", "unknown")
        try:
            comment_type = CommentType(comment_type_str)
        except ValueError:
            comment_type = CommentType.UNKNOWN

        return cls(
            location=data.get("location", ""),
            datetime=dt,
            weather_condition=data.get("weather_condition", ""),
            comment_text=data.get("comment_text", ""),
            comment_type=comment_type,
            temperature=data.get("temperature"),
            weather_code=data.get("weather_code"),
            humidity=data.get("humidity"),
            wind_speed=data.get("wind_speed"),
            precipitation=data.get("precipitation"),
            source_file=source_file or data.get("source_file"),
            raw_data=data,
            weather_comment=data.get("weather_comment"),
            advice_comment=data.get("advice_comment"),
        )

    def get_character_count(self) -> int:
        """コメントの文字数を取得"""
        return len(self.comment_text)

    def is_within_length_limit(self, max_length: int = 15) -> bool:
        """コメントが指定の文字数制限内か確認
        
        Args:
            max_length: 最大文字数（デフォルト: 15）
        
        Returns:
            制限内の場合True
        """
        return self.get_character_count() <= max_length

    def is_valid(self) -> bool:
        """コメントの妥当性を検証
        
        Returns:
            有効なコメントの場合True
        """
        # 必須フィールドのチェック
        if not self.location or not self.comment_text:
            return False
        
        # コメントテキストが有効か
        if len(self.comment_text.strip()) < 3:  # 最低3文字は必要
            return False
        
        # 天気状況が設定されているか
        if not self.weather_condition:
            return False
        
        # 温度が現実的な範囲か（設定されている場合）
        if self.temperature is not None:
            if self.temperature < -50 or self.temperature > 50:
                return False
        
        # 湿度が現実的な範囲か（設定されている場合）
        if self.humidity is not None:
            if self.humidity < 0 or self.humidity > 100:
                return False
        
        return True
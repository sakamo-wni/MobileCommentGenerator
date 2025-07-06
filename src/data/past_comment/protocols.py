"""
過去コメントデータ管理のプロトコル定義

循環参照を避けるためのインターフェース定義
"""

from typing import Protocol, Optional
from datetime import datetime


class SimilarityCalculable(Protocol):
    """類似度計算可能なオブジェクトのプロトコル"""
    
    location: str
    datetime: datetime
    weather_condition: str
    comment_text: str
    temperature: Optional[float]
    humidity: Optional[float]
    
    def matches_weather_condition(self, target_condition: str, fuzzy: bool = True) -> bool:
        """天気条件が一致するかチェック"""
        ...
    
    def calculate_similarity_score(
        self,
        target_weather: str,
        target_temp: Optional[float] = None,
        target_humidity: Optional[float] = None,
        target_datetime: Optional[datetime] = None,
    ) -> float:
        """現在の天気条件との類似度スコアを計算"""
        ...
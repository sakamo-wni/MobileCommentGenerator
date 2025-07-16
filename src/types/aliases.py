"""
共通で使用される型エイリアスの定義

頻繁に使用される複雑な型をエイリアスとして定義することで、
コードの可読性と保守性を向上させます。
"""

from __future__ import annotations
from typing import Any
from collections.abc import Callable

# ジェネリックなデータ構造
JsonDict = dict[str, Any]
JsonList = list[dict[str, Any]]
NullableJsonDict = dict[str, Any | None]

# 設定とコンフィグレーション
ConfigDict = dict[str, str | int | float | bool]
StringMapping = dict[str, str]

# 天気と地点に特化した型
WeatherMetadata = dict[str, str | float | None]
TemperatureDifferences = dict[str, float | None]

# UI と履歴
HistoryEntry = dict[str, str]
HistoryList = list[dict[str, str]]

# コールバック
ProgressCallback = Callable[[int, int, str | None], None]

# 統計とメトリクス
NumericStats = dict[str, int]
FloatStats = dict[str, float]

# API レスポンス
ApiResponse = dict[str, Any]
ApiErrorDetail = dict[str, str | int | None]

# バッチ処理結果
BatchResult = dict[str, bool | str | list[Any] | None]
LocationResults = list[dict[str, Any]]
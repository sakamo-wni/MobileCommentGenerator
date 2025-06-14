"""共通ユーティリティ関数"""

from datetime import datetime
from typing import Dict


def get_season_from_month(month: int) -> str:
    """月から季節を判定する共通関数
    
    Args:
        month: 月（1-12）
        
    Returns:
        季節名（春、梅雨、夏、台風、秋、冬）
    """
    season_map = {
        1: "冬", 2: "冬", 3: "春", 4: "春", 5: "春",
        6: "梅雨", 7: "夏", 8: "夏", 9: "台風",
        10: "秋", 11: "秋", 12: "冬"
    }
    return season_map.get(month, "不明")


def get_related_seasons(month: int) -> list[str]:
    """現在月に関連する季節を取得（前後の季節も含む）
    
    Args:
        month: 月（1-12）
        
    Returns:
        関連する季節のリスト
    """
    # 月と季節の詳細マッピング
    season_transitions = {
        1: ["冬"],
        2: ["冬"],
        3: ["冬", "春"],
        4: ["春"],
        5: ["春", "梅雨"],
        6: ["春", "梅雨", "夏"],
        7: ["梅雨", "夏"],
        8: ["夏", "台風"],
        9: ["夏", "台風", "秋"],
        10: ["台風", "秋"],
        11: ["秋", "冬"],
        12: ["冬"]
    }
    return season_transitions.get(month, ["春", "夏", "秋", "冬"])


def get_time_period_from_hour(hour: int) -> str:
    """時間帯から期間を判定
    
    Args:
        hour: 時（0-23）
        
    Returns:
        時間帯（朝、昼、夕方、夜）
    """
    if 5 <= hour < 10:
        return "朝"
    elif 10 <= hour < 16:
        return "昼"
    elif 16 <= hour < 19:
        return "夕方"
    else:
        return "夜"


# 共通定数
SEVERE_WEATHER_PATTERNS = ["大雨", "豪雨", "暴風", "台風", "雷", "嵐", "大雪", "吹雪"]
FORBIDDEN_PHRASES = ["ニワカ雨が心配", "にわか雨が心配", "スッキリしない空", "変わりやすい空", 
                    "蒸し暑い", "厳しい暑さ", "過ごしやすい体感", "過ごしやすい", "快適"]
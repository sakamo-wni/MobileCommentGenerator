"""天気タイプ分類ユーティリティ"""

from typing import Optional
from src.config.config import get_weather_constants

# 定数を取得
WEATHER_TYPE_KEYWORDS = get_weather_constants().WEATHER_TYPE_KEYWORDS


def classify_weather_type(weather_desc: str) -> Optional[str]:
    """
    天気説明文から天気タイプを分類
    
    Args:
        weather_desc: 天気の説明文
        
    Returns:
        'sunny', 'cloudy', 'rainy', None のいずれか
    """
    if not weather_desc:
        return None
        
    weather_desc_lower = weather_desc.lower()
    
    # 各タイプのキーワードをチェック
    for weather_type, keywords in WEATHER_TYPE_KEYWORDS.items():
        if any(keyword in weather_desc for keyword in keywords):
            return weather_type
            
    return None


def count_weather_type_changes(weather_types: list[Optional[str]]) -> int:
    """
    天気タイプの変化回数をカウント
    
    Args:
        weather_types: 天気タイプのリスト
        
    Returns:
        変化回数
    """
    if not weather_types or len(weather_types) < 2:
        return 0
        
    changes = 0
    for i in range(1, len(weather_types)):
        if weather_types[i] != weather_types[i-1]:
            changes += 1
            
    return changes


def is_morning_only_change(weather_types: list[Optional[str]]) -> bool:
    """
    朝だけ天気が違って、その後同じ天気が続くパターンかチェック
    
    Args:
        weather_types: 天気タイプのリスト（時系列順）
        
    Returns:
        朝だけ変化パターンかどうか
    """
    if len(weather_types) < 4:
        return False
        
    # 最初の時間帯（朝）が異なり、その後の3つの時間帯が同じ場合
    return (weather_types[0] != weather_types[1] and 
            weather_types[1] == weather_types[2] == weather_types[3])
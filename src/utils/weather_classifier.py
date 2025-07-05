"""天気タイプ分類のための共通ユーティリティ"""

from typing import List, Literal

# 天気タイプの定義
WeatherType = Literal["sunny", "cloudy", "rainy", "snowy", "other"]

# 天気判定の閾値
WEATHER_CHANGE_THRESHOLD = 2  # 「変わりやすい」と判定する変化回数の閾値

# 天気キーワードマッピング
WEATHER_KEYWORDS = {
    "rainy": ["雨", "にわか雨", "雷雨", "雷"],
    "snowy": ["雪", "みぞれ", "あられ", "ひょう"],
    "sunny": ["晴", "快晴", "日差し"],
    "cloudy": ["曇", "くもり"],
}


def classify_weather_type(weather_description: str) -> WeatherType:
    """
    天気の説明文から天気タイプを分類する
    
    Args:
        weather_description: 天気の説明文
        
    Returns:
        天気タイプ ("sunny", "cloudy", "rainy", "snowy", "other")
    """
    # 文字列を小文字に統一して判定
    desc_lower = weather_description.lower()
    
    # 雨・雪・雷を最優先で判定
    for keyword in WEATHER_KEYWORDS["rainy"]:
        if keyword in weather_description:
            return "rainy"
    
    for keyword in WEATHER_KEYWORDS["snowy"]:
        if keyword in weather_description:
            return "snowy"
    
    # 晴れ・曇りの判定
    for keyword in WEATHER_KEYWORDS["sunny"]:
        if keyword in weather_description:
            return "sunny"
    
    for keyword in WEATHER_KEYWORDS["cloudy"]:
        if keyword in weather_description:
            return "cloudy"
    
    return "other"


def count_weather_type_changes(weather_sequence: List[WeatherType]) -> int:
    """
    天気タイプの変化回数をカウントする
    
    Args:
        weather_sequence: 天気タイプのリスト
        
    Returns:
        変化回数
    """
    if len(weather_sequence) <= 1:
        return 0
    
    changes = 0
    for i in range(1, len(weather_sequence)):
        if weather_sequence[i] != weather_sequence[i-1]:
            changes += 1
    
    return changes


def is_weather_stable(weather_sequence: List[WeatherType], allow_morning_difference: bool = True) -> bool:
    """
    天気が安定しているかを判定する
    
    Args:
        weather_sequence: 天気タイプのリスト
        allow_morning_difference: 朝だけ違う場合を安定とみなすか
        
    Returns:
        安定している場合True
    """
    if not weather_sequence:
        return False
    
    changes = count_weather_type_changes(weather_sequence)
    
    # 変化が閾値以上なら不安定
    if changes >= WEATHER_CHANGE_THRESHOLD:
        return False
    
    # 朝だけ違う場合の特別処理
    if allow_morning_difference and changes == 1 and len(weather_sequence) >= 4:
        # インデックス1以降が全て同じかチェック
        if all(weather_sequence[i] == weather_sequence[1] for i in range(1, len(weather_sequence))):
            return True
    
    # その他の場合は変化が1回以下なら安定
    return changes <= 1
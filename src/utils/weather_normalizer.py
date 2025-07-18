"""
天気表現の正規化ユーティリティ

天気の表記ゆれを統一的に扱うためのユーティリティ関数
"""

def normalize_weather_description(weather_desc: str) -> str:
    """
    天気の表現を正規化する
    
    Args:
        weather_desc: 天気の説明文字列
        
    Returns:
        正規化された天気タイプ
    """
    weather_desc = weather_desc.lower()
    
    # 晴れ系
    if any(word in weather_desc for word in ["晴", "快晴", "はれ", "sunny", "clear"]):
        return "sunny"
    
    # 曇り系
    if any(word in weather_desc for word in ["曇", "くもり", "うすぐもり", "薄曇", "cloudy"]):
        return "cloudy"
    
    # 雨系
    if any(word in weather_desc for word in ["雨", "あめ", "rain", "雷雨", "にわか雨"]):
        return "rainy"
    
    # 雪系
    if any(word in weather_desc for word in ["雪", "ゆき", "snow", "吹雪"]):
        return "snowy"
    
    # その他
    return "other"


def is_stable_weather_condition(weather_descriptions: list[str]) -> bool:
    """
    天気が安定しているかどうかを判定
    
    Args:
        weather_descriptions: 天気説明のリスト
        
    Returns:
        安定した天気かどうか
    """
    normalized = [normalize_weather_description(desc) for desc in weather_descriptions]
    
    # 全て晴れまたは曇りで、雨や雪が含まれていない
    stable_types = {"sunny", "cloudy"}
    return all(weather in stable_types for weather in normalized)


def get_weather_severity(weather_desc: str) -> int:
    """
    天気の厳しさレベルを取得
    
    Args:
        weather_desc: 天気の説明
        
    Returns:
        厳しさレベル (0: 穏やか, 1: 普通, 2: 注意, 3: 警戒)
    """
    weather_desc = weather_desc.lower()
    
    # 警戒レベル
    if any(word in weather_desc for word in ["台風", "暴風", "大雨", "豪雨", "大雪", "吹雪"]):
        return 3
    
    # 注意レベル
    if any(word in weather_desc for word in ["雨", "雪", "雷", "強風"]):
        return 2
    
    # 普通レベル
    if any(word in weather_desc for word in ["曇", "くもり"]):
        return 1
    
    # 穏やかレベル
    return 0
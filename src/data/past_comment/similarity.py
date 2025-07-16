"""過去コメントの類似度計算"""

from __future__ import annotations
from src.config.similarity_config import get_similarity_config


def matches_weather_condition(comment_weather: str, target_condition: str, fuzzy: bool = True) -> bool:
    """天気状況がマッチするか確認
    
    Args:
        comment_weather: コメントの天気状況
        target_condition: 比較対象の天気状況
        fuzzy: あいまい検索を有効にするか
    
    Returns:
        マッチする場合True
    """
    if not fuzzy:
        return comment_weather.lower() == target_condition.lower()
    
    # あいまい検索: 部分一致を許可
    comment_weather_lower = comment_weather.lower()
    target_condition_lower = target_condition.lower()
    
    # 完全一致
    if comment_weather_lower == target_condition_lower:
        return True
    
    # 同義語マッピング
    synonyms = {
        "晴れ": ["晴", "快晴", "sunny", "clear"],
        "曇り": ["曇", "くもり", "cloudy", "overcast"],
        "雨": ["雨", "rain", "rainy", "降雨"],
        "雪": ["雪", "snow", "snowy", "降雪"],
        "霧": ["霧", "fog", "foggy", "濃霧"],
        "台風": ["台風", "typhoon", "暴風雨"],
    }
    
    # 同義語チェック
    for _, synonym_list in synonyms.items():
        if any(s in comment_weather_lower for s in synonym_list) and any(
            s in target_condition_lower for s in synonym_list
        ):
            return True
    
    # 部分一致
    return (
        target_condition_lower in comment_weather_lower
        or comment_weather_lower in target_condition_lower
    )


def calculate_similarity_score(
    comment_weather_condition: str,
    comment_temperature: float | None,
    comment_humidity: float | None,
    target_weather_condition: str,
    target_temperature: float | None = None,
    target_humidity: float | None = None,
) -> float:
    """天気条件の類似度スコアを計算
    
    Args:
        comment_weather_condition: コメントの天気状況
        comment_temperature: コメントの気温
        comment_humidity: コメントの湿度
        target_weather_condition: 対象の天気状況
        target_temperature: 対象の気温
        target_humidity: 対象の湿度
    
    Returns:
        0.0〜1.0の類似度スコア
    """
    config = get_similarity_config()
    score = 0.0
    weight_sum = 0.0
    
    # 天気状況の類似度
    if matches_weather_condition(comment_weather_condition, target_weather_condition):
        score += config.weather_condition_weight
    weight_sum += config.weather_condition_weight
    
    # 気温の類似度
    if comment_temperature is not None and target_temperature is not None:
        temp_diff = abs(comment_temperature - target_temperature)
        temp_score = max(0, 1 - (temp_diff / config.temperature_diff_threshold))
        score += temp_score * config.temperature_weight
        weight_sum += config.temperature_weight
    
    # 湿度の類似度
    if comment_humidity is not None and target_humidity is not None:
        humidity_diff = abs(comment_humidity - target_humidity)
        humidity_score = max(0, 1 - (humidity_diff / config.humidity_diff_threshold))
        score += humidity_score * config.humidity_weight
        weight_sum += config.humidity_weight
    
    # 重み付き平均
    return score / weight_sum if weight_sum > 0 else 0.0
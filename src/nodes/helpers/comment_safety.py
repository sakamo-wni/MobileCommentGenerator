"""コメント安全性チェックモジュール"""

from typing import List, Optional, Tuple
import logging
from src.data.comment_generation_state import CommentGenerationState
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment

logger = logging.getLogger(__name__)


def check_and_fix_weather_comment_safety(
    weather_data: WeatherForecast,
    weather_comment: str,
    advice_comment: str,
    state: CommentGenerationState
) -> Tuple[str, str]:
    """コメントの安全性をチェックし、必要に応じて修正する
    
    Args:
        weather_data: 天気予報データ
        weather_comment: 天気コメント
        advice_comment: アドバイスコメント
        state: コメント生成状態
        
    Returns:
        (修正後の天気コメント, 修正後のアドバイスコメント)のタプル
    """
    # 緊急安全チェック：完全に不適切な組み合わせを強制修正
    logger.critical(f"🚨 最終安全チェック開始: 天気='{weather_data.weather_description}', 気温={weather_data.temperature}°C")
    logger.critical(f"🚨 選択されたコメント: 天気='{weather_comment}', アドバイス='{advice_comment}'")
    
    # 晴天・快晴時の「変わりやすい空」は絶対に不適切 - 既存コメントから再選択
    if any(sunny in weather_data.weather_description for sunny in ["晴", "快晴", "猛暑"]) and weather_comment:
        changeable_patterns = [
            "変わりやすい空", "変わりやすい天気", "変わりやすい",
            "変化しやすい空", "移ろいやすい空", "気まぐれな空", "不安定な空模様"
        ]
        for pattern in changeable_patterns:
            if pattern in weather_comment:
                logger.critical(f"🚨 緊急修正: 晴天時に「{pattern}」は不適切 - 代替コメント検索")
                weather_comment = _find_alternative_weather_comment(
                    weather_data, state.past_weather_comments, changeable_patterns
                )
                break
    
    # 雨天で熱中症警告は絶対に不適切 - 既存コメントから再選択
    if "雨" in weather_data.weather_description and weather_data.temperature < 30.0 and advice_comment and "熱中症" in advice_comment:
        logger.critical(f"🚨 緊急修正: 雨天+低温で熱中症警告を除外 - 代替アドバイス検索")
        advice_comment = _find_rain_advice(state.past_advice_comments, advice_comment)
    
    # 大雨・嵐でムシムシ暑いは不適切 - 既存コメントから再選択
    if ("大雨" in weather_data.weather_description or "嵐" in weather_data.weather_description) and weather_comment and "ムシムシ" in weather_comment:
        logger.critical(f"🚨 緊急修正: 悪天候でムシムシコメントを除外 - 代替コメント検索")
        weather_comment = _find_storm_weather_comment(state.past_weather_comments, weather_comment)
    
    return weather_comment, advice_comment


def _find_alternative_weather_comment(
    weather_data: WeatherForecast,
    past_comments: Optional[List[PastComment]],
    changeable_patterns: List[str]
) -> str:
    """晴天時の代替天気コメントを検索"""
    if not past_comments:
        return ""
    
    # 気温に応じた適切なコメントのパターン
    if weather_data.temperature >= 35:
        preferred_patterns = ["猛烈な暑さ", "危険な暑さ", "猛暑に警戒", "激しい暑さ"]
    elif weather_data.temperature >= 30:
        preferred_patterns = ["厳しい暑さ", "強い日差し", "厳しい残暑", "強烈な日差し"]
    else:
        preferred_patterns = ["爽やかな晴天", "穏やかな空", "心地よい天気", "過ごしやすい天気"]
    
    # 既存コメントから適切なものを検索
    replacement_found = False
    weather_comment = ""
    
    for past_comment in past_comments:
        comment_text = past_comment.comment_text
        # 優先パターンに一致するものを探す
        for preferred in preferred_patterns:
            if preferred in comment_text:
                weather_comment = comment_text
                logger.critical(f"🚨 代替コメント発見: '{weather_comment}'")
                replacement_found = True
                break
        if replacement_found:
            break
    
    # 優先パターンが見つからない場合、晴天系の任意のコメントを選択
    if not replacement_found:
        sunny_keywords = ["晴", "日差し", "太陽", "快晴", "青空"]
        for past_comment in past_comments:
            comment_text = past_comment.comment_text
            if any(keyword in comment_text for keyword in sunny_keywords) and \
               not any(ng in comment_text for ng in changeable_patterns):
                weather_comment = comment_text
                logger.critical(f"🚨 晴天系代替コメント: '{weather_comment}'")
                replacement_found = True
                break
    
    # それでも見つからない場合はデフォルト（最初の有効なコメント）
    if not replacement_found and past_comments:
        weather_comment = past_comments[0].comment_text
        logger.critical(f"🚨 デフォルト代替: '{weather_comment}'")
    
    return weather_comment


def _find_rain_advice(past_comments: Optional[List[PastComment]], current_advice: str) -> str:
    """雨天時の代替アドバイスを検索"""
    if not past_comments:
        return current_advice
    
    # 雨天に適したアドバイスを検索
    rain_patterns = ["雨にご注意", "傘", "濡れ", "雨具", "足元", "滑り"]
    
    for past_comment in past_comments:
        comment_text = past_comment.comment_text
        if any(pattern in comment_text for pattern in rain_patterns):
            logger.critical(f"🚨 雨天用代替アドバイス: '{comment_text}'")
            return comment_text
    
    # 見つからない場合はデフォルト
    if past_comments:
        advice = past_comments[0].comment_text
        logger.critical(f"🚨 デフォルト代替アドバイス: '{advice}'")
        return advice
    
    return current_advice


def _find_storm_weather_comment(past_comments: Optional[List[PastComment]], current_comment: str) -> str:
    """悪天候時の代替天気コメントを検索"""
    if not past_comments:
        return current_comment
    
    # 悪天候に適したコメントを検索
    storm_patterns = ["荒れた天気", "大雨", "激しい雨", "暴風", "警戒", "注意", "本格的な雨"]
    
    for past_comment in past_comments:
        comment_text = past_comment.comment_text
        if any(pattern in comment_text for pattern in storm_patterns):
            logger.critical(f"🚨 悪天候用代替コメント: '{comment_text}'")
            return comment_text
    
    # 見つからない場合はデフォルト
    if past_comments:
        comment = past_comments[0].comment_text
        logger.critical(f"🚨 デフォルト代替: '{comment}'")
        return comment
    
    return current_comment
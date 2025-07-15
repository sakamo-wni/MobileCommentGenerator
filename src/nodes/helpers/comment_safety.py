"""コメント安全性チェックモジュール"""

from typing import Any
import logging
from src.data.comment_generation_state import CommentGenerationState
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment, CommentType

logger = logging.getLogger(__name__)

# 天気の変わりやすさを表現するパターン
CHANGEABLE_WEATHER_PATTERNS = [
    "変わりやすい空", "変わりやすい天気", "変わりやすい",
    "変化しやすい空", "移ろいやすい空", "気まぐれな空", "不安定な空模様"
]

# 晴天を表すキーワード（weather_comment_validator.pyと整合）
SUNNY_KEYWORDS = ["晴", "日差し", "太陽", "快晴", "青空"]
SUNNY_WEATHER_DESCRIPTIONS = ["晴", "快晴", "晴天", "薄曇", "うすぐもり", "薄ぐもり", "薄曇り", "うす曇り", "猛暑"]

# 雨天に適したアドバイスパターン
RAIN_ADVICE_PATTERNS = ["雨にご注意", "傘", "濡れ", "雨具", "足元", "滑り"]

# 悪天候を表すパターン
STORM_WEATHER_PATTERNS = ["荒れた天気", "大雨", "激しい雨", "暴風", "警戒", "注意", "本格的な雨"]

# 連続雨判定の閾値（時間）
CONTINUOUS_RAIN_THRESHOLD_HOURS = 4

# にわか雨表現のパターン
SHOWER_RAIN_PATTERNS = ["にわか雨", "ニワカ雨", "一時的な雨", "急な雨", "突然の雨", "雨が心配"]


def check_and_fix_weather_comment_safety(
    weather_data: WeatherForecast,
    weather_comment: str,
    advice_comment: str,
    state: CommentGenerationState
) -> tuple[str, str]:
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
    logger.info(f"🚨 最終安全チェック開始: 天気='{weather_data.weather_description}', 気温={weather_data.temperature}°C")
    logger.info(f"🚨 選択されたコメント: 天気='{weather_comment}', アドバイス='{advice_comment}'")
    
    # 晴天・快晴時の「変わりやすい空」は絶対に不適切 - 既存コメントから再選択
    if any(sunny in weather_data.weather_description for sunny in SUNNY_WEATHER_DESCRIPTIONS) and weather_comment:
        for pattern in CHANGEABLE_WEATHER_PATTERNS:
            if pattern in weather_comment:
                logger.warning(f"🚨 緊急修正: 晴天時に「{pattern}」は不適切 - 代替コメント検索")
                weather_comment = _find_alternative_weather_comment(
                    weather_data, state.past_comments, CHANGEABLE_WEATHER_PATTERNS
                )
                break
    
    # 雨天で熱中症警告は絶対に不適切 - 既存コメントから再選択
    if "雨" in weather_data.weather_description and weather_data.temperature < 30.0 and advice_comment and "熱中症" in advice_comment:
        logger.warning(f"🚨 緊急修正: 雨天+低温で熱中症警告を除外 - 代替アドバイス検索")
        advice_comment = _find_rain_advice(state.past_comments, advice_comment)
    
    # 大雨・嵐でムシムシ暑いは不適切 - 既存コメントから再選択
    if ("大雨" in weather_data.weather_description or "嵐" in weather_data.weather_description) and weather_comment and "ムシムシ" in weather_comment:
        logger.warning(f"🚨 緊急修正: 悪天候でムシムシコメントを除外 - 代替コメント検索")
        weather_comment = _find_storm_weather_comment(state.past_comments, weather_comment)
    
    # 連続雨判定
    is_continuous_rain = _check_continuous_rain(state)
    
    # 連続雨時に「にわか雨」表現は絶対に不適切
    if is_continuous_rain and weather_comment:
        for pattern in SHOWER_RAIN_PATTERNS:
            if pattern in weather_comment:
                logger.warning(f"🚨 緊急修正: 連続雨時に「{pattern}」は不適切 - 代替コメント検索")
                weather_comment = _find_rain_weather_comment(
                    state.past_comments, weather_comment, weather_data, avoid_shower=True
                )
                break
    
    # 雨天時に晴天表現は絶対に不適切 - 既存コメントから再選択
    if "雨" in weather_data.weather_description and weather_comment:
        sunny_inappropriate_patterns = ["晴れ", "快晴", "日差し", "太陽", "青空", "陽射し", "日向", "晴天"]
        for pattern in sunny_inappropriate_patterns:
            if pattern in weather_comment:
                logger.warning(f"🚨 緊急修正: 雨天時に晴天表現「{pattern}」は不適切 - 代替コメント検索")
                weather_comment = _find_rain_weather_comment(
                    state.past_comments, weather_comment, weather_data
                )
                break
    
    return weather_comment, advice_comment


def _find_alternative_weather_comment(
    weather_data: WeatherForecast,
    past_comments: list[PastComment | None],
    changeable_patterns: list[str]
) -> str:
    """晴天時の代替天気コメントを検索"""
    if not past_comments:
        return ""
    
    # 気温に応じた適切なコメントのパターン
    if weather_data.temperature >= 35:
        preferred_patterns = ["猛烈な暑さ", "危険な暑さ", "猛暑に警戒", "激しい暑さ"]
    elif weather_data.temperature >= 30:
        # 月を確認して残暑を除外（7月は残暑ではない）
        if state and hasattr(state, 'target_datetime'):
            month = state.target_datetime.month
            if month in [6, 7, 8]:  # 夏季
                preferred_patterns = ["厳しい暑さ", "強い日差し", "強烈な日差し", "真夏の暑さ"]
            else:  # 9月以降
                preferred_patterns = ["厳しい暑さ", "強い日差し", "厳しい残暑", "強烈な日差し"]
        else:
            preferred_patterns = ["厳しい暑さ", "強い日差し", "強烈な日差し"]
    else:
        preferred_patterns = ["爽やかな晴天", "穏やかな空", "心地よい天気", "過ごしやすい天気"]
    
    # 既存コメントから適切なものを検索
    replacement_found = False
    weather_comment = ""
    
    # 天気コメントのみをフィルタリング
    weather_comments = [c for c in past_comments if c.comment_type == CommentType.WEATHER_COMMENT]
    
    for past_comment in weather_comments:
        comment_text = past_comment.comment_text
        # 優先パターンに一致するものを探す
        for preferred in preferred_patterns:
            if preferred in comment_text:
                weather_comment = comment_text
                logger.info(f"🚨 代替コメント発見: '{weather_comment}'")
                replacement_found = True
                break
        if replacement_found:
            break
    
    # 優先パターンが見つからない場合、晴天系の任意のコメントを選択
    if not replacement_found:
        for past_comment in weather_comments:
            comment_text = past_comment.comment_text
            if any(keyword in comment_text for keyword in SUNNY_KEYWORDS) and \
               not any(ng in comment_text for ng in changeable_patterns):
                weather_comment = comment_text
                logger.info(f"🚨 晴天系代替コメント: '{weather_comment}'")
                replacement_found = True
                break
    
    # それでも見つからない場合はデフォルト（最初の有効なコメント）
    if not replacement_found and weather_comments:
        # デフォルトコメントも禁止パターンをチェック
        for past_comment in weather_comments:
            comment_text = past_comment.comment_text
            if not any(ng in comment_text for ng in changeable_patterns):
                weather_comment = comment_text
                logger.info(f"🚨 デフォルト代替（禁止ワード回避）: '{weather_comment}'")
                replacement_found = True
                break
        
        # それでも見つからない場合は、最初の有効なコメントを返す
        if not replacement_found:
            # 禁止パターンを含まない最初のコメントを返す（それも無い場合は空文字列）
            weather_comment = ""
            logger.error(f"🚨 適切な代替コメントが見つかりません")
    
    return weather_comment


def _find_rain_advice(past_comments: list[PastComment | None], current_advice: str) -> str:
    """雨天時の代替アドバイスを検索"""
    if not past_comments:
        return current_advice
    
    # アドバイスコメントのみをフィルタリング
    advice_comments = [c for c in past_comments if c.comment_type == CommentType.ADVICE]
    
    # 雨天に適したアドバイスを検索
    for past_comment in advice_comments:
        comment_text = past_comment.comment_text
        if any(pattern in comment_text for pattern in RAIN_ADVICE_PATTERNS):
            logger.info(f"🚨 雨天用代替アドバイス: '{comment_text}'")
            return comment_text
    
    # 見つからない場合はデフォルト
    if advice_comments:
        advice = advice_comments[0].comment_text
        logger.info(f"🚨 デフォルト代替アドバイス: '{advice}'")
        return advice
    
    return current_advice


def _find_storm_weather_comment(past_comments: list[PastComment | None], current_comment: str) -> str:
    """悪天候時の代替天気コメントを検索"""
    if not past_comments:
        return current_comment
    
    # 天気コメントのみをフィルタリング
    weather_comments = [c for c in past_comments if c.comment_type == CommentType.WEATHER_COMMENT]
    
    # 悪天候に適したコメントを検索
    for past_comment in weather_comments:
        comment_text = past_comment.comment_text
        if any(pattern in comment_text for pattern in STORM_WEATHER_PATTERNS):
            logger.info(f"🚨 悪天候用代替コメント: '{comment_text}'")
            return comment_text
    
    # 見つからない場合はデフォルト
    if weather_comments:
        comment = weather_comments[0].comment_text
        logger.info(f"🚨 デフォルト代替: '{comment}'")
        return comment
    
    return current_comment


def _find_rain_weather_comment(past_comments: list[PastComment | None], 
                              current_comment: str,
                              weather_data: WeatherForecast,
                              avoid_shower: bool = False) -> str:
    """雨天時の代替天気コメントを検索"""
    if not past_comments:
        return current_comment
    
    # 天気コメントのみをフィルタリング
    weather_comments = [c for c in past_comments if c.comment_type == CommentType.WEATHER_COMMENT]
    
    # 降水量に応じた適切なコメントのパターン
    rain_patterns = []
    if weather_data.precipitation >= 10:
        # 強雨時
        rain_patterns = [
            "大雨", "激しい雨", "強い雨", "本格的な雨", "豪雨",
            "荒れた天気", "悪天候", "雨が強く", "傘が必須"
        ]
    elif weather_data.precipitation >= 1:
        # 中雨時
        rain_patterns = [
            "雨が降りやすく", "雨の降りやすい", "雨模様", "雨が降ったり",
            "傘が必要", "傘をお忘れなく", "雨に注意"
        ]
    else:
        # 小雨時
        rain_patterns = [
            "にわか雨", "ニワカ雨", "急な雨", "雨が心配",
            "傘があると安心", "雨の可能性", "天気急変"
        ]
    
    # 雨関連コメントを検索
    for past_comment in weather_comments:
        comment_text = past_comment.comment_text
        
        # avoid_showerがTrueの場合、にわか雨表現をスキップ
        if avoid_shower and any(shower in comment_text for shower in SHOWER_RAIN_PATTERNS):
            continue
            
        # 優先パターンに一致するものを探す
        for pattern in rain_patterns:
            if pattern in comment_text:
                logger.info(f"🚨 雨天用代替コメント発見: '{comment_text}'")
                return comment_text
    
    # 汎用的な雨コメントを検索
    general_rain_patterns = ["雨", "傘", "濡れ"]
    for past_comment in weather_comments:
        comment_text = past_comment.comment_text
        
        # avoid_showerがTrueの場合、にわか雨表現をスキップ
        if avoid_shower and any(shower in comment_text for shower in SHOWER_RAIN_PATTERNS):
            continue
            
        if any(pattern in comment_text for pattern in general_rain_patterns):
            # 晴天表現を含まないことを確認
            if not any(sunny in comment_text for sunny in ["晴", "日差し", "太陽", "青空"]):
                logger.info(f"🚨 汎用雨天コメント: '{comment_text}'")
                return comment_text
    
    # それでも見つからない場合はデフォルト
    if weather_comments:
        logger.warning(f"🚨 適切な雨天コメントが見つかりません。最初のコメントを使用")
        return weather_comments[0].comment_text
    
    return current_comment


def _check_continuous_rain(state: CommentGenerationState) -> bool:
    """連続雨かどうかを判定"""
    if not state or not hasattr(state, 'generation_metadata') or not state.generation_metadata:
        return False
        
    period_forecasts = state.generation_metadata.get('period_forecasts', [])
    if not period_forecasts:
        return False
    
    # 天気が「雨」または降水量が0.1mm以上の時間をカウント
    rain_hours = 0
    for f in period_forecasts:
        if hasattr(f, 'weather') and '雨' in str(f.weather):
            rain_hours += 1
        elif hasattr(f, 'precipitation') and f.precipitation >= 0.1:
            rain_hours += 1
    
    is_continuous_rain = rain_hours >= CONTINUOUS_RAIN_THRESHOLD_HOURS
    
    if is_continuous_rain:
        logger.info(f"🚨 連続雨を検出: {rain_hours}時間の雨（comment_safetyでの判定）")
        # デバッグ情報
        for f in period_forecasts:
            if hasattr(f, 'datetime') and hasattr(f, 'weather'):
                time_str = f.datetime.strftime('%H時')
                weather = f.weather
                precip = f.precipitation if hasattr(f, 'precipitation') else 0
                logger.debug(f"  {time_str}: {weather}, 降水量{precip}mm")
    
    return is_continuous_rain
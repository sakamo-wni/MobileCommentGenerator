"""コメント安全性チェックモジュール"""

from typing import List, Optional, Tuple
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
    
    # LLMを使った動的な矛盾チェック
    has_contradiction = _check_dynamic_contradictions(
        weather_comment, advice_comment, weather_data, state
    )
    
    if has_contradiction:
        logger.warning("🚨 LLMが矛盾を検出 - 代替コメント検索")
        # 矛盾が検出された場合、代替コメントを検索
        weather_comment, advice_comment = _find_non_contradictory_pair(
            weather_data, state.past_comments, weather_comment, advice_comment
        )
    
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


def _find_rain_advice(past_comments: Optional[List[PastComment]], current_advice: str) -> str:
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


def _find_storm_weather_comment(past_comments: Optional[List[PastComment]], current_comment: str) -> str:
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


def _check_dynamic_contradictions(
    weather_comment: str,
    advice_comment: str,
    weather_data: WeatherForecast,
    state: CommentGenerationState
) -> bool:
    """LLMを使用して動的に矛盾をチェック"""
    
    # 簡易的な矛盾パターンを事前チェック
    simple_contradictions = [
        ("過ごしやすい", "蒸し暑い"),
        ("涼しい", "暑い"),
        ("爽やか", "じめじめ"),
        ("爽やか", "ムシムシ"),
        ("快適", "厳しい"),
        ("穏やか", "荒れ"),
        ("カラッと", "湿っぽい"),
        ("さわやか", "ムシムシ"),
        ("ひんやり", "汗ばむ"),
        ("心地よい", "不快"),
        ("過ごしやすい", "厳しい"),
        ("快適", "蒸し暑い"),
    ]
    
    combined_text = f"{weather_comment} {advice_comment}".lower()
    
    # 簡易チェック
    for word1, word2 in simple_contradictions:
        if word1 in combined_text and word2 in combined_text:
            logger.info(f"🚨 簡易矛盾検出: '{word1}' と '{word2}' が共存")
            return True
    
    # LLMプロバイダーが利用可能な場合のみLLMチェックを実行
    if hasattr(state, 'llm_provider') and state.llm_provider:
        try:
            from src.llm.llm_manager import LLMManager
            llm_manager = LLMManager(provider=state.llm_provider)
            
            prompt = f"""
以下のコメントペアに矛盾や不自然な表現の組み合わせがないかチェックしてください。

【天気情報】
- 天気: {weather_data.weather_description}
- 気温: {weather_data.temperature}°C
- 湿度: {weather_data.humidity}%
- 降水量: {weather_data.precipitation}mm

【コメント】
天気コメント: {weather_comment}
アドバイス: {advice_comment}

【チェック項目】
1. 天気コメントとアドバイスの間に矛盾がないか
2. 同一コメント内に相反する表現がないか（例：「過ごしやすいが蒸し暑い」）
3. 気温と表現が矛盾していないか（例：34°Cで「涼しい」）
4. 天気と表現が矛盾していないか（例：雨なのに「カラッと」）

矛盾がない場合は「OK」、矛盾がある場合は「NG」とだけ回答してください。
"""
            
            response = llm_manager.generate(prompt)
            response_clean = response.strip().upper()
            
            if "NG" in response_clean:
                logger.info(f"🚨 LLM矛盾検出: 天気='{weather_comment}', アドバイス='{advice_comment}'")
                return True
                
        except Exception as e:
            logger.error(f"LLM矛盾チェックエラー: {e}")
    
    return False


def _find_non_contradictory_pair(
    weather_data: WeatherForecast,
    past_comments: Optional[List[PastComment]],
    current_weather_comment: str,
    current_advice_comment: str
) -> Tuple[str, str]:
    """矛盾のないコメントペアを検索"""
    
    if not past_comments:
        return current_weather_comment, current_advice_comment
    
    # コメントをタイプ別に分類
    weather_comments = [c for c in past_comments if c.comment_type == CommentType.WEATHER_COMMENT]
    advice_comments = [c for c in past_comments if c.comment_type == CommentType.ADVICE]
    
    # 天気と気温に基づいて適切なパターンを定義
    if weather_data.temperature >= 30:
        # 暑い時は涼しい系の表現を避ける
        avoid_patterns = ["涼しい", "爽やか", "ひんやり", "過ごしやすい", "快適"]
        prefer_patterns = ["暑い", "厳しい", "猛暑", "熱中症"]
    elif weather_data.temperature <= 15:
        # 寒い時は暑い系の表現を避ける
        avoid_patterns = ["暑い", "蒸し暑い", "汗ばむ", "熱中症"]
        prefer_patterns = ["寒い", "冷える", "肌寒い", "防寒"]
    else:
        avoid_patterns = []
        prefer_patterns = ["過ごしやすい", "快適", "穏やか"]
    
    # 適切な天気コメントを検索
    selected_weather = current_weather_comment
    for comment in weather_comments:
        text = comment.comment_text
        # 避けるべきパターンが含まれていない
        if not any(avoid in text for avoid in avoid_patterns):
            # 好ましいパターンが含まれている
            if any(prefer in text for prefer in prefer_patterns):
                selected_weather = text
                logger.info(f"🚨 矛盾回避: 天気コメント変更 '{selected_weather}'")
                break
    
    # 適切なアドバイスを検索
    selected_advice = current_advice_comment
    for comment in advice_comments:
        text = comment.comment_text
        # 選択された天気コメントと矛盾しない
        if not _has_simple_contradiction(selected_weather, text):
            selected_advice = text
            logger.info(f"🚨 矛盾回避: アドバイス変更 '{selected_advice}'")
            break
    
    return selected_weather, selected_advice


def _has_simple_contradiction(text1: str, text2: str) -> bool:
    """2つのテキスト間の簡単な矛盾をチェック"""
    contradictions = [
        ("過ごしやすい", "厳しい"),
        ("涼しい", "暑い"),
        ("爽やか", "蒸し暑い"),
        ("快適", "不快"),
        ("穏やか", "激しい"),
    ]
    
    combined = f"{text1} {text2}".lower()
    for word1, word2 in contradictions:
        if word1 in combined and word2 in combined:
            return True
    
    return False
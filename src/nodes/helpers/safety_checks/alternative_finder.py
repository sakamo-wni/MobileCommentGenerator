"""代替コメント検索モジュール"""

from __future__ import annotations
import logging
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import PastComment, CommentType
from .constants import (
    SUNNY_KEYWORDS,
    RAIN_ADVICE_PATTERNS,
    STORM_WEATHER_PATTERNS,
    SHOWER_RAIN_PATTERNS
)

logger = logging.getLogger(__name__)


class AlternativeCommentFinder:
    """代替コメントを検索するクラス"""
    
    def find_alternative_weather_comment(
        self,
        weather_data: WeatherForecast,
        past_comments: list[PastComment | None],
        inappropriate_patterns: list[str],
        state: CommentGenerationState | None = None
    ) -> str:
        """晴天時の代替天気コメントを検索
        
        Args:
            weather_data: 天気予報データ
            past_comments: 過去のコメントリスト（Noneが含まれる場合は無効なコメント）
            inappropriate_patterns: 不適切な表現パターンのリスト
            state: コメント生成状態（Noneの場合は月情報が利用できない）
            
        Returns:
            適切な代替コメント。見つからない場合はデフォルトコメントを生成
        """
        if not past_comments:
            return ""
        
        # 気温に応じた適切なコメントのパターン
        preferred_patterns = self._get_temperature_patterns(weather_data.temperature, state)
        
        # 天気コメントのみをフィルタリング
        weather_comments = [c for c in past_comments if c and c.comment_type == CommentType.WEATHER_COMMENT]
        
        # 優先パターンに一致するものを探す
        for past_comment in weather_comments:
            comment_text = past_comment.comment_text
            for preferred in preferred_patterns:
                if preferred in comment_text:
                    logger.info(f"🚨 代替コメント発見: '{comment_text}'")
                    return comment_text
        
        # 優先パターンが見つからない場合、晴天系の任意のコメントを選択
        for past_comment in weather_comments:
            comment_text = past_comment.comment_text
            if any(keyword in comment_text for keyword in SUNNY_KEYWORDS) and \
               not any(ng in comment_text for ng in inappropriate_patterns):
                logger.info(f"🚨 晴天系代替コメント: '{comment_text}'")
                return comment_text
        
        # それでも見つからない場合、禁止パターンを含まないコメントを探す
        for past_comment in weather_comments:
            comment_text = past_comment.comment_text
            if not any(ng in comment_text for ng in inappropriate_patterns):
                logger.info(f"🚨 デフォルト代替（禁止ワード回避）: '{comment_text}'")
                return comment_text
        
        # 最終的なフォールバック: デフォルトコメントを生成
        logger.error(f"🚨 適切な代替コメントが見つかりません。デフォルトコメントを使用します")
        return self._generate_default_weather_comment(weather_data)
    
    def find_rain_advice(
        self,
        past_comments: list[PastComment | None],
        current_advice: str
    ) -> str:
        """雨天時の代替アドバイスを検索"""
        if not past_comments:
            return current_advice
        
        # アドバイスコメントのみをフィルタリング
        advice_comments = [c for c in past_comments if c and c.comment_type == CommentType.ADVICE]
        
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
    
    def find_storm_weather_comment(
        self,
        past_comments: list[PastComment | None],
        current_comment: str
    ) -> str:
        """悪天候時の代替天気コメントを検索"""
        if not past_comments:
            return current_comment
        
        # 天気コメントのみをフィルタリング
        weather_comments = [c for c in past_comments if c and c.comment_type == CommentType.WEATHER_COMMENT]
        
        # 悪天候に適したコメントを検索
        for past_comment in weather_comments:
            comment_text = past_comment.comment_text
            if any(pattern in comment_text for pattern in STORM_WEATHER_PATTERNS):
                logger.info(f"🚨 悪天候用代替コメント: '{comment_text}'")
                return comment_text
        
        # 見つからない場合はデフォルト
        if weather_comments:
            comment = weather_comments[0].comment_text
            logger.info(f"🚨 デフォルト代替コメント: '{comment}'")
            return comment
        
        return current_comment
    
    def find_rain_weather_comment(
        self,
        past_comments: list[PastComment | None],
        current_comment: str,
        weather_data: WeatherForecast,
        avoid_shower: bool = False
    ) -> str:
        """雨天時の代替天気コメントを検索"""
        if not past_comments:
            return current_comment
        
        # 天気コメントのみをフィルタリング
        weather_comments = [c for c in past_comments if c and c.comment_type == CommentType.WEATHER_COMMENT]
        
        # 雨に関するコメントを検索
        for past_comment in weather_comments:
            comment_text = past_comment.comment_text
            if "雨" in comment_text:
                # にわか雨表現を避ける場合
                if avoid_shower and any(shower in comment_text for shower in ["にわか", "一時的", "急な"]):
                    continue
                logger.info(f"🚨 雨天用代替コメント: '{comment_text}'")
                return comment_text
        
        return current_comment
    
    def find_cloudy_weather_comment(
        self,
        past_comments: list[PastComment | None],
        current_comment: str
    ) -> str:
        """曇天時の代替天気コメントを検索"""
        if not past_comments:
            return current_comment
        
        # 天気コメントのみをフィルタリング
        weather_comments = [c for c in past_comments if c and c.comment_type == CommentType.WEATHER_COMMENT]
        
        # 曇りに関するコメントを検索
        cloudy_keywords = ["曇", "くもり", "雲", "どんより", "グレー"]
        avoid_keywords = ["強い日差し", "太陽", "ギラギラ", "照りつける"]
        
        for past_comment in weather_comments:
            comment_text = past_comment.comment_text
            if any(cloudy in comment_text for cloudy in cloudy_keywords) and \
               not any(avoid in comment_text for avoid in avoid_keywords):
                logger.info(f"🚨 曇天用代替コメント: '{comment_text}'")
                return comment_text
        
        return current_comment
    
    def _get_temperature_patterns(
        self,
        temperature: float,
        state: CommentGenerationState | None = None
    ) -> list[str]:
        """気温に応じた適切なコメントパターンを取得"""
        if temperature >= 35:
            return ["猛烈な暑さ", "危険な暑さ", "猛暑に警戒", "激しい暑さ"]
        elif temperature >= 30:
            # 月を確認して残暑を除外
            if state and hasattr(state, 'target_datetime'):
                month = state.target_datetime.month
                if month in [6, 7, 8]:  # 夏季
                    return ["厳しい暑さ", "強い日差し", "強烈な日差し", "真夏の暑さ"]
                else:  # 9月以降
                    return ["厳しい暑さ", "強い日差し", "厳しい残暑", "強烈な日差し"]
            return ["厳しい暑さ", "強い日差し", "強烈な日差し"]
        else:
            return ["爽やかな晴天", "穏やかな空", "心地よい天気", "過ごしやすい天気"]
    
    def _generate_default_weather_comment(self, weather_data: WeatherForecast) -> str:
        """天気データに基づいてデフォルトコメントを生成
        
        過去のコメントから適切なものが見つからない場合の
        フォールバック処理として使用される。
        """
        if "雨" in weather_data.weather_description:
            if weather_data.precipitation >= 10:
                return "激しい雨に注意が必要です"
            elif weather_data.precipitation >= 2:
                return "雨が降る見込みです"
            else:
                return "小雨の可能性があります"
        elif "曇" in weather_data.weather_description:
            return "曇り空の一日となりそうです"
        elif any(sunny in weather_data.weather_description for sunny in SUNNY_KEYWORDS):
            if weather_data.temperature >= 30:
                return "晴れて暑くなりそうです"
            else:
                return "穏やかな晴天となりそうです"
        else:
            return "天気の変化にご注意ください"
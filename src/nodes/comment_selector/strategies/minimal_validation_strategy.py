"""
Minimal validation selection strategy

最低限のバリデーションによる選択戦略
"""

from __future__ import annotations

import logging
from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast

logger = logging.getLogger(__name__)


class MinimalValidationStrategy:
    """最低限のバリデーションによる選択戦略"""
    
    @staticmethod
    def select_weather_with_minimal_validation(
        comments: list[PastComment],
        weather_data: WeatherForecast
    ) -> PastComment | None:
        """最低限のバリデーションで天気コメントを選択"""
        logger.info("最低限バリデーションで天気コメントを選択")
        
        # 雨の場合
        if weather_data.precipitation > 0 or "雨" in weather_data.weather_description:
            rain_keywords = ["雨", "降水", "傘"]
            for comment in comments:
                if any(keyword in comment.comment_text for keyword in rain_keywords):
                    logger.info(f"雨関連コメントを選択: '{comment.comment_text}'")
                    return comment
        
        # 嵐・台風の場合
        if any(word in weather_data.weather_description.lower() for word in ["嵐", "台風", "storm", "typhoon"]):
            storm_keywords = ["嵐", "台風", "荒", "強風", "暴風"]
            for comment in comments:
                if any(keyword in comment.comment_text for keyword in storm_keywords):
                    logger.info(f"嵐関連コメントを選択: '{comment.comment_text}'")
                    return comment
        
        # 天気キーワードが含まれるものを選択
        weather_keywords = ["晴", "曇", "雨", "雪", "風", "天気", "空", "太陽"]
        for comment in comments:
            if any(keyword in comment.comment_text for keyword in weather_keywords):
                logger.info(f"天気キーワードを含むコメントを選択: '{comment.comment_text}'")
                return comment
        
        # 最後の手段：最初のコメント
        if comments:
            logger.warning(f"適切なキーワードが見つからず、最初のコメントを選択: '{comments[0].comment_text}'")
            return comments[0]
        
        return None
    
    @staticmethod
    def select_advice_with_minimal_validation(
        comments: list[PastComment],
        weather_data: WeatherForecast
    ) -> PastComment | None:
        """最低限のバリデーションでアドバイスコメントを選択"""
        logger.info("最低限バリデーションでアドバイスコメントを選択")
        
        # 雨の場合
        if weather_data.precipitation > 0 or "雨" in weather_data.weather_description:
            rain_advice_keywords = ["傘", "雨具", "濡れ", "雨対策"]
            for comment in comments:
                if any(keyword in comment.comment_text for keyword in rain_advice_keywords):
                    logger.info(f"雨関連アドバイスを選択: '{comment.comment_text}'")
                    return comment
        
        # 嵐・台風の場合
        if any(word in weather_data.weather_description.lower() for word in ["嵐", "台風", "storm", "typhoon"]):
            # 「台風対策を」などのコメントも含む
            storm_advice_keywords = ["台風", "嵐", "安全", "対策", "警戒", "注意", "備え"]
            for comment in comments:
                if any(keyword in comment.comment_text for keyword in storm_advice_keywords):
                    logger.info(f"嵐関連アドバイスを選択: '{comment.comment_text}'")
                    return comment
        
        # 高温の場合
        if weather_data.temperature >= 30:
            heat_advice_keywords = ["暑さ", "熱中症", "水分", "冷房", "涼し"]
            for comment in comments:
                if any(keyword in comment.comment_text for keyword in heat_advice_keywords):
                    logger.info(f"暑さ関連アドバイスを選択: '{comment.comment_text}'")
                    return comment
        
        # アドバイスキーワードが含まれるものを選択
        advice_keywords = ["対策", "注意", "備え", "準備", "服装", "持ち物", "おすすめ"]
        for comment in comments:
            if any(keyword in comment.comment_text for keyword in advice_keywords):
                logger.info(f"アドバイスキーワードを含むコメントを選択: '{comment.comment_text}'")
                return comment
        
        # 最後の手段：最初のコメント
        if comments:
            logger.warning(f"適切なキーワードが見つからず、最初のコメントを選択: '{comments[0].comment_text}'")
            return comments[0]
        
        return None
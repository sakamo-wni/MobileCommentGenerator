"""天気コメント検証システム - メインバリデータ"""

import logging
from typing import List, Dict, Any, Tuple, Optional, TypedDict
from datetime import datetime

from src.config.weather_constants import (
    HEATSTROKE_WARNING_TEMP,
    HEATSTROKE_SEVERE_TEMP,
)
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.past_comment import PastComment, CommentType
from .base_validator import BaseValidator
from .weather_validator import WeatherValidator
from .temperature_validator import TemperatureValidator
from .consistency_validator import ConsistencyValidator
from .regional_validator import RegionalValidator

logger = logging.getLogger(__name__)


class RequiredKeywords(TypedDict):
    """必須キーワードの型定義"""
    weather_comment: List[str]
    advice: List[str]


class WeatherCommentValidator:
    """天気条件に基づいてコメントの適切性を検証するメインクラス"""
    
    def __init__(self):
        # 各バリデータのインスタンスを作成
        self.weather_validator = WeatherValidator()
        self.temperature_validator = TemperatureValidator()
        self.consistency_validator = ConsistencyValidator()
        self.regional_validator = RegionalValidator()
        
        # 必須キーワード（悪天候時）
        self.required_keywords: Dict[str, RequiredKeywords] = {
            "heavy_rain": {
                "weather_comment": ["注意", "警戒", "危険", "荒れ", "激しい", "強い", "本格的"],
                "advice": ["傘", "雨具", "安全", "注意", "室内", "控え", "警戒", "備え", "準備"]
            },
            "storm": {
                "weather_comment": ["嵐", "暴風", "警戒", "危険", "荒天", "大荒れ"],
                "advice": ["危険", "外出控え", "安全確保", "警戒", "室内", "備え", "準備"]
            }
        }
    
    def validate_comment(self, comment: PastComment, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """
        天気コメントの適切性を総合的に検証
        
        Args:
            comment: 検証対象のコメント
            weather_data: 天気データ
            
        Returns:
            (is_valid, reason): 検証結果とその理由
        """
        comment_type = comment.comment_type.value
        comment_text = comment.comment_text
        
        # 1. 天気条件チェック
        weather_check = self.weather_validator.validate(comment, weather_data)
        if not weather_check[0]:
            logger.info(f"天気条件エラー: {weather_check[1]} - コメント: '{comment_text}'")
            return weather_check
        
        # 2. 温度条件チェック
        temp_check = self.temperature_validator.validate(comment, weather_data)
        if not temp_check[0]:
            logger.info(f"温度条件エラー: {temp_check[1]} - コメント: '{comment_text}'")
            return temp_check
        
        # 3. 地域特性チェック
        regional_check = self.regional_validator.validate(comment, weather_data)
        if not regional_check[0]:
            logger.info(f"地域特性エラー: {regional_check[1]} - コメント: '{comment_text}'")
            return regional_check
        
        # 4. 必須キーワードチェック
        required_check = self._check_required_keywords(
            comment_text, comment_type, weather_data
        )
        if not required_check[0]:
            logger.info(f"必須キーワードエラー: {required_check[1]} - コメント: '{comment_text}'")
            return required_check
        
        return True, "検証OK"
    
    def _check_required_keywords(self, comment_text: str, comment_type: str,
                               weather_data: WeatherForecast) -> Tuple[bool, str]:
        """必須キーワードのチェック"""
        weather_desc = weather_data.weather_description.lower()
        
        # 大雨・豪雨時のチェック
        if any(word in weather_desc for word in ["豪雨", "大雨", "暴風雨"]):
            if "heavy_rain" in self.required_keywords:
                required = self.required_keywords["heavy_rain"].get(comment_type, [])
                if required and not any(keyword in comment_text for keyword in required):
                    return False, f"大雨時の必須キーワードが不足: {required}"
        
        # 嵐・台風時のチェック
        if any(word in weather_desc for word in ["嵐", "台風", "storm", "typhoon"]):
            if "storm" in self.required_keywords:
                required = self.required_keywords["storm"].get(comment_type, [])
                if required and not any(keyword in comment_text for keyword in required):
                    return False, f"嵐時の必須キーワードが不足: {required}"
        
        return True, ""
    
    def validate_comment_pair_consistency(
        self, 
        weather_comment: str, 
        advice_comment: str, 
        weather_data: WeatherForecast
    ) -> Tuple[bool, str]:
        """
        天気コメントとアドバイスの一貫性をチェック
        
        Args:
            weather_comment: 天気コメント
            advice_comment: アドバイスコメント
            weather_data: 天気データ
            
        Returns:
            (is_consistent, reason): 一貫性チェック結果とその理由
        """
        return self.consistency_validator.validate_comment_pair_consistency(
            weather_comment, advice_comment, weather_data
        )
    
    def filter_comments(self, comments: List[PastComment], 
                       weather_data: WeatherForecast) -> List[PastComment]:
        """
        天気条件に基づいてコメントをフィルタリング
        
        Args:
            comments: フィルタリング対象のコメントリスト
            weather_data: 天気データ
            
        Returns:
            適切なコメントのリスト
        """
        valid_comments = []
        
        for comment in comments:
            is_valid, reason = self.validate_comment(comment, weather_data)
            if is_valid:
                valid_comments.append(comment)
            else:
                logger.info(f"コメント除外: '{comment.comment_text}' - 理由: {reason}")
        
        # 有効なコメントが少なすぎる場合の警告
        if len(valid_comments) < len(comments) * 0.1:  # 90%以上除外された場合
            logger.warning(f"大量のコメントが除外されました: {len(comments)}件中{len(valid_comments)}件のみ有効")
        
        return valid_comments
    
    def get_weather_appropriate_comments(self, comments: List[PastComment],
                                       weather_data: WeatherForecast,
                                       comment_type: CommentType,
                                       limit: int = 30) -> List[PastComment]:
        """
        天気に適したコメントを優先度順に取得
        
        Args:
            comments: 候補コメントリスト
            weather_data: 天気データ
            limit: 取得する最大コメント数
            
        Returns:
            優先度順にソートされた適切なコメントリスト
        """
        # まず有効なコメントをフィルタリング
        valid_comments = self.filter_comments(comments, weather_data)
        
        # スコアを計算してソート
        scored_comments = []
        for comment in valid_comments:
            score = self._calculate_appropriateness_score(comment, weather_data)
            scored_comments.append((score, comment))
        
        # スコアの高い順にソート
        scored_comments.sort(key=lambda x: x[0], reverse=True)
        
        # 上位のコメントを返す
        return [comment for score, comment in scored_comments[:limit]]
    
    def _calculate_appropriateness_score(self, comment: PastComment, 
                                       weather_data: WeatherForecast) -> float:
        """
        コメントの適切性スコアを計算
        
        Args:
            comment: 評価対象のコメント
            weather_data: 天気データ
            
        Returns:
            適切性スコア（0.0～1.0）
        """
        score = 0.5  # 基準スコア
        
        # 天気条件の一致度
        weather_desc = weather_data.weather_description.lower()
        comment_text = comment.comment_text.lower()
        
        # 天気キーワードの一致
        weather_keywords = {
            "晴": ["晴", "快晴", "日差し", "青空"],
            "曇": ["曇", "くもり", "雲"],
            "雨": ["雨", "降雨", "傘"],
            "雪": ["雪", "積雪", "降雪"]
        }
        
        for weather_type, keywords in weather_keywords.items():
            if any(keyword in weather_desc for keyword in keywords):
                matching_keywords = sum(1 for keyword in keywords if keyword in comment_text)
                score += matching_keywords * 0.1
        
        # 温度の適切性
        temp = weather_data.temperature
        if temp >= HEATSTROKE_SEVERE_TEMP and "熱中症" in comment_text:
            score += 0.2
        elif temp <= 10 and any(word in comment_text for word in ["寒", "冷え", "防寒"]):
            score += 0.2
        
        # 時間帯の適切性
        hour = weather_data.datetime.hour
        if 6 <= hour <= 9 and "朝" in comment_text:
            score += 0.1
        elif 11 <= hour <= 14 and "昼" in comment_text:
            score += 0.1
        elif 17 <= hour <= 20 and "夕" in comment_text:
            score += 0.1
        
        # 季節の適切性
        month = weather_data.datetime.month
        season = self._get_season_from_month(month)
        if season in comment_text:
            score += 0.1
        
        # スコアを0.0～1.0の範囲に正規化
        return min(max(score, 0.0), 1.0)
    
    def _get_season_from_month(self, month: int) -> str:
        """月から季節を判定"""
        if month in [3, 4, 5]:
            return "春"
        elif month == 6:
            return "梅雨"
        elif month in [7, 8]:
            return "夏"
        elif month == 9:
            return "台風"
        elif month in [10, 11]:
            return "秋"
        else:  # 12, 1, 2
            return "冬"
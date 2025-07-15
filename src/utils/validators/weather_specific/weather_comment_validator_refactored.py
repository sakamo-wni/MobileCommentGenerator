"""リファクタリングされた天気コメントバリデーター - ファサードパターンで各バリデーターを統合"""

from __future__ import annotations

import logging
from typing import Tuple, TYPE_CHECKING, Named
from datetime import datetime

if TYPE_CHECKING:
    from src.data.weather_data import WeatherForecast
    from src.data.past_comment import PastComment, CommentType

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment, CommentType
from src.utils.validators.weather_specific.weather_condition_validator import WeatherConditionValidator
from src.utils.validators.weather_specific.temperature_condition_validator import TemperatureConditionValidator
from src.utils.validators.weather_specific.regional_specifics_validator import RegionalSpecificsValidator
from src.utils.validators.weather_specific.consistency_validator import ConsistencyValidator

logger = logging.getLogger(__name__)


class ValidationResult(NamedTuple):
    """バリデーション結果を表す名前付きタプル"""
    is_valid: bool
    reason: str


class AppropriatessScore(NamedTuple):
    """適切性スコアの詳細"""
    total_score: float
    weather_match_score: float
    temperature_match_score: float
    season_match_score: float
    usage_penalty: float
    regional_bonus: float


class WeatherCommentValidatorRefactored:
    """天気条件に基づいてコメントの適切性を検証するファサードクラス"""
    
    def __init__(self):
        # 各種バリデーターの初期化
        self.weather_validator = WeatherConditionValidator()
        self.temperature_validator = TemperatureConditionValidator()
        self.regional_validator = RegionalSpecificsValidator()
        self.consistency_validator = ConsistencyValidator()
    
    def validate_comment(
        self, 
        comment: PastComment, 
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """
        コメントを天気条件に基づいて検証
        
        Args:
            comment: 検証対象のコメント
            weather_data: 天気予報データ
            
        Returns:
            (is_valid, reason): 検証結果とその理由
        """
        comment_text = comment.comment_text
        comment_type = "weather_comment" if comment.comment_type == CommentType.WEATHER_COMMENT else "advice"
        
        # 基本的な天気コメント禁止ワードチェック
        if comment.comment_type == CommentType.WEATHER_COMMENT:
            basic_forbidden = ["コメント", "アドバイス", "メッセージ"]
            for word in basic_forbidden:
                if word in comment_text:
                    return False, f"天気コメントに「{word}」は不適切"
        
        # 1. 天気条件チェック
        weather_check = self.weather_validator.check_weather_conditions(
            comment_text, comment_type, weather_data.weather_description
        )
        if not weather_check[0]:
            return weather_check
        
        # 2. 温度条件チェック
        temp_check = self.temperature_validator.check_temperature_conditions(
            comment_text, comment_type, weather_data.temperature
        )
        if not temp_check[0]:
            return temp_check
        
        # 3. 湿度条件チェック（高湿度の場合）
        if hasattr(weather_data, 'humidity') and weather_data.humidity:
            humidity_check = self._check_humidity_conditions(
                comment_text, comment_type, weather_data.humidity
            )
            if not humidity_check[0]:
                return humidity_check
        
        # 4. 必須キーワードチェック（特定の天気条件下）
        required_check = self._check_required_keywords(
            comment_text, comment_type, weather_data
        )
        if not required_check[0]:
            return required_check
        
        # 5. 雨天時の矛盾チェック
        rainy_check = self.weather_validator.check_rainy_weather_contradictions(
            comment_text, weather_data.weather_description
        )
        if not rainy_check[0]:
            return rainy_check
        
        # 6. 地域特性チェック
        if hasattr(comment, 'location') and comment.location:
            regional_check = self.regional_validator.check_regional_specifics(
                comment_text, comment.location
            )
            if not regional_check[0]:
                return regional_check
        
        return True, "検証OK"
    
    def validate_comment_pair_consistency(
        self, 
        weather_comment: str, 
        advice_comment: str, 
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """天気コメントとアドバイスの一貫性を包括的にチェック"""
        # 1. 天気と現実の矛盾チェック
        weather_reality_check = self.consistency_validator.check_weather_reality_contradiction(
            weather_comment, weather_data
        )
        if not weather_reality_check[0]:
            return weather_reality_check
        
        # 2. 温度と症状の矛盾チェック
        temp_symptom_check = self.temperature_validator.check_temperature_symptom_contradiction(
            weather_comment, advice_comment, weather_data
        )
        if not temp_symptom_check[0]:
            return temp_symptom_check
        
        # 3. 重複・類似表現チェック
        duplication_check = self.consistency_validator.check_content_duplication(
            weather_comment, advice_comment
        )
        if not duplication_check[0]:
            return duplication_check
        
        # 4. 矛盾する態度・トーンチェック
        tone_contradiction_check = self.consistency_validator.check_tone_contradiction(
            weather_comment, advice_comment, weather_data
        )
        if not tone_contradiction_check[0]:
            return tone_contradiction_check
        
        return True, "コメントペアの一貫性OK"
    
    def filter_comments(
        self, 
        comments: list[PastComment], 
        weather_data: WeatherForecast
    ) -> list[PastComment]:
        """
        コメントリストから天気条件に適合するものをフィルタリング
        
        Args:
            comments: フィルタリング対象のコメントリスト
            weather_data: 天気予報データ
            
        Returns:
            適合するコメントのリスト
        """
        valid_comments = []
        
        for comment in comments:
            is_valid, reason = self.validate_comment(comment, weather_data)
            if is_valid:
                valid_comments.append(comment)
            else:
                logger.debug(f"コメントをフィルタ: {reason} - {comment.comment_text[:30]}...")
        
        logger.info(f"フィルタリング結果: {len(comments)} → {len(valid_comments)} コメント")
        return valid_comments
    
    def get_weather_appropriate_comments(
        self, 
        comments: list[PastComment],
        weather_data: WeatherForecast,
        max_results: int = 10
    ) -> list[PastComment]:
        """
        天気条件に最も適したコメントを取得
        
        Args:
            comments: 候補となるコメントリスト
            weather_data: 天気予報データ
            max_results: 返す最大コメント数
            
        Returns:
            適切なコメントのリスト（スコア順）
        """
        # まず基本的なフィルタリング
        valid_comments = self.filter_comments(comments, weather_data)
        
        # スコアリング
        scored_comments = []
        for comment in valid_comments:
            score_result = self._calculate_appropriateness_score(comment, weather_data)
            scored_comments.append((score_result.total_score, comment))
        
        # スコアでソート（降順）
        scored_comments.sort(key=lambda x: x[0], reverse=True)
        
        # 上位N件を返す
        return [comment for _, comment in scored_comments[:max_results]]
    
    def _check_humidity_conditions(
        self, 
        comment_text: str, 
        comment_type: str,
        humidity: float
    ) -> tuple[bool, str]:
        """湿度条件に基づく検証（シンプル版）"""
        # 高湿度時（70%以上）
        if humidity >= 70:
            inappropriate_words = ["カラッと", "さっぱり", "爽やか", "乾燥"]
            for word in inappropriate_words:
                if word in comment_text:
                    return False, f"高湿度（{humidity}%）で「{word}」は不適切"
        
        # 低湿度時（30%以下）
        elif humidity <= 30:
            inappropriate_words = ["じめじめ", "蒸し暑い", "湿った", "べたつく"]
            for word in inappropriate_words:
                if word in comment_text:
                    return False, f"低湿度（{humidity}%）で「{word}」は不適切"
        
        return True, "湿度条件チェックOK"
    
    def _check_required_keywords(
        self, 
        comment_text: str, 
        comment_type: str,
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """必須キーワードの存在チェック（シンプル版）"""
        weather_desc = weather_data.weather_description.lower()
        
        # 大雨・豪雨時は警告が必須
        if any(word in weather_desc for word in ["豪雨", "大雨", "暴風雨"]):
            if comment_type == "advice":
                warning_words = ["注意", "警戒", "気をつけ", "お気をつけ", "安全"]
                if not any(word in comment_text for word in warning_words):
                    return False, "大雨時のアドバイスには警告表現が必要"
        
        # 猛暑時は熱中症への言及が必要
        if weather_data.temperature >= 35:
            if comment_type == "advice":
                heat_words = ["熱中症", "水分", "涼しい", "休憩", "無理をしない"]
                if not any(word in comment_text for word in heat_words):
                    return False, "猛暑時のアドバイスには熱中症対策が必要"
        
        return True, "必須キーワードチェックOK"
    
    def _calculate_appropriateness_score(
        self, 
        comment: PastComment, 
        weather_data: WeatherForecast
    ) -> AppropriatessScore:
        """コメントの適切性スコアを計算（0-100）"""
        base_score = 50.0  # 基本スコア
        weather_match_score = 0.0
        temperature_match_score = 0.0
        season_match_score = 0.0
        usage_penalty = 0.0
        regional_bonus = 0.0
        
        # 1. 天気の一致度
        comment_weather = comment.weather_condition.lower()
        actual_weather = weather_data.weather_description.lower()
        
        # 完全一致
        if comment_weather == actual_weather:
            weather_match_score = 20.0
        # 部分一致
        elif any(word in comment_weather for word in actual_weather.split()) or \
             any(word in actual_weather for word in comment_weather.split()):
            weather_match_score = 10.0
        
        # 2. 温度の近似度（±3°C以内）
        if hasattr(comment, 'temperature') and comment.temperature:
            temp_diff = abs(comment.temperature - weather_data.temperature)
            if temp_diff <= 1:
                temperature_match_score = 15.0
            elif temp_diff <= 3:
                temperature_match_score = 10.0
            elif temp_diff <= 5:
                temperature_match_score = 5.0
        
        # 3. 季節の一致
        current_season = self._get_season_from_month(datetime.now().month)
        if hasattr(comment, 'season') and comment.season == current_season:
            season_match_score = 10.0
        
        # 4. 使用回数によるペナルティ
        if hasattr(comment, 'usage_count') and comment.usage_count > 5:
            usage_penalty = min(comment.usage_count * 2, 20)
        
        # 5. 地域特性ボーナス
        if hasattr(comment, 'location') and comment.location:
            if weather_data.location and comment.location in weather_data.location:
                regional_bonus = 5.0
        
        # 総合スコアの計算
        total_score = base_score + weather_match_score + temperature_match_score + \
                     season_match_score - usage_penalty + regional_bonus
        total_score = max(0.0, min(100.0, total_score))
        
        return AppropriatessScore(
            total_score=total_score,
            weather_match_score=weather_match_score,
            temperature_match_score=temperature_match_score,
            season_match_score=season_match_score,
            usage_penalty=usage_penalty,
            regional_bonus=regional_bonus
        )
    
    def _get_season_from_month(self, month: int) -> str:
        """月から季節を判定"""
        if month in [3, 4, 5]:
            return "春"
        elif month in [6, 7, 8]:
            if month == 6:
                return "梅雨"
            else:
                return "夏"
        elif month in [9, 10, 11]:
            return "秋"
        else:
            return "冬"
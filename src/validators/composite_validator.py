"""複合検証モジュール - すべての検証を統合"""

import logging
from typing import List, Dict, Any, Tuple, Optional

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment, CommentType
from src.data.comment_pair import CommentPair
from src.validators.weather_validator import WeatherValidator
from src.validators.temperature_validator import TemperatureValidator
from src.validators.humidity_validator import HumidityValidator
from src.validators.consistency_validator import ConsistencyValidator

logger = logging.getLogger(__name__)


class WeatherCommentValidator:
    """天気条件に基づいてコメントの適切性を検証する統合クラス"""
    
    def __init__(self):
        """各種バリデーターを初期化"""
        self.weather_validator = WeatherValidator()
        self.temperature_validator = TemperatureValidator()
        self.humidity_validator = HumidityValidator()
        self.consistency_validator = ConsistencyValidator()
        
        # 基底クラスから共通データを参照
        self.required_keywords = self.weather_validator.required_keywords
        self.regional_keywords = self.weather_validator.regional_keywords
    
    def validate_comment(self, comment: PastComment, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """コメントの妥当性を検証
        
        Args:
            comment: 検証対象のコメント
            weather_data: 天気予報データ
            
        Returns:
            (is_valid, reason): 検証結果とその理由
        """
        try:
            comment_text = comment.text
            comment_type = "weather_comment" if comment.comment_type == CommentType.WEATHER else "advice"
            
            # 1. 天気条件チェック
            is_valid, reason = self.weather_validator.check_weather_conditions(
                comment_text, comment_type, weather_data
            )
            if not is_valid:
                logger.debug(f"天気条件チェックで除外: {reason}")
                return False, reason
            
            # 2. 気温条件チェック
            is_valid, reason = self.temperature_validator.check_temperature_conditions(
                comment_text, comment_type, weather_data
            )
            if not is_valid:
                logger.debug(f"気温条件チェックで除外: {reason}")
                return False, reason
            
            # 3. 湿度条件チェック
            is_valid, reason = self.humidity_validator.check_humidity_conditions(
                comment_text, comment_type, weather_data
            )
            if not is_valid:
                logger.debug(f"湿度条件チェックで除外: {reason}")
                return False, reason
            
            # 4. 必須キーワードチェック
            is_valid, reason = self._check_required_keywords(
                comment_text, comment_type, weather_data
            )
            if not is_valid:
                logger.debug(f"必須キーワードチェックで除外: {reason}")
                return False, reason
            
            # 5. 地域特有チェック（location情報があれば）
            # ※実装では通常locationは別途渡される
            
            return True, ""
            
        except Exception as e:
            logger.error(f"コメント検証中にエラー: {e}")
            return False, f"検証エラー: {str(e)}"
    
    def _check_required_keywords(self, comment_text: str, comment_type: str,
                                weather_data: WeatherForecast) -> Tuple[bool, str]:
        """必須キーワードの存在をチェック"""
        for keyword, requirements in self.required_keywords.items():
            if keyword in comment_text:
                required_words = requirements.get(comment_type, [])
                if required_words:
                    # いずれかの必須ワードが含まれているかチェック
                    if not any(word in comment_text for word in required_words):
                        return False, f"'{keyword}'を含む場合、関連キーワードが必要"
        
        return True, ""
    
    def _check_regional_specifics(self, comment_text: str, location: str) -> Tuple[bool, str]:
        """地域特有の表現をチェック"""
        if not location:
            return True, ""
        
        # 地域特有のキーワードチェック
        for region, keywords in self.regional_keywords.items():
            if region in location:
                # 他地域のキーワードが含まれていないかチェック
                for other_region, other_keywords in self.regional_keywords.items():
                    if other_region != region:
                        for keyword in other_keywords:
                            if keyword in comment_text and keyword not in keywords:
                                # 例外: 「雪」は冬季なら全国で使用可能
                                month = weather_data.date.month
                                if keyword == "雪" and month in [12, 1, 2, 3]:
                                    continue
                                return False, f"{location}で'{keyword}'は不適切な可能性"
        
        return True, ""
    
    def validate_comment_pair_consistency(self, comment_pair: CommentPair, 
                                        weather_data: WeatherForecast,
                                        location: Optional[str] = None) -> Tuple[bool, str]:
        """天気コメントとアドバイスの一貫性をチェック"""
        return self.consistency_validator.validate_comment_pair_consistency(
            comment_pair, weather_data, location
        )
    
    def filter_comments(self, comments: List[PastComment], 
                       weather_data: WeatherForecast) -> List[PastComment]:
        """天気条件に基づいてコメントリストをフィルタリング
        
        Args:
            comments: フィルタリング対象のコメントリスト
            weather_data: 天気予報データ
            
        Returns:
            適切なコメントのみのリスト
        """
        filtered_comments = []
        
        for comment in comments:
            is_valid, reason = self.validate_comment(comment, weather_data)
            if is_valid:
                filtered_comments.append(comment)
            else:
                logger.debug(f"コメント除外: {comment.text[:20]}... - 理由: {reason}")
        
        logger.info(f"フィルタリング結果: {len(comments)} → {len(filtered_comments)} コメント")
        return filtered_comments
    
    def get_weather_appropriate_comments(self, comments: List[PastComment],
                                       weather_data: WeatherForecast,
                                       limit: int = 10) -> List[PastComment]:
        """天気に適したコメントを優先度順に取得
        
        Args:
            comments: コメントリスト
            weather_data: 天気予報データ
            limit: 取得する最大コメント数
            
        Returns:
            適切性スコアが高い順のコメントリスト
        """
        # まず不適切なコメントを除外
        valid_comments = self.filter_comments(comments, weather_data)
        
        # 適切性スコアを計算してソート
        scored_comments = []
        for comment in valid_comments:
            score = self._calculate_appropriateness_score(comment, weather_data)
            scored_comments.append((score, comment))
        
        # スコアの高い順にソート
        scored_comments.sort(key=lambda x: x[0], reverse=True)
        
        # 上位のコメントを返す
        return [comment for _, comment in scored_comments[:limit]]
    
    def _calculate_appropriateness_score(self, comment: PastComment, 
                                       weather_data: WeatherForecast) -> float:
        """コメントの適切性スコアを計算
        
        天気条件との一致度、季節の適合性、具体性などを総合的に評価
        """
        score = 0.0
        comment_text = comment.text
        
        # 天気キーワードの一致
        weather_str = weather_data.weather.value
        weather_keywords = weather_str.split()
        for keyword in weather_keywords:
            if keyword in comment_text:
                score += 10.0
        
        # 気温の適合性
        temp = weather_data.temperature
        if temp >= 30:
            hot_keywords = ["暑", "熱", "猛暑", "酷暑"]
            score += sum(5.0 for k in hot_keywords if k in comment_text)
        elif temp <= 10:
            cold_keywords = ["寒", "冷", "冷え込み"]
            score += sum(5.0 for k in cold_keywords if k in comment_text)
        
        # 季節の適合性
        month = weather_data.date.month
        season = self._get_season_from_month(month)
        season_keywords = {
            "spring": ["春", "桜", "花粉", "新緑"],
            "summer": ["夏", "暑", "熱中症", "紫外線"],
            "autumn": ["秋", "紅葉", "涼しい", "過ごしやすい"],
            "winter": ["冬", "寒", "防寒", "インフルエンザ"]
        }
        
        if season in season_keywords:
            for keyword in season_keywords[season]:
                if keyword in comment_text:
                    score += 8.0
        
        # 具体性ボーナス
        if any(char.isdigit() for char in comment_text):  # 数字が含まれる
            score += 3.0
        
        # コメントタイプによる調整
        if comment.comment_type == CommentType.ADVICE:
            # アドバイスは実用性を重視
            action_keywords = ["しましょう", "ください", "注意", "対策", "準備"]
            score += sum(2.0 for k in action_keywords if k in comment_text)
        
        return score
    
    def _get_season_from_month(self, month: int) -> str:
        """月から季節を判定"""
        return self.weather_validator._get_season_from_month(month)
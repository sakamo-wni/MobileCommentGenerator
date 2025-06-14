"""天気コメント検証システム - 天気条件に不適切なコメントを検出・除外"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.past_comment import PastComment, CommentType
from src.config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class WeatherCommentValidator:
    """天気条件に基づいてコメントの適切性を検証"""
    
    def __init__(self):
        # 設定ファイルから検証ルールを読み込み
        config = ConfigLoader.load_config("validation_rules.yaml")
        
        # 天気別禁止ワードの定義
        self.weather_forbidden_words = config.get("weather_forbidden_words", {})
        
        # 温度別禁止ワード
        self.temperature_forbidden_words = config.get("temperature_forbidden_words", {})
        
        # 必須キーワード（悪天候時）
        self.required_keywords = config.get("required_keywords", {})
        
        # 地域別NG表現
        self.regional_ng_expressions = config.get("regional_ng_expressions", {})
        
        # 湿度別禁止ワード
        self.humidity_forbidden_words = config.get("humidity_forbidden_words", {})
        
        # 閾値設定
        self.thresholds = config.get("thresholds", {
            "temperature": {"hot": 30, "cold": 12, "mild_min": 10, "mild_max": 30},
            "humidity": {"high": 80, "low": 30},
            "precipitation": {"light": 3.0, "moderate": 10.0, "heavy": 20.0, "very_heavy": 50.0},
            "thunder": {"light_threshold": 5.0}
        })
        
        # 過度な警戒表現
        self.excessive_warning_words = config.get("excessive_warning_words", {})
    
    def validate_comment(self, comment: PastComment, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """
        コメントが天気条件に適しているか検証
        
        Returns:
            (is_valid, reason): 検証結果とその理由
        """
        comment_text = comment.comment_text
        comment_type = comment.comment_type.value
        
        # 1. 天気条件チェック
        weather_check = self._check_weather_conditions(comment_text, comment_type, weather_data)
        if not weather_check[0]:
            return weather_check
        
        # 2. 温度条件チェック
        temp_check = self._check_temperature_conditions(comment_text, weather_data)
        if not temp_check[0]:
            return temp_check
        
        # 2.5. 地域特性チェック（位置情報がある場合）
        if hasattr(weather_data, 'location') and weather_data.location:
            regional_check = self._check_regional_specifics(comment_text, weather_data.location)
            if not regional_check[0]:
                return regional_check
        
        # 3. 湿度条件チェック
        humidity_check = self._check_humidity_conditions(comment_text, weather_data)
        if not humidity_check[0]:
            return humidity_check
        
        # 4. 必須キーワードチェック（悪天候時）
        required_check = self._check_required_keywords(comment_text, comment_type, weather_data)
        if not required_check[0]:
            return required_check
        
        # 5. 雨天時の矛盾表現チェック
        contradiction_check = self._check_rainy_weather_contradictions(comment_text, weather_data)
        if not contradiction_check[0]:
            return contradiction_check
        
        return True, "OK"
    
    def _check_weather_conditions(self, comment_text: str, comment_type: str, 
                                 weather_data: WeatherForecast) -> Tuple[bool, str]:
        """天気条件に基づく検証"""
        weather_desc = weather_data.weather_description.lower()
        comment_lower = comment_text.lower()
        precipitation = weather_data.precipitation
        
        # 降水量レベルを取得
        precipitation_severity = weather_data.get_precipitation_severity()
        
        # 大雨・嵐チェック
        if any(severe in weather_desc for severe in ["大雨", "豪雨", "嵐", "暴風", "台風"]):
            forbidden_words = self.weather_forbidden_words["heavy_rain"][comment_type]
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"悪天候時の禁止ワード「{word}」を含む"
        
        # 雷の特別チェック（降水量を考慮）
        elif "雷" in weather_desc:
            thunder_threshold = self.thresholds.get("thunder", {}).get("light_threshold", 5.0)
            if precipitation >= thunder_threshold:
                # 強い雷（降水量5mm以上）
                forbidden_words = self.weather_forbidden_words["heavy_rain"][comment_type]
                for word in forbidden_words:
                    if word in comment_text:
                        return False, f"強い雷雨時の禁止ワード「{word}」を含む"
            else:
                # 軽微な雷（設定閾値未満）
                if comment_type in self.excessive_warning_words:
                    for word in self.excessive_warning_words[comment_type]:
                        if word in comment_text:
                            return False, f"軽微な雷（{precipitation}mm）で過度な警戒表現「{word}」を含む"
        
        # 通常の雨チェック（降水量レベルで判定）
        elif any(rain in weather_desc for rain in ["雨", "rain"]):
            if precipitation_severity in ["heavy", "very_heavy"]:
                # 大雨・激しい雨
                forbidden_words = self.weather_forbidden_words["heavy_rain"][comment_type]
            else:
                # 軽い雨～中程度の雨
                forbidden_words = self.weather_forbidden_words["rain"][comment_type]
            
            for word in forbidden_words:
                if word in comment_text:
                    severity_desc = "大雨" if precipitation_severity in ["heavy", "very_heavy"] else "雨天"
                    return False, f"{severity_desc}時の禁止ワード「{word}」を含む"
            
            # 軽い雨では強い警戒表現を禁止
            if precipitation_severity == "light" and comment_type == "weather_comment":
                strong_warning_words = ["激しい", "警戒", "危険", "大荒れ", "本格的", "強雨"]
                for word in strong_warning_words:
                    if word in comment_text:
                        return False, f"軽い雨（{precipitation}mm）で過度な警戒表現「{word}」を含む"
        
        # 晴天チェック
        elif any(sunny in weather_desc for sunny in ["晴", "快晴"]):
            forbidden_words = self.weather_forbidden_words["sunny"][comment_type]
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"晴天時の禁止ワード「{word}」を含む"
        
        # 曇天チェック
        elif "曇" in weather_desc or "くもり" in weather_desc:
            forbidden_words = self.weather_forbidden_words["cloudy"][comment_type]
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"曇天時の禁止ワード「{word}」を含む"
            
            # 曇天時に「スッキリしない」を許可（除外から除く）
            if "スッキリしない" in comment_text:
                return True, "曇天時の適切な表現"
        
        return True, "天気条件OK"
    
    def _check_temperature_conditions(self, comment_text: str, 
                                    weather_data: WeatherForecast) -> Tuple[bool, str]:
        """温度条件に基づく検証"""
        temp = weather_data.temperature
        temp_thresholds = self.thresholds["temperature"]
        
        if temp >= temp_thresholds["hot"]:
            forbidden = self.temperature_forbidden_words["hot"]["forbidden"]
        elif temp < temp_thresholds["cold"]:
            forbidden = self.temperature_forbidden_words["cold"]["forbidden"]
        else:
            forbidden = self.temperature_forbidden_words["mild"]["forbidden"]
        
        for word in forbidden:
            if word in comment_text:
                return False, f"温度{temp}°Cで禁止ワード「{word}」を含む"
        
        return True, "温度条件OK"
    
    def _check_humidity_conditions(self, comment_text: str, 
                                  weather_data: WeatherForecast) -> Tuple[bool, str]:
        """湿度条件に基づく検証"""
        humidity = weather_data.humidity
        humidity_thresholds = self.thresholds["humidity"]
        
        # 高湿度時の乾燥関連コメントを除外
        if humidity >= humidity_thresholds["high"]:
            if "high" in self.humidity_forbidden_words:
                for word in self.humidity_forbidden_words["high"]["forbidden"]:
                    if word in comment_text:
                        return False, f"高湿度（{humidity}%）で乾燥関連表現「{word}」を含む"
        
        # 低湿度時の除湿関連コメントを除外
        if humidity < humidity_thresholds["low"]:
            if "low" in self.humidity_forbidden_words:
                for word in self.humidity_forbidden_words["low"]["forbidden"]:
                    if word in comment_text:
                        return False, f"低湿度（{humidity}%）で除湿関連表現「{word}」を含む"
        
        return True, "湿度条件OK"
    
    def _check_required_keywords(self, comment_text: str, comment_type: str,
                                weather_data: WeatherForecast) -> Tuple[bool, str]:
        """必須キーワードチェック（悪天候時）"""
        weather_desc = weather_data.weather_description.lower()
        
        # 大雨・豪雨時
        if any(heavy in weather_desc for heavy in ["大雨", "豪雨"]):
            if comment_type in self.required_keywords["heavy_rain"]:
                required = self.required_keywords["heavy_rain"][comment_type]
                if not any(keyword in comment_text for keyword in required):
                    return False, f"大雨時の必須キーワード不足（{', '.join(required)}のいずれか必要）"
        
        # 嵐・暴風時
        elif any(storm in weather_desc for storm in ["嵐", "暴風", "台風"]):
            if comment_type in self.required_keywords["storm"]:
                required = self.required_keywords["storm"][comment_type]
                if not any(keyword in comment_text for keyword in required):
                    return False, f"嵐時の必須キーワード不足（{', '.join(required)}のいずれか必要）"
        
        return True, "必須キーワードOK"
    
    def _check_rainy_weather_contradictions(self, comment_text: str, 
                                          weather_data: WeatherForecast) -> Tuple[bool, str]:
        """雨天時の矛盾表現を特別にチェック"""
        weather_desc = weather_data.weather_description.lower()
        
        # 雨天チェック
        if any(rain_word in weather_desc for rain_word in ["雨", "小雨", "中雨", "大雨", "豪雨"]):
            # 雨天時に矛盾する表現のリスト
            contradictory_phrases = [
                "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み", 
                "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下",
                "晴天", "好天", "快晴の", "青空が"
            ]
            
            for phrase in contradictory_phrases:
                if phrase in comment_text:
                    return False, f"雨天時の矛盾表現「{phrase}」を含む（天気：{weather_data.weather_description}）"
        
        return True, "矛盾表現チェックOK"
    
    def _check_regional_specifics(self, comment_text: str, location: str) -> Tuple[bool, str]:
        """地域特性に基づく検証"""
        # 地域別設定から該当地域を検索
        for region, config in self.regional_ng_expressions.items():
            if region in location:
                # 一般的な不適切表現チェック
                if "inappropriate" in config:
                    for word in config["inappropriate"]:
                        if word in comment_text:
                            return False, f"{region}で「{word}」は不適切"
                
                # 季節限定の不適切表現チェック（北海道の夏など）
                import datetime
                current_month = datetime.datetime.now().month
                if "inappropriate_summer" in config and current_month in [6, 7, 8]:
                    for word in config["inappropriate_summer"]:
                        if word in comment_text:
                            return False, f"{region}の夏季で「{word}」は不適切"
        
        return True, "地域特性OK"
    
    def filter_comments(self, comments: List[PastComment], 
                       weather_data: WeatherForecast) -> List[PastComment]:
        """
        コメントリストから不適切なものを除外
        
        Returns:
            適切なコメントのみのリスト
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
        天気に最も適したコメントを優先順位付けして取得
        
        Returns:
            優先順位付けされたコメントリスト（最大limit件）
        """
        # まず不適切なコメントを除外
        valid_comments = self.filter_comments(comments, weather_data)
        
        # スコアリング
        scored_comments = []
        for comment in valid_comments:
            score = self._calculate_appropriateness_score(comment, weather_data)
            scored_comments.append((score, comment))
        
        # スコア順にソート
        scored_comments.sort(key=lambda x: x[0], reverse=True)
        
        # 上位limit件を返す
        return [comment for _, comment in scored_comments[:limit]]
    
    def _calculate_appropriateness_score(self, comment: PastComment, 
                                       weather_data: WeatherForecast) -> float:
        """コメントの適切性スコアを計算"""
        score = 100.0  # 基本スコア
        comment_text = comment.comment_text
        weather_desc = weather_data.weather_description.lower()
        
        # 悪天候時のスコアリング
        if any(severe in weather_desc for severe in ["大雨", "豪雨", "嵐", "暴風"]):
            # 強い警戒表現にボーナス
            strong_warning_words = ["警戒", "危険", "激しい", "本格的", "荒れ", "大荒れ"]
            for word in strong_warning_words:
                if word in comment_text:
                    score += 20.0
            
            # 軽い表現にペナルティ
            mild_words = ["にわか雨", "変わりやすい", "スッキリしない", "どんより"]
            for word in mild_words:
                if word in comment_text:
                    score -= 30.0
        
        # 季節との一致度
        if 'season' in comment.raw_data:
            current_month = weather_data.datetime.month
            expected_season = self._get_season_from_month(current_month)
            if comment.raw_data['season'] == expected_season:
                score += 10.0
        
        # 使用回数によるスコア（人気度）
        if 'count' in comment.raw_data:
            count = comment.raw_data['count']
            score += min(count / 1000, 10.0)  # 最大10点のボーナス
        
        return score
    
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
"""天気条件バリデータ - 天気状態に基づくコメント検証"""

import logging
from typing import Tuple, Dict, List

from src.config.weather_constants import SUNNY_WEATHER_KEYWORDS
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.past_comment import PastComment, CommentType
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)


class WeatherValidator(BaseValidator):
    """天気条件に基づいてコメントの適切性を検証"""
    
    def __init__(self):
        super().__init__()
        self._initialize_weather_forbidden_words()
    
    def _initialize_weather_forbidden_words(self):
        """天気別禁止ワードの定義"""
        self.weather_forbidden_words = {
            # 雨天時（全レベル）
            "rain": {
                "weather_comment": [
                    "青空", "晴れ", "快晴", "日差し", "太陽", "陽射し", "眩しい",
                    "穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "のどか",
                    "お出かけ日和", "散歩日和", "ピクニック", "外出推奨",
                    "スッキリ", "気持ちいい", "清々しい",
                    # 雨天時に矛盾する表現を追加
                    "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み",
                    "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下"
                ],
                "advice": [
                    "日焼け止め", "帽子", "サングラス", "日傘", "紫外線",
                    "お出かけ", "外出", "散歩", "ピクニック", "日光浴",
                    "過ごしやすい", "快適", "心地良い", "爽やか",
                    # 雨天時の生活関連アドバイスを追加
                    "洗濯物を外に", "布団を干す", "外干しを", "窓を開けて", "ベランダ作業"
                ]
            },
            # 大雨・豪雨・嵐
            "heavy_rain": {
                "weather_comment": [
                    # 雨天時の禁止ワード全て
                    "青空", "晴れ", "快晴", "日差し", "太陽", "陽射し", "眩しい",
                    "穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "のどか",
                    "お出かけ日和", "散歩日和", "ピクニック", "外出推奨",
                    "スッキリ", "気持ちいい", "清々しい",
                    # 軽微な表現（大雨時は特に禁止）
                    "にわか雨", "ニワカ雨", "変わりやすい", "スッキリしない",
                    "蒸し暑い", "厳しい暑さ", "体感", "心地",
                    "雲の多い", "どんより", "じめじめ", "湿っぽい",
                    # 大雨時に特に不適切な表現を追加
                    "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み",
                    "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下"
                ],
                "advice": [
                    # 基本的な外出系
                    "日焼け止め", "帽子", "サングラス", "日傘", "紫外線",
                    "お出かけ", "外出", "散歩", "ピクニック", "日光浴",
                    "過ごしやすい", "快適", "心地良い", "爽やか",
                    # 軽い対策（大雨時は不適切）
                    "折り畳み傘", "軽い雨具", "短時間の外出"
                ]
            },
            # 晴天時
            "sunny": {
                "weather_comment": [
                    "雨", "じめじめ", "湿った", "どんより", "曇り", "雲が厚い",
                    "傘", "雨具", "濡れ", "湿気", "降水",
                    # 晴天時に不適切な空の状態表現を追加
                    "スッキリしない", "すっきりしない", "はっきりしない", "ぼんやり",
                    "もやもや", "重い空", "厚い雲", "灰色の空",
                    "曇りがち", "雲多め", "変わりやすい天気", "不安定",
                    # 安定した晴れ天気に不適切な表現を追加
                    "変わりやすい空", "変わりやすい", "気まぐれ", "移ろいやすい",
                    "一定しない", "変化しやすい", "変動", "不規則"
                ],
                "advice": [
                    "傘", "レインコート", "濡れ", "雨具", "長靴"
                ]
            },
            # 曇天時
            "cloudy": {
                "weather_comment": [
                    "青空", "快晴", "眩しい", "強い日差し", "ギラギラ",
                    "夏空", "秋空", "冬空", "春空", "澄んだ空", "抜けるような青空",
                    # 雨天時の生活関連表現を追加
                    "洗濯日和", "布団干し日和", "外干し", "窓を開けて", "ベランダで"
                ],
                "advice": [
                    "強い日差し対策", "紫外線対策必須"
                ]
            }
        }
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """天気条件に基づいてコメントを検証"""
        return self._check_weather_conditions(
            comment.comment_text,
            comment.comment_type.value,
            weather_data
        )
    
    def _check_weather_conditions(self, comment_text: str, comment_type: str, 
                                weather_data: WeatherForecast) -> Tuple[bool, str]:
        """天気条件に基づいてコメントの適切性をチェック"""
        # 天気タイプの判定
        weather_type = self._get_weather_type(weather_data)
        
        # 該当する天気タイプの禁止ワードを取得
        if weather_type in self.weather_forbidden_words:
            forbidden_words = self.weather_forbidden_words[weather_type].get(comment_type, [])
            
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"天気条件に不適切なワード: {word}"
        
        # 雨天時の追加チェック
        if weather_type in ["rain", "heavy_rain"]:
            result = self._check_rainy_weather_contradictions(
                comment_text, weather_data
            )
            if not result[0]:
                return result
        
        return True, ""
    
    def _get_weather_type(self, weather_data: WeatherForecast) -> str:
        """天気データから天気タイプを判定"""
        weather_desc = weather_data.weather_description.lower()
        
        # 大雨・豪雨判定
        if any(word in weather_desc for word in ["豪雨", "大雨", "暴風雨", "嵐", "台風"]):
            return "heavy_rain"
        
        # 雨判定
        if any(word in weather_desc for word in ["雨", "rain"]):
            return "rain"
        
        # 晴れ判定
        if any(word in weather_data.weather_description for word in SUNNY_WEATHER_KEYWORDS):
            return "sunny"
        
        # 曇り判定（うすぐもりも含む）
        if any(word in weather_desc for word in ["曇", "くもり", "cloud", "うすぐもり", "薄曇", "薄ぐもり"]):
            return "cloudy"
        
        return "unknown"
    
    def _check_rainy_weather_contradictions(self, comment_text: str, 
                                          weather_data: WeatherForecast) -> Tuple[bool, str]:
        """雨天時の矛盾をチェック"""
        # 降水量チェック
        if weather_data.precipitation > 5:  # 5mm/h以上の雨
            mild_expressions = ["小雨", "ぱらぱら", "ポツポツ", "少し"]
            for expr in mild_expressions:
                if expr in comment_text:
                    return False, f"降水量{weather_data.precipitation}mm/hに対して軽微な表現: {expr}"
        
        # 風速チェック（暴風雨）
        if weather_data.wind_speed > 15:  # 15m/s以上
            if "そよ風" in comment_text or "微風" in comment_text:
                return False, f"風速{weather_data.wind_speed}m/sに対して不適切な風の表現"
        
        return True, ""
    
    def _check_required_keywords(self, comment_text: str, comment_type: str,
                               weather_data: WeatherForecast) -> Tuple[bool, str]:
        """必須キーワードのチェック"""
        weather_desc = weather_data.weather_description.lower()
        
        # 雨天時は「雨」関連の言及が必要
        if any(word in weather_desc for word in ["雨", "rain"]):
            rain_keywords = ["雨", "降水", "傘", "濡れ", "レイン", "降り"]
            if not any(keyword in comment_text for keyword in rain_keywords):
                return False, "雨天時に雨への言及がない"
        
        # 台風時は警戒メッセージが必要
        if "台風" in weather_desc or "typhoon" in weather_desc.lower():
            warning_keywords = ["注意", "警戒", "気をつけ", "対策", "備え"]
            if not any(keyword in comment_text for keyword in warning_keywords):
                return False, "台風時に警戒メッセージがない"
        
        return True, ""
    
    def _is_stable_cloudy_weather(self, weather_data: WeatherForecast) -> bool:
        """安定した曇天かどうかを判定
        
        TODO: このメソッドは現在未使用ですが、将来的に安定した曇天時の
              特別な処理（例：変わりやすい天気の警告を出さない）に使用予定
        """
        # 現在の天気が曇りでない場合はFalse
        weather_desc = weather_data.weather_description.lower()
        if not any(cloudy in weather_desc for cloudy in ["曇", "くもり"]):
            return False
        
        # 設定ファイルから闾値を取得
        try:
            from src.config.config_loader import load_config
            config = load_config('weather_thresholds', validate=False)
            stability_config = config.get('weather_stability', {})
            precipitation_threshold = stability_config.get('cloudy_precipitation_threshold', 1.0)
            wind_threshold = stability_config.get('cloudy_wind_threshold', 5.0)
        except (FileNotFoundError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load stability thresholds, using defaults: {e}")
            # デフォルト値を使用
            precipitation_threshold = 1.0  # 1mm/h
            wind_threshold = 5.0  # 5m/s
        
        # 降水量が多い場合は不安定と判定
        if weather_data.precipitation > precipitation_threshold:
            return False
        
        # 風速が強い場合は不安定と判定
        if weather_data.wind_speed > wind_threshold:
            return False
        
        # 雷を含む場合は不安定と判定
        if "雷" in weather_desc or "thunder" in weather_desc.lower():
            return False
        
        # 霧を含む場合も変化の可能性があるため不安定と判定
        if "霧" in weather_desc or "fog" in weather_desc.lower():
            return False
        
        # 上記の条件をクリアした場合は安定した曇天と判定
        return True
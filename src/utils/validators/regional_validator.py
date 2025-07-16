"""地域特性バリデータ - 地域に基づくコメント検証"""

from __future__ import annotations
import logging

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)


class RegionalValidator(BaseValidator):
    """地域特性に基づいてコメントの適切性を検証"""
    
    def __init__(self):
        super().__init__()
        self._initialize_regional_keywords()
    
    def _initialize_regional_keywords(self):
        """地域別のキーワードを初期化"""
        # 沖縄県関連
        self.okinawa_keywords = [
            "沖縄", "那覇", "石垣", "宮古", "名護", "うるま", 
            "沖縄市", "浦添", "糸満", "豊見城", "南城"
        ]
        
        # 北海道関連
        self.hokkaido_keywords = [
            "北海道", "札幌", "函館", "旭川", "釧路", "帯広", 
            "北見", "小樽", "室蘭", "苫小牧"
        ]
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> tuple[bool, str]:
        """地域特性に基づいてコメントを検証"""
        location = comment.location
        comment_text = comment.comment_text
        
        # 地域特性チェック
        regional_check = self._check_regional_specifics(comment_text, location)
        if not regional_check[0]:
            return regional_check
        
        # 湿度条件チェック（地域により湿度の感じ方が異なる場合があるため）
        humidity_check = self._check_humidity_conditions(comment_text, weather_data)
        if not humidity_check[0]:
            return humidity_check
        
        return True, "地域検証OK"
    
    def _check_regional_specifics(self, comment_text: str, location: str) -> tuple[bool, str]:
        """地域特性に基づく検証（改善版）"""
        # 地域判定の改善：都道府県と市町村の適切な判定
        location_lower = location.lower()
        
        # 沖縄県関連の判定（県名・市町村名を包括）
        is_okinawa = any(keyword in location_lower for keyword in self.okinawa_keywords)
        
        if is_okinawa:
            # 雪関連のコメントを除外
            snow_words = [
                "雪", "雪景色", "粉雪", "新雪", "雪かき", "雪道", 
                "雪が降る", "雪化粧", "雪だるま"
            ]
            for word in snow_words:
                if word in comment_text:
                    return False, f"沖縄地域で雪関連表現「{word}」は不適切"
            
            # 低温警告の閾値を緩和（沖縄は寒くならない）
            strong_cold_words = [
                "極寒", "凍える", "凍結", "防寒対策必須", 
                "暖房必須", "厚着必要"
            ]
            for word in strong_cold_words:
                if word in comment_text:
                    return False, f"沖縄地域で強い寒さ表現「{word}」は不適切"
        
        # 北海道関連の判定（道名・主要都市名を包括）
        is_hokkaido = any(keyword in location_lower for keyword in self.hokkaido_keywords)
        
        if is_hokkaido:
            # 高温警告の閾値を上げ（北海道は暑くなりにくい）
            strong_heat_words = [
                "酷暑", "猛暑", "危険な暑さ", "熱帯夜", "猛烈な暑さ"
            ]
            for word in strong_heat_words:
                if word in comment_text:
                    return False, f"北海道地域で強い暑さ表現「{word}」は不適切"
        
        # その他の地域特性チェック（今後拡張可能）
        # 山間部・海岸部などの特性も将来的に追加可能
        
        return True, "地域特性OK"
    
    def _check_humidity_conditions(self, comment_text: str, 
                                  weather_data: WeatherForecast) -> tuple[bool, str]:
        """湿度条件に基づく検証"""
        humidity = weather_data.humidity
        
        # 高湿度時（80%以上）の乾燥関連コメントを除外
        if humidity >= 80:
            dry_words = [
                "乾燥注意", "乾燥対策", "乾燥しやすい", "乾燥した空気", 
                "からっと", "さっぱり", "湿度低下"
            ]
            for word in dry_words:
                if word in comment_text:
                    return False, f"高湿度（{humidity}%）で乾燥関連表現「{word}」を含む"
        
        # 低湿度時（30%未満）の除湿関連コメントを除外
        if humidity < 30:
            humid_words = ["除湿対策", "除湿", "ジメジメ", "湿気対策", "湿っぽい"]
            for word in humid_words:
                if word in comment_text:
                    return False, f"低湿度（{humidity}%）で除湿関連表現「{word}」を含む"
        
        return True, "湿度条件OK"
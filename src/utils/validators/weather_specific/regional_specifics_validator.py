"""地域特性バリデーター - 地域特性に基づいてコメントの適切性を検証"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class RegionalSpecificsValidator:
    """地域特性に基づいてコメントの適切性を検証"""
    
    def __init__(self):
        # 地域キーワードの定義
        self.okinawa_keywords = [
            "沖縄", "那覇", "石垣", "宮古", "名護", "うるま", 
            "沖縄市", "浦添", "糸満", "豊見城", "南城"
        ]
        
        self.hokkaido_keywords = [
            "北海道", "札幌", "函館", "旭川", "釧路", "帯広", "北見", 
            "小樽", "室蘭", "苫小牧", "稚内", "網走", "留萌", "岩見沢"
        ]
        
        # 地域別の禁止ワード
        self.regional_forbidden_words = {
            "okinawa": {
                "snow": ["雪", "雪景色", "粉雪", "新雪", "雪かき", "雪道", 
                        "雪が降る", "雪化粧", "雪だるま", "吹雪", "積雪"],
                "extreme_cold": ["極寒", "凍える", "凍結", "防寒対策必須", 
                               "暖房必須", "厚着必要", "氷点下", "路面凍結"]
            },
            "hokkaido": {
                "extreme_heat": ["酷暑", "猛暑", "危険な暑さ", "熱帯夜", 
                               "猛烈な暑さ", "灼熱", "うだるような暑さ"]
            }
        }
    
    def check_regional_specifics(
        self, 
        comment_text: str, 
        location: str
    ) -> tuple[bool, str]:
        """地域特性に基づく検証（改善版）"""
        # 地域判定の改善：都道府県と市町村の適切な判定
        location_lower = location.lower()
        
        # 沖縄県関連の判定
        is_okinawa = any(keyword in location_lower for keyword in self.okinawa_keywords)
        
        if is_okinawa:
            # 雪関連のコメントを除外
            for word in self.regional_forbidden_words["okinawa"]["snow"]:
                if word in comment_text:
                    return False, f"沖縄地域で雪関連表現「{word}」は不適切"
            
            # 低温警告の閾値を緩和（沖縄は寒くならない）
            for word in self.regional_forbidden_words["okinawa"]["extreme_cold"]:
                if word in comment_text:
                    return False, f"沖縄地域で強い寒さ表現「{word}」は不適切"
        
        # 北海道関連の判定
        is_hokkaido = any(keyword in location_lower for keyword in self.hokkaido_keywords)
        
        if is_hokkaido:
            # 高温警告の閾値を上げ（北海道は暑くなりにくい）
            for word in self.regional_forbidden_words["hokkaido"]["extreme_heat"]:
                if word in comment_text:
                    return False, f"北海道地域で強い暑さ表現「{word}」は不適切"
        
        # その他の地域特性チェック（今後拡張可能）
        # 山間部・海岸部などの特性も将来的に追加可能
        
        return True, "地域特性OK"
    
    def get_regional_temperature_thresholds(self, location: str) -> dict:
        """地域に応じた温度閾値を取得"""
        location_lower = location.lower()
        
        # デフォルト値
        thresholds = {
            "hot_threshold": 30.0,
            "cold_threshold": 10.0,
            "extreme_hot_threshold": 35.0,
            "extreme_cold_threshold": 0.0
        }
        
        # 沖縄の場合
        if any(keyword in location_lower for keyword in self.okinawa_keywords):
            thresholds["cold_threshold"] = 15.0  # 寒さの閾値を上げる
            thresholds["extreme_cold_threshold"] = 10.0
        
        # 北海道の場合
        elif any(keyword in location_lower for keyword in self.hokkaido_keywords):
            thresholds["hot_threshold"] = 25.0  # 暑さの閾値を下げる
            thresholds["extreme_hot_threshold"] = 30.0
        
        return thresholds
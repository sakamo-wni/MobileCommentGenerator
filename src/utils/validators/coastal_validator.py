"""海岸地域バリデータ - 海岸/内陸に基づくコメント検証"""

import logging
from typing import Tuple, Set, Optional

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from src.data.location_manager import LocationManager
from src.utils.geography import CoastalDetector
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)


class CoastalValidator(BaseValidator):
    """海岸地域に基づいてコメントの適切性を検証"""
    
    # 海岸地域のリスト（主要な海岸都市）
    COASTAL_LOCATIONS = {
        # 北海道
        "稚内", "釧路", "根室", "函館", "小樽", "留萌", "網走", "紋別",
        # 東北
        "青森", "八戸", "宮古", "大船渡", "石巻", "相馬", "いわき",
        # 関東
        "銚子", "勝浦", "館山", "横浜", "平塚", "小田原", "三浦",
        # 中部
        "新潟", "富山", "金沢", "福井", "静岡", "浜松", "伊東", "下田",
        # 近畿
        "舞鶴", "神戸", "姫路", "和歌山", "串本", "潮岬",
        # 中国
        "鳥取", "境港", "松江", "浜田", "岡山", "広島", "下関",
        # 四国
        "高松", "徳島", "高知", "宇和島", "松山",
        # 九州・沖縄
        "福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島", "那覇", "石垣", "宮古島"
    }
    
    # 海岸関連のキーワード
    COASTAL_KEYWORDS = {
        "海", "波", "沿岸", "海岸", "海上", "港", "漁",
        "サーフィン", "海水浴", "磯", "浜", "岸", "湾"
    }
    
    # 高波・海の危険に関するキーワード
    HIGH_WAVE_KEYWORDS = {
        "高波", "波浪", "うねり", "しけ", "荒れ", "大波"
    }
    
    def __init__(self):
        super().__init__()
        self.location_manager = LocationManager()
        logger.info("海岸地域バリデータを初期化しました（緯度経度ベース）")
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """海岸地域に基づいてコメントを検証"""
        location = weather_data.location
        comment_text = comment.comment_text
        advice_text = comment.raw_data.get("advice", "")
        
        # 内陸地域で海岸関連コメントをチェック
        if not self._is_coastal_location(location):
            # 高波や海の危険に関する表現をチェック
            for keyword in self.HIGH_WAVE_KEYWORDS:
                if keyword in comment_text or keyword in advice_text:
                    logger.info(f"内陸地域で海岸関連表現を除外: '{comment_text}' - 地域: {location}")
                    return False, f"内陸地域（{location}）で海岸関連表現「{keyword}」は不適切"
            
            # その他の海岸関連表現をチェック
            coastal_count = sum(1 for kw in self.COASTAL_KEYWORDS if kw in comment_text or kw in advice_text)
            if coastal_count >= 2:  # 2つ以上の海岸関連キーワードがある場合
                logger.info(f"内陸地域で複数の海岸関連表現を除外: '{comment_text}' - 地域: {location}")
                return False, f"内陸地域（{location}）で海岸関連表現が多すぎます"
        
        return True, "海岸地域検証OK"
    
    def _is_coastal_location(self, location_name: str) -> bool:
        """地域が海岸地域かどうかを判定（緯度経度ベース）"""
        try:
            # LocationManagerから地点情報を取得
            location = self.location_manager.get_location(location_name)
            
            if location and location.latitude and location.longitude:
                # 緯度経度から海岸地域かどうかを判定
                is_coastal = CoastalDetector.is_coastal(
                    location.latitude, 
                    location.longitude,
                    threshold_km=15.0  # 15km以内を海岸地域とする
                )
                
                logger.debug(
                    f"{location_name} ({location.latitude}, {location.longitude}) - "
                    f"海岸地域: {is_coastal}"
                )
                
                return is_coastal
            else:
                logger.debug(f"{location_name}の緯度経度情報が取得できません")
                # フォールバック: 従来の名前ベースの判定
                return self._is_coastal_by_name(location_name)
                
        except Exception as e:
            logger.error(f"海岸地域判定エラー: {e}")
            # エラー時は従来の方法にフォールバック
            return self._is_coastal_by_name(location_name)
    
    def _is_coastal_by_name(self, location: str) -> bool:
        """地域名から海岸地域かどうかを判定（フォールバック用）"""
        # 完全一致チェック
        if location in self.COASTAL_LOCATIONS:
            return True
        
        # 部分一致チェック（市区町村を含む場合）
        for coastal_loc in self.COASTAL_LOCATIONS:
            if coastal_loc in location or location in coastal_loc:
                return True
        
        # 海岸関連の地名を含むかチェック
        coastal_indicators = ["港", "浜", "海", "岬", "崎", "浦", "湾", "磯"]
        return any(indicator in location for indicator in coastal_indicators)
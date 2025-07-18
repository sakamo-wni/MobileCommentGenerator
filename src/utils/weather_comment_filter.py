"""
天気コメントフィルタリング統合モジュール

天気条件とコメントの整合性をチェックする統合フィルタ
"""

import logging
from typing import List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WeatherCommentFilter:
    """天気コメントの統合フィルタクラス"""
    
    # 天気別の禁止キーワード
    WEATHER_INCOMPATIBLE_KEYWORDS = {
        "sunny": {  # 晴れ
            "forbidden": ["雨", "傘", "濡れ", "しっとり", "じめじめ", "ずぶ濡れ", "土砂降り", "にわか雨", "雷雨", "降りやすい"],
            "weather_patterns": ["晴", "快晴"]
        },
        "cloudy": {  # 曇り
            "forbidden": [
                # 日差し関連
                "強い日差し", "眩しい", "太陽がギラギラ", "日光が強", "日差しジリジリ", 
                "照りつける", "燦々", "日差しの活用", "太陽の恵み", "日光浴",
                # 雨関連（降水なしの場合）
                "雨", "傘", "濡れ", "しっとり", "じめじめ", "ずぶ濡れ", "土砂降り", 
                "にわか雨", "雷雨", "降りやすい", "雨具", "レインコート"
            ],
            "weather_patterns": ["曇", "くもり", "うすぐもり", "薄曇"]
        },
        "rainy": {  # 雨
            "forbidden": ["快晴", "青空", "強い日差し", "眩しい", "太陽がギラギラ", "日差しの活用"],
            "weather_patterns": ["雨", "雷雨", "にわか雨"]
        },
        "snowy": {  # 雪
            "forbidden": ["暑", "熱中症", "日差し", "汗ばむ", "蒸し暑い"],
            "weather_patterns": ["雪", "吹雪"]
        }
    }
    
    # 季節別の禁止表現
    SEASONAL_FORBIDDEN = {
        1: ["残暑", "梅雨", "台風", "海水浴", "プール"],  # 1月
        2: ["残暑", "梅雨", "台風", "海水浴", "プール"],  # 2月
        3: ["残暑", "真夏", "猛暑", "酷暑", "真冬", "初雪"],  # 3月
        4: ["残暑", "真夏", "猛暑", "酷暑", "真冬", "初雪"],  # 4月
        5: ["残暑", "真夏", "猛暑", "酷暑", "真冬", "初雪"],  # 5月
        6: ["残暑", "真冬", "初雪", "年末", "師走"],  # 6月
        7: ["残暑", "真冬", "初雪", "年末", "師走"],  # 7月
        8: ["残暑", "真冬", "初雪", "年末", "師走"],  # 8月
        9: ["真冬", "初雪", "年末", "師走"],  # 9月（残暑OK）
        10: ["真夏", "猛暑", "梅雨", "真冬", "年末"],  # 10月
        11: ["真夏", "猛暑", "梅雨"],  # 11月
        12: ["梅雨", "台風", "残暑"]  # 12月
    }
    
    # 安定天気時の禁止表現
    UNSTABLE_WEATHER_KEYWORDS = [
        "変わりやすい", "天気急変", "不安定", "変化", "急変",
        "めまぐるしく", "一時的", "急な雨", "にわか雨",
        "突然の雨", "ゲリラ豪雨", "天気の急変"
    ]
    
    def __init__(self):
        """フィルタの初期化"""
        pass
    
    def get_weather_type(self, weather_description: str, precipitation: float = 0) -> str:
        """
        天気説明から天気タイプを判定
        
        Args:
            weather_description: 天気の説明
            precipitation: 降水量（Noneの場合も0として扱う）
            
        Returns:
            天気タイプ (sunny, cloudy, rainy, snowy)
        """
        # 降水量のNoneチェック
        if precipitation is None:
            precipitation = 0
            
        weather_desc_lower = weather_description.lower()
        
        # 雨・雪の判定（降水量も考慮）
        if precipitation > 0:
            if any(snow in weather_desc_lower for snow in ["雪", "snow"]):
                return "snowy"
            return "rainy"
        
        # 天気説明から判定
        for weather_type, config in self.WEATHER_INCOMPATIBLE_KEYWORDS.items():
            for pattern in config["weather_patterns"]:
                if pattern in weather_description:
                    return weather_type
        
        return "cloudy"  # デフォルト
    
    def is_comment_appropriate(
        self, 
        comment_text: str, 
        weather_description: str,
        precipitation: float = 0,
        temperature: Optional[float] = None,
        month: Optional[int] = None,
        is_stable_weather: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        コメントが天気条件に適切かチェック
        
        Args:
            comment_text: チェックするコメント
            weather_description: 天気の説明
            precipitation: 降水量
            temperature: 気温
            month: 月
            is_stable_weather: 安定した天気かどうか
            
        Returns:
            (適切かどうか, 不適切な理由)
        """
        # 天気タイプの判定
        weather_type = self.get_weather_type(weather_description, precipitation)
        
        # 天気別チェック
        if weather_type in self.WEATHER_INCOMPATIBLE_KEYWORDS:
            forbidden = self.WEATHER_INCOMPATIBLE_KEYWORDS[weather_type]["forbidden"]
            
            # 曇りで降水なしの場合のみ雨関連を除外
            if weather_type == "cloudy" and precipitation > 0:
                # 降水がある場合は雨関連表現を許可
                forbidden = [kw for kw in forbidden if kw not in ["雨", "傘", "濡れ", "しっとり", "じめじめ", "ずぶ濡れ", "土砂降り", "にわか雨", "雷雨", "降りやすい", "雨具", "レインコート"]]
            
            for keyword in forbidden:
                if keyword in comment_text:
                    return False, f"{weather_description}時に「{keyword}」は不適切"
        
        # 安定天気チェック
        if is_stable_weather:
            for keyword in self.UNSTABLE_WEATHER_KEYWORDS:
                if keyword in comment_text:
                    return False, f"安定した天気で「{keyword}」は不適切"
        
        # 季節チェック
        if month and month in self.SEASONAL_FORBIDDEN:
            for keyword in self.SEASONAL_FORBIDDEN[month]:
                if keyword in comment_text:
                    return False, f"{month}月に「{keyword}」は不適切"
        
        return True, None
    
    def filter_comments(
        self,
        comments: List,
        weather_description: str,
        precipitation: float = 0,
        temperature: Optional[float] = None,
        month: Optional[int] = None,
        is_stable_weather: bool = False
    ) -> List:
        """
        コメントリストをフィルタリング
        
        Args:
            comments: コメントオブジェクトのリスト
            weather_description: 天気の説明
            precipitation: 降水量
            temperature: 気温
            month: 月
            is_stable_weather: 安定した天気かどうか
            
        Returns:
            フィルタリング後のコメントリスト
        """
        # 入力パラメータの検証
        if not comments:
            return comments
            
        if not weather_description:
            weather_description = ""
            
        filtered = []
        
        for comment in comments:
            comment_text = comment.comment_text if hasattr(comment, 'comment_text') else str(comment)
            if not comment_text:
                continue
            
            is_appropriate, reason = self.is_comment_appropriate(
                comment_text,
                weather_description,
                precipitation,
                temperature,
                month,
                is_stable_weather
            )
            
            if is_appropriate:
                filtered.append(comment)
            else:
                logger.info(f"コメントを除外: {reason} - '{comment_text}'")
        
        return filtered
"""悪天候時のコメント選択設定"""

from dataclasses import dataclass, field
from typing import Dict, List, Set
from src.data.weather_data import WeatherCondition


@dataclass
class SevereWeatherConfig:
    """悪天候時の特別なコメント選択設定"""
    
    # 悪天候として特別扱いする条件
    severe_weather_conditions: Set[WeatherCondition] = field(default_factory=lambda: {
        WeatherCondition.SEVERE_STORM,  # 大雨・嵐
        WeatherCondition.STORM,         # 嵐
        WeatherCondition.THUNDER,       # 雷
        WeatherCondition.HEAVY_RAIN,    # 大雨
        WeatherCondition.RAIN,          # 雨
        WeatherCondition.FOG,           # 霧
        WeatherCondition.HEAVY_SNOW,    # 大雪
        WeatherCondition.SNOW,          # 雪
    })
    
    # 悪天候時に推奨される天気コメント
    severe_weather_comments: Dict[str, List[str]] = field(default_factory=lambda: {
        "大雨・嵐": [
            "大荒れの空",
            "激しい雨に警戒",
            "外出は控えめに",
            "安全第一の一日",
            "荒天に要注意"
        ],
        "雨": [
            "雨雲が広がる空",
            "本格的な雨に注意",
            "濡れ対策が必要",
            "雨が続く空模様",
            "雨脚が強まる可能性"
        ],
        "雷": [
            "雷に注意",
            "不安定な空模様",
            "急な雷雨に警戒",
            "空の様子に注意",
            "雷鳴轟く空"
        ],
        "霧": [
            "視界不良に注意",
            "霧に包まれる朝",
            "見通し悪い空",
            "慎重な行動を",
            "霧が立ち込める"
        ],
        "暴風": [
            "強風に警戒",
            "風が強い一日",
            "飛来物に注意",
            "外出時は要注意",
            "荒れ模様の空"
        ]
    })
    
    # 悪天候時に推奨されるアドバイスコメント
    severe_weather_advice: Dict[str, List[str]] = field(default_factory=lambda: {
        "大雨・嵐": [
            "室内で安全に",
            "無理な外出は避けて",
            "最新情報をチェック",
            "早めの帰宅を",
            "安全確保を優先"
        ],
        "雨": [
            "傘がお守り",
            "足元に注意を",
            "濡れ対策を忘れずに",
            "室内で過ごすのも",
            "雨具の準備を"
        ],
        "雷": [
            "建物内で待機を",
            "高い場所は避けて",
            "電気製品に注意",
            "屋内で安全に",
            "金属類から離れて"
        ],
        "霧": [
            "車の運転は慎重に",
            "ゆっくり移動を",
            "時間に余裕を持って",
            "足元に注意して",
            "明るい服装で"
        ],
        "暴風": [
            "飛来物に注意",
            "窓から離れて",
            "外出は最小限に",
            "しっかり固定を",
            "安全な場所で"
        ]
    })
    
    # 悪天候時の除外キーワード（これらを含むコメントは選ばない）
    exclude_keywords_severe: List[str] = field(default_factory=lambda: [
        "穏やか", "過ごしやすい", "快適", "爽やか", "心地良い",
        "青空", "晴れ", "快晴", "日差し", "太陽",
        "散歩", "ピクニック", "お出かけ", "外出日和",
        "洗濯日和", "布団干し", "外遊び",
        "ニワカ雨が心配", "スッキリしない", "蒸し暑い"
    ])
    
    # 天気条件の日本語マッピング
    weather_condition_japanese: Dict[WeatherCondition, str] = field(default_factory=lambda: {
        WeatherCondition.SEVERE_STORM: "大雨・嵐",
        WeatherCondition.STORM: "嵐",
        WeatherCondition.THUNDER: "雷",
        WeatherCondition.HEAVY_RAIN: "大雨",
        WeatherCondition.RAIN: "雨",
        WeatherCondition.FOG: "霧",
        WeatherCondition.HEAVY_SNOW: "大雪",
        WeatherCondition.SNOW: "雪",
    })
    
    def is_severe_weather(self, condition: WeatherCondition) -> bool:
        """指定された天気条件が悪天候かどうか判定"""
        return condition in self.severe_weather_conditions
    
    def get_recommended_comments(self, condition: WeatherCondition) -> Dict[str, List[str]]:
        """指定された天気条件に推奨されるコメントを取得"""
        japanese_name = self.weather_condition_japanese.get(condition, "")
        
        return {
            "weather": self.severe_weather_comments.get(japanese_name, []),
            "advice": self.severe_weather_advice.get(japanese_name, [])
        }


# シングルトンインスタンス
_severe_config = None


def get_severe_weather_config() -> SevereWeatherConfig:
    """悪天候設定を取得"""
    global _severe_config
    if _severe_config is None:
        _severe_config = SevereWeatherConfig()
    return _severe_config
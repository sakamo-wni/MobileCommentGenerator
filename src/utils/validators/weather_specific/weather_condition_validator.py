"""天気条件バリデーター - 天気条件に基づいてコメントの適切性を検証"""

from __future__ import annotations
import logging
import yaml
from pathlib import Path
from src.config.config import get_weather_constants

# 定数を取得
SUNNY_WEATHER_KEYWORDS = get_weather_constants().SUNNY_WEATHER_KEYWORDS
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment

logger = logging.getLogger(__name__)


class WeatherConditionValidator:
    """天気条件に基づいてコメントの適切性を検証"""
    
    def __init__(self, config_path: str | None = None):
        """
        初期化
        
        Args:
            config_path: 禁止ワード設定ファイルのパス。Noneの場合はデフォルトパスを使用
        """
        self.weather_forbidden_words = self._load_forbidden_words(config_path)
    
    def check_weather_conditions(
        self, 
        comment_text: str, 
        comment_type: str,
        weather_description: str
    ) -> tuple[bool, str]:
        """天気条件に基づく検証"""
        weather_desc_lower = weather_description.lower()
        
        # 晴天パターン
        if any(sunny_word in weather_desc_lower for sunny_word in SUNNY_WEATHER_KEYWORDS):
            forbidden_words = self.weather_forbidden_words.get("sunny", {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"晴天時に「{word}」は不適切"
        
        # 雨天パターン（豪雨・大雨を優先的にチェック）
        elif any(word in weather_desc_lower for word in ["豪雨", "大雨", "暴風雨", "激しい雨", "非常に激しい雨", "猛烈な雨"]):
            forbidden_words = self.weather_forbidden_words.get("heavy_rain", {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"大雨時に「{word}」は不適切"
        
        # 通常の雨
        elif "雨" in weather_desc_lower or "rain" in weather_desc_lower:
            forbidden_words = self.weather_forbidden_words.get("rain", {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"雨天時に「{word}」は不適切"
        
        # 曇天パターン
        elif any(word in weather_desc_lower for word in ["曇", "くもり", "曇り", "雲", "cloudy"]):
            forbidden_words = self.weather_forbidden_words.get("cloudy", {}).get(comment_type, [])
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"曇天時に「{word}」は不適切"
        
        return True, "天気条件チェックOK"
    
    def check_rainy_weather_contradictions(
        self,
        comment_text: str,
        weather_description: str
    ) -> tuple[bool, str]:
        """雨天時の矛盾をチェックする（全タイプ共通）"""
        weather_desc_lower = weather_description.lower()
        
        # 雨天の場合のみチェック
        if not ("雨" in weather_desc_lower or "rain" in weather_desc_lower):
            return True, "雨天チェック対象外"
        
        # 雨天時に矛盾する活動
        contradictory_activities = [
            "洗濯物を外に", "布団を干", "外干し", "ベランダで干",
            "窓を開けて換気", "窓を全開", "外で乾かす"
        ]
        
        for activity in contradictory_activities:
            if activity in comment_text:
                return False, f"雨天時に「{activity}」は矛盾"
        
        return True, "雨天矛盾チェックOK"
    
    def is_stable_cloudy_weather(self, weather_data: WeatherForecast) -> bool:
        """安定した曇り天気かどうかを判定"""
        weather_desc = weather_data.weather_description.lower()
        
        # 安定した曇り天気のパターン
        stable_cloudy_patterns = [
            "曇り", "くもり", "曇", "cloudy", "overcast",
            "雲が多い", "雲が広がる", "どんより"
        ]
        
        # 不安定な要素があれば除外
        unstable_patterns = [
            "一時", "のち", "時々", "変わりやすい", "不安定",
            "にわか雨", "雷", "突風", "あられ", "ひょう"
        ]
        
        # 安定した曇りかチェック
        is_cloudy = any(pattern in weather_desc for pattern in stable_cloudy_patterns)
        is_unstable = any(pattern in weather_desc for pattern in unstable_patterns)
        
        return is_cloudy and not is_unstable
    
    def _load_forbidden_words(self, config_path: str | None = None) -> dict[str, dict[str, list[str]]]:
        """禁止ワード設定をYAMLファイルから読み込む"""
        if config_path is None:
            # デフォルトパスを構築
            current_file = Path(__file__).resolve()
            config_path = current_file.parent.parent.parent.parent.parent / "config" / "weather_forbidden_words.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                # YAMLファイルの先頭にあるドキュメントストリングをスキップ
                content = f.read()
                # 三重引用符で囲まれた部分を削除
                if content.startswith('"""'):
                    end_index = content.find('"""', 3)
                    if end_index != -1:
                        content = content[end_index + 3:].strip()
                
                forbidden_words = yaml.safe_load(content)
                logger.info(f"禁止ワード設定を読み込みました: {config_path}")
                return forbidden_words
                
        except FileNotFoundError:
            logger.warning(f"設定ファイルが見つかりません: {config_path}. デフォルト設定を使用します。")
            return self._get_default_forbidden_words()
        except Exception as e:
            logger.error(f"設定ファイルの読み込みエラー: {e}. デフォルト設定を使用します。")
            return self._get_default_forbidden_words()
    
    def _get_default_forbidden_words(self) -> dict[str, dict[str, list[str]]]:
        """デフォルトの禁止ワード設定を返す"""
        return {
            # 雨天時（全レベル）
            "rain": {
                "weather_comment": [
                    "青空", "晴れ", "快晴", "日差し", "太陽", "陽射し", "眩しい",
                    "穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "のどか",
                    "お出かけ日和", "散歩日和", "ピクニック", "外出推奨",
                    "スッキリ", "気持ちいい", "清々しい",
                    "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み",
                    "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下"
                ],
                "advice": [
                    "日焼け止め", "帽子", "サングラス", "日傘", "紫外線",
                    "お出かけ", "外出", "散歩", "ピクニック", "日光浴",
                    "過ごしやすい", "快適", "心地良い", "爽やか",
                    "洗濯物を外に", "布団を干す", "外干しを", "窓を開けて", "ベランダ作業"
                ]
            },
            # 大雨・豪雨・嵐
            "heavy_rain": {
                "weather_comment": [
                    "青空", "晴れ", "快晴", "日差し", "太陽", "陽射し", "眩しい",
                    "穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "のどか",
                    "お出かけ日和", "散歩日和", "ピクニック", "外出推奨",
                    "スッキリ", "気持ちいい", "清々しい",
                    "にわか雨", "ニワカ雨", "変わりやすい", "スッキリしない",
                    "蒸し暑い", "厳しい暑さ", "体感", "心地",
                    "雲の多い", "どんより", "じめじめ", "湿っぽい",
                    "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み",
                    "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下"
                ],
                "advice": [
                    "日焼け止め", "帽子", "サングラス", "日傘", "紫外線",
                    "お出かけ", "外出", "散歩", "ピクニック", "日光浴",
                    "過ごしやすい", "快適", "心地良い", "爽やか",
                    "折り畳み傘", "軽い雨具", "短時間の外出"
                ]
            },
            # 晴天時
            "sunny": {
                "weather_comment": [
                    "雨", "じめじめ", "湿った", "どんより", "曇り", "雲が厚い",
                    "傘", "雨具", "濡れ", "湿気", "降水",
                    "スッキリしない", "すっきりしない", "はっきりしない", "ぼんやり",
                    "もやもや", "重い空", "厚い雲", "灰色の空",
                    "曇りがち", "雲多め", "変わりやすい天気", "不安定",
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
                    "洗濯日和", "布団干し日和", "外干し", "窓を開けて", "ベランダで"
                ],
                "advice": [
                    "強い日差し対策", "紫外線対策必須"
                ]
            }
        }
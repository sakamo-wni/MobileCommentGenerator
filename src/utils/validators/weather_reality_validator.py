"""天気と現実の矛盾を検証するバリデータ"""

from __future__ import annotations
import logging
import yaml
from pathlib import Path
from src.data.weather_data import WeatherForecast
from src.config.config import get_weather_constants

# 定数を取得
SUNNY_WEATHER_KEYWORDS = get_weather_constants().SUNNY_WEATHER_KEYWORDS

logger = logging.getLogger(__name__)


class WeatherRealityValidator:
    """天気コメントと実際の天気データの矛盾を検証"""
    
    def __init__(self):
        """設定ファイルから表現リストを読み込み"""
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "validator_words.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.weather_reality_config = config.get('weather_reality', {})
        except Exception as e:
            logger.warning(f"設定ファイル読み込みエラー: {e}. デフォルト値を使用します。")
            self.weather_reality_config = self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """デフォルトの設定を返す"""
        return {
            'rain_expressions': ["雨", "降水", "傘", "濡れ", "しっとり", "じめじめ"],
            'sunny_expressions': ["快晴", "日差し", "陽射し", "太陽", "青空", "晴天"],
            'cold_expressions': ["寒い", "冷え", "ひんやり", "凍える", "震える"],
            'hot_expressions': ["暑い", "猛暑", "酷暑", "うだる", "汗ばむ"],
            'high_temp_threshold': 30,
            'low_temp_threshold': 10
        }
    
    def check_weather_reality_contradiction(
        self, 
        weather_comment: str, 
        weather_data: WeatherForecast
    ) -> tuple[bool, str]:
        """
        天気コメントが実際の天気と矛盾していないかチェック
        
        Args:
            weather_comment: 天気コメント
            weather_data: 実際の天気データ
            
        Returns:
            (is_consistent, reason): 一貫性チェック結果とその理由
        """
        # 晴れているのに雨の表現
        if any(keyword in weather_data.weather_description for keyword in SUNNY_WEATHER_KEYWORDS):
            rain_expressions = self.weather_reality_config.get('rain_expressions', [])
            for expr in rain_expressions:
                if expr in weather_comment:
                    return False, f"晴天時に不適切な表現: {expr}"
        
        # 雨なのに晴れの表現
        if "雨" in weather_data.weather_description:
            sunny_expressions = self.weather_reality_config.get('sunny_expressions', [])
            for expr in sunny_expressions:
                if expr in weather_comment:
                    return False, f"雨天時に不適切な表現: {expr}"
        
        # 高温時に寒さの表現
        high_temp_threshold = self.weather_reality_config.get('high_temp_threshold', 30)
        if weather_data.temperature > high_temp_threshold:
            cold_expressions = self.weather_reality_config.get('cold_expressions', [])
            for expr in cold_expressions:
                if expr in weather_comment:
                    return False, f"高温時({weather_data.temperature}°C)に不適切な表現: {expr}"
        
        # 低温時に暑さの表現
        low_temp_threshold = self.weather_reality_config.get('low_temp_threshold', 10)
        if weather_data.temperature < low_temp_threshold:
            hot_expressions = self.weather_reality_config.get('hot_expressions', [])
            for expr in hot_expressions:
                if expr in weather_comment:
                    return False, f"低温時({weather_data.temperature}°C)に不適切な表現: {expr}"
        
        return True, ""
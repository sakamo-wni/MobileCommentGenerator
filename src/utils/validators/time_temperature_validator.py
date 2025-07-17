"""時間帯と温度の矛盾を検証するバリデータ"""

from __future__ import annotations
import logging
from functools import lru_cache
from datetime import datetime
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState
from src.config.config import get_validator_words

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_time_temperature_config():
    """時間温度設定を取得（キャッシュ付き）"""
    config = get_validator_words()
    return config.get('time_temperature', _get_default_config())


def _get_default_config() -> dict:
    """デフォルトの時間帯設定を返す"""
    return {
        'time_periods': {
            'morning': {'start': 5, 'end': 9},
            'day': {'start': 10, 'end': 15},
            'evening': {'start': 16, 'end': 18},
            'night': {'start': 19, 'end': 4}
        },
        'inappropriate_expressions': {
            'morning': ["夕焼け", "夜風", "日没", "夕暮れ", "星空"],
            'day': ["星空", "月明かり", "夜露", "朝露", "朝もや"],
            'evening': ["朝日", "朝焼け", "朝露", "早朝"],
            'night': ["強い日差し", "日焼け", "紫外線対策", "日中の暑さ"]
        },
        'night_hot_expressions': ["蒸し暑い", "熱帯夜", "寝苦しい"],
        'night_hot_threshold': 25,
        'day_cold_threshold': 10
    }


class TimeTemperatureValidator:
    """時間帯と温度表現の矛盾を検証"""
    
    def check_time_temperature_contradiction(
        self,
        weather_comment: str,
        advice_comment: str,
        weather_data: WeatherForecast,
        state: CommentGenerationState | None = None
    ) -> tuple[bool, str]:
        """
        時間帯と温度の表現が矛盾していないかチェック
        
        Args:
            weather_comment: 天気コメント
            advice_comment: アドバイスコメント
            weather_data: 天気データ
            state: コメント生成の状態（時間情報を含む）
            
        Returns:
            (is_consistent, reason): 一貫性チェック結果とその理由
        """
        combined_text = weather_comment + " " + advice_comment
        
        # 対象時刻を取得
        target_hour = self._get_target_hour(weather_data, state)
        
        if target_hour is None:
            return True, ""  # 時刻情報がない場合はチェックしない
        
        # 時間帯の定義を取得
        config = _get_time_temperature_config()
        time_periods = config.get('time_periods', {})
        inappropriate_expressions = config.get('inappropriate_expressions', {})
        
        # 朝の時間帯
        morning = time_periods.get('morning', {})
        if morning.get('start', 5) <= target_hour <= morning.get('end', 9):
            inappropriate_morning = inappropriate_expressions.get('morning', [])
            for expr in inappropriate_morning:
                if expr in combined_text:
                    return False, f"朝の時間帯（{target_hour}時）に不適切な表現: {expr}"
        
        # 昼の時間帯
        day = time_periods.get('day', {})
        if day.get('start', 10) <= target_hour <= day.get('end', 15):
            inappropriate_day = inappropriate_expressions.get('day', [])
            for expr in inappropriate_day:
                if expr in combined_text:
                    return False, f"昼の時間帯（{target_hour}時）に不適切な表現: {expr}"
        
        # 夕方の時間帯
        evening = time_periods.get('evening', {})
        if evening.get('start', 16) <= target_hour <= evening.get('end', 18):
            inappropriate_evening = inappropriate_expressions.get('evening', [])
            for expr in inappropriate_evening:
                if expr in combined_text:
                    return False, f"夕方の時間帯（{target_hour}時）に不適切な表現: {expr}"
        
        # 夜の時間帯（その他の時間）
        else:
            inappropriate_night = inappropriate_expressions.get('night', [])
            for expr in inappropriate_night:
                if expr in combined_text:
                    return False, f"夜の時間帯（{target_hour}時）に不適切な表現: {expr}"
        
        # 温度と時間帯の組み合わせチェック
        return self._check_temperature_time_consistency(
            weather_data.temperature, target_hour, combined_text
        )
    
    def _get_target_hour(
        self, 
        weather_data: WeatherForecast, 
        state: CommentGenerationState | None
    ) -> int | None:
        """対象時刻の時間を取得"""
        # weather_dataから取得を試みる
        if hasattr(weather_data, 'datetime') and weather_data.datetime:
            return weather_data.datetime.hour
        
        # stateから取得を試みる
        if state and hasattr(state, 'target_datetime') and state.target_datetime:
            return state.target_datetime.hour
        
        return None
    
    def _check_temperature_time_consistency(
        self, 
        temperature: float, 
        hour: int, 
        text: str
    ) -> tuple[bool, str]:
        """温度と時間帯の組み合わせの妥当性をチェック"""
        config = _get_time_temperature_config()
        
        # 早朝・夜間の高温表現チェック
        night_hours = config.get('night_hours', {})
        early_morning_end = night_hours.get('early_morning_end', 6)
        night_start = night_hours.get('night_start', 20)
        
        night_hot_threshold = config.get('night_hot_threshold', 25)
        if (hour < early_morning_end or hour >= night_start) and temperature < night_hot_threshold:
            hot_expressions = config.get('night_hot_expressions', [])
            for expr in hot_expressions:
                if expr in text:
                    return False, f"低温（{temperature}°C）の夜間に不適切な暑さ表現: {expr}"
        
        # 日中の低温で日差し関連
        day_hours = config.get('day_hours', {})
        day_start = day_hours.get('start', 10)
        day_end = day_hours.get('end', 15)
        
        day_cold_threshold = config.get('day_cold_threshold', 10)
        if day_start <= hour <= day_end and temperature < day_cold_threshold:
            sunshine_expressions = config.get('sunshine_expressions', ["強い日差し", "日焼け対策"])
            for expr in sunshine_expressions:
                if expr in text:
                    return False, f"低温（{temperature}°C）での日差し表現は不自然: {expr}"
        
        return True, ""
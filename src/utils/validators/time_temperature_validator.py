"""時間帯と温度の矛盾を検証するバリデータ"""

from __future__ import annotations
import logging
from datetime import datetime
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState

logger = logging.getLogger(__name__)


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
        
        # 朝の時間帯（5-9時）
        if 5 <= target_hour <= 9:
            inappropriate_morning = ["夕焼け", "夜風", "日没", "夕暮れ", "星空"]
            for expr in inappropriate_morning:
                if expr in combined_text:
                    return False, f"朝の時間帯（{target_hour}時）に不適切な表現: {expr}"
        
        # 昼の時間帯（10-15時）
        elif 10 <= target_hour <= 15:
            # 昼間に星や月の話は不適切
            inappropriate_day = ["星空", "月明かり", "夜露", "朝露", "朝もや"]
            for expr in inappropriate_day:
                if expr in combined_text:
                    return False, f"昼の時間帯（{target_hour}時）に不適切な表現: {expr}"
        
        # 夕方の時間帯（16-18時）
        elif 16 <= target_hour <= 18:
            inappropriate_evening = ["朝日", "朝焼け", "朝露", "早朝"]
            for expr in inappropriate_evening:
                if expr in combined_text:
                    return False, f"夕方の時間帯（{target_hour}時）に不適切な表現: {expr}"
        
        # 夜の時間帯（19-4時）
        else:
            inappropriate_night = ["強い日差し", "日焼け", "紫外線対策", "日中の暑さ"]
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
        
        # 早朝・夜間の高温表現チェック
        if (hour < 6 or hour > 20) and temperature < 25:
            hot_expressions = ["蒸し暑い", "熱帯夜", "寝苦しい"]
            for expr in hot_expressions:
                if expr in text:
                    return False, f"低温（{temperature}°C）の夜間に不適切な暑さ表現: {expr}"
        
        # 日中の低温で日差し関連
        if 10 <= hour <= 15 and temperature < 10:
            if "強い日差し" in text or "日焼け対策" in text:
                return False, f"低温（{temperature}°C）での強い日差し表現は不自然"
        
        return True, ""
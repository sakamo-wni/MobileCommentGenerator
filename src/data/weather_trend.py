"""気象変化の傾向を表現するデータクラス"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.data.weather_data import WeatherForecast, WeatherCondition
from src.config.config import get_comment_config


class TrendDirection(Enum):
    """変化の方向"""
    IMPROVING = "improving"  # 改善
    STABLE = "stable"  # 安定
    WORSENING = "worsening"  # 悪化
    FLUCTUATING = "fluctuating"  # 変動


@dataclass
class WeatherTrend:
    """気象変化の傾向を表すデータクラス
    
    Attributes:
        start_forecast: 開始時点の予報
        end_forecast: 終了時点の予報
        hourly_forecasts: 時間毎の予報リスト（3時間ごと）
        weather_trend: 天気の変化傾向
        temperature_trend: 気温の変化傾向
        temperature_change: 気温変化量（℃）
        max_temperature: 期間中の最高気温
        min_temperature: 期間中の最低気温
        precipitation_total: 期間中の総降水量
        has_weather_change: 天気の変化があるか
        weather_changes: 天気変化のタイミングと内容
    """
    
    start_forecast: WeatherForecast
    end_forecast: WeatherForecast
    hourly_forecasts: list[WeatherForecast]
    weather_trend: TrendDirection
    temperature_trend: TrendDirection
    temperature_change: float
    max_temperature: float
    min_temperature: float
    precipitation_total: float
    has_weather_change: bool
    weather_changes: list[tuple[datetime, str, str]]  # (時刻, 変化前, 変化後)
    
    @classmethod
    def from_forecasts(cls, forecasts: list[WeatherForecast]) -> "WeatherTrend":
        """予報リストから気象傾向を分析して生成
        
        Args:
            forecasts: 時系列順の予報リスト
            
        Returns:
            WeatherTrend インスタンス
        """
        if len(forecasts) < 2:
            raise ValueError("気象傾向の分析には最低2つの予報が必要です")
            
        start = forecasts[0]
        end = forecasts[-1]
        
        # 気温変化の計算
        temperature_change = end.temperature - start.temperature
        temperatures = [f.temperature for f in forecasts]
        max_temp = max(temperatures)
        min_temp = min(temperatures)
        
        # 気温傾向の判定
        if abs(temperature_change) < 2.0:
            temp_trend = TrendDirection.STABLE
        elif temperature_change > 0:
            temp_trend = TrendDirection.IMPROVING if start.temperature < 25 else TrendDirection.WORSENING
        else:
            temp_trend = TrendDirection.WORSENING if start.temperature > 15 else TrendDirection.IMPROVING
            
        # 天気変化の検出
        weather_changes = []
        prev_condition = forecasts[0].weather_condition
        
        for i in range(1, len(forecasts)):
            curr_condition = forecasts[i].weather_condition
            if curr_condition != prev_condition:
                weather_changes.append((
                    forecasts[i].datetime,
                    prev_condition.value,
                    curr_condition.value
                ))
                prev_condition = curr_condition
                
        has_weather_change = len(weather_changes) > 0
        
        # 天気傾向の判定
        weather_trend = cls._determine_weather_trend(forecasts, weather_changes)
        
        # 総降水量の計算
        precipitation_total = sum(f.precipitation for f in forecasts)
        
        return cls(
            start_forecast=start,
            end_forecast=end,
            hourly_forecasts=forecasts,
            weather_trend=weather_trend,
            temperature_trend=temp_trend,
            temperature_change=temperature_change,
            max_temperature=max_temp,
            min_temperature=min_temp,
            precipitation_total=precipitation_total,
            has_weather_change=has_weather_change,
            weather_changes=weather_changes
        )
    
    @staticmethod
    def _determine_weather_trend(forecasts: list[WeatherForecast], 
                                changes: list[tuple[datetime, str, str]]) -> TrendDirection:
        """天気の変化傾向を判定"""
        if not changes:
            return TrendDirection.STABLE
            
        if len(changes) >= 2:
            return TrendDirection.FLUCTUATING
            
        # 1回の変化の場合、改善か悪化かを判定
        start_condition = forecasts[0].weather_condition
        end_condition = forecasts[-1].weather_condition
        
        # 設定から天気スコアを取得
        config = get_comment_config()
        condition_scores = config.weather_scores
        
        start_score = condition_scores.get(start_condition, 2)
        end_score = condition_scores.get(end_condition, 2)
        
        if end_score > start_score:
            return TrendDirection.IMPROVING
        elif end_score < start_score:
            return TrendDirection.WORSENING
        else:
            return TrendDirection.STABLE
            
    def get_summary(self) -> str:
        """気象変化の要約を生成"""
        summaries = []
        
        # 天気変化
        if self.has_weather_change:
            change_desc = []
            for dt, before, after in self.weather_changes:
                time_str = dt.strftime("%H時")
                change_desc.append(f"{time_str}頃{before}から{after}へ")
            summaries.append("、".join(change_desc))
            
        # 気温変化
        if abs(self.temperature_change) >= 5:
            direction = "上昇" if self.temperature_change > 0 else "下降"
            summaries.append(f"気温{abs(self.temperature_change):.1f}°C{direction}")
            
        # 降水
        if self.precipitation_total > 0:
            summaries.append(f"総降水量{self.precipitation_total:.1f}mm")
            
        return "。".join(summaries) if summaries else "大きな変化なし"

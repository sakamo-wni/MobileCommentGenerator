"""
天気予報データ変換モジュール

天気予報データの変換・加工・集計機能を提供
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.weather_trend import WeatherTrend
from src.config.config import get_weather_config

logger = logging.getLogger(__name__)


class WeatherDataTransformer:
    """天気予報データ変換クラス"""
    
    def __init__(self):
        """初期化"""
        self.config = get_weather_config()
    
    def filter_forecasts_by_hours(
        self,
        forecasts: list[WeatherForecast],
        hours: int,
    ) -> list[WeatherForecast]:
        """指定時間内の予報データをフィルタリング
        
        Args:
            forecasts: 天気予報リスト
            hours: 予報時間数
            
        Returns:
            フィルタリングされた天気予報リスト
        """
        if hours <= 0:
            return forecasts
        
        now = datetime.now()
        cutoff_time = now + timedelta(hours=hours)
        
        return [forecast for forecast in forecasts if forecast.datetime <= cutoff_time]
    
    def generate_weather_summary(self, forecasts: list[WeatherForecast]) -> dict[str, Any]:
        """天気概要を生成
        
        Args:
            forecasts: 天気予報リスト
            
        Returns:
            天気概要辞書
        """
        if not forecasts:
            return {}
        
        # 指定時間後の天気
        target_time = datetime.now() + timedelta(hours=self.config.forecast_hours_ahead)
        current_forecast = min(
            forecasts,
            key=lambda f: abs((f.datetime - target_time).total_seconds()),
        )
        
        # デバッグ情報
        logger.info(f"generate_weather_summary - ターゲット時刻: {target_time}, 選択された予報時刻: {current_forecast.datetime}")
        logger.info(f"generate_weather_summary - 選択された天気データ: {current_forecast.temperature}°C, {current_forecast.weather_description}")
        
        # 気温統計
        temperatures = [f.temperature for f in forecasts]
        precipitations = [f.precipitation for f in forecasts]
        
        # 天気パターン分析
        weather_conditions = [f.weather_condition for f in forecasts]
        condition_counts = {}
        for condition in weather_conditions:
            condition_counts[condition.value] = condition_counts.get(condition.value, 0) + 1
        
        # 主要な天気状況
        dominant_condition = max(condition_counts.items(), key=lambda x: x[1])
        
        # 雨の予測
        rain_forecasts = [f for f in forecasts if f.precipitation > 0.1]
        rain_probability = len(rain_forecasts) / len(forecasts) if forecasts else 0
        
        # 悪天候の判定
        severe_weather_forecasts = [f for f in forecasts if f.is_severe_weather()]
        has_severe_weather = len(severe_weather_forecasts) > 0
        
        return {
            "current_weather": {
                "temperature": current_forecast.temperature,
                "condition": current_forecast.weather_condition.value,
                "description": current_forecast.weather_description,
                "precipitation": current_forecast.precipitation,
                "comfort_level": current_forecast.get_comfort_level(),
            },
            "temperature_range": {
                "max": max(temperatures),
                "min": min(temperatures),
                "average": sum(temperatures) / len(temperatures),
            },
            "precipitation": {
                "total": sum(precipitations),
                "max_hourly": max(precipitations),
                "probability": rain_probability * 100,
            },
            "dominant_condition": {
                "condition": dominant_condition[0],
                "frequency": dominant_condition[1] / len(forecasts),
            },
            "alerts": {
                "has_severe_weather": has_severe_weather,
                "severe_weather_count": len(severe_weather_forecasts),
                "high_precipitation": max(precipitations) > 10.0,
                "extreme_temperature": any(t < 0 or t > 35 for t in temperatures),
            },
            "recommendations": self._generate_recommendations(forecasts),
        }
    
    def _generate_recommendations(self, forecasts: list[WeatherForecast]) -> list[str]:
        """天気に基づく推奨事項を生成
        
        Args:
            forecasts: 天気予報リスト
            
        Returns:
            推奨事項のリスト
        """
        recommendations = []
        
        if not forecasts:
            return recommendations
        
        # 雨の予測チェック
        rain_forecasts = [f for f in forecasts if f.precipitation > 0.1]
        if rain_forecasts:
            max_precipitation = max(f.precipitation for f in rain_forecasts)
            if max_precipitation > 10.0:
                recommendations.append("傘の携帯をおすすめします（強い雨の予報）")
            else:
                recommendations.append("念のため傘をお持ちください")
        
        # 気温チェック
        temperatures = [f.temperature for f in forecasts]
        max_temp = max(temperatures)
        min_temp = min(temperatures)
        
        if max_temp > 30:
            recommendations.append("暑くなる予報です。水分補給や熱中症対策をお忘れなく")
        elif max_temp < 5:
            recommendations.append("寒くなる予報です。防寒対策をしっかりと")
        elif min_temp < 0:
            recommendations.append("氷点下になる可能性があります。路面凍結にご注意ください")
        
        # 風速チェック
        strong_winds = [f for f in forecasts if f.wind_speed > 10.0]
        if strong_winds:
            recommendations.append("強風の予報があります。外出時はご注意ください")
        
        # 悪天候チェック
        severe_weather = [f for f in forecasts if f.is_severe_weather()]
        if severe_weather:
            recommendations.append("悪天候の予報があります。不要な外出は控えることをおすすめします")
        
        # 良い天気の場合
        good_weather = [f for f in forecasts if f.is_good_weather()]
        if len(good_weather) > len(forecasts) * 0.7:  # 70%以上が良い天気
            recommendations.append("良い天気が続く予報です。外出日和ですね")
        
        return recommendations
    
    def analyze_weather_trend(self, forecasts: list[WeatherForecast]) -> WeatherTrend:
        """気象変化傾向を分析
        
        Args:
            forecasts: 天気予報リスト
            
        Returns:
            気象変化傾向
        """
        return WeatherTrend.from_forecasts(forecasts)
    
    def transform_for_state(
        self,
        forecasts: list[WeatherForecast],
        location_name: str,
        generated_at: datetime,
    ) -> dict[str, Any]:
        """状態辞書用に天気データを変換
        
        Args:
            forecasts: 天気予報リスト
            location_name: 地点名
            generated_at: 生成日時
            
        Returns:
            状態辞書用の天気データ
        """
        # 天気概要を生成
        weather_summary = self.generate_weather_summary(forecasts)
        
        return {
            "weather_data": {
                "location": location_name,
                "forecasts": [f.to_dict() for f in forecasts],
                "generated_at": generated_at.isoformat(),
                "summary": weather_summary,
            },
            "weather_summary": weather_summary,
        }
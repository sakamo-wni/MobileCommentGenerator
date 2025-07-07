"""
天気データ検証モジュール

天気予報データの妥当性を検証する機能
"""

from typing import Optional, List, Tuple
from datetime import datetime, timedelta

from src.data.weather.models import WeatherForecast
from src.data.weather.enums import WeatherCondition


class WeatherValidator:
    """天気データの検証を行うクラス"""
    
    @staticmethod
    def validate_forecast(forecast: WeatherForecast) -> Tuple[bool, List[str]]:
        """天気予報データの妥当性を検証
        
        Args:
            forecast: 検証対象の天気予報
            
        Returns:
            (is_valid, errors): 妥当性とエラーメッセージのリスト
        """
        errors = []
        
        # 気温の妥当性チェック
        if forecast.temperature < -50 or forecast.temperature > 60:
            errors.append(f"気温が異常範囲: {forecast.temperature}°C")
        
        # 体感温度の妥当性チェック
        if abs(forecast.feels_like - forecast.temperature) > 20:
            errors.append(f"体感温度と気温の差が大きすぎます: {abs(forecast.feels_like - forecast.temperature)}°C")
        
        # 湿度の妥当性チェック
        if forecast.humidity < 0 or forecast.humidity > 100:
            errors.append(f"湿度が異常範囲: {forecast.humidity}%")
        
        # 降水量の妥当性チェック
        if forecast.precipitation_mm < 0:
            errors.append(f"降水量が負の値: {forecast.precipitation_mm}mm")
        elif forecast.precipitation_mm > 500:
            errors.append(f"降水量が異常に多い: {forecast.precipitation_mm}mm")
        
        # 風速の妥当性チェック
        if forecast.wind_speed < 0:
            errors.append(f"風速が負の値: {forecast.wind_speed}m/s")
        elif forecast.wind_speed > 100:
            errors.append(f"風速が異常に高い: {forecast.wind_speed}m/s")
        
        # 気圧の妥当性チェック（設定されている場合）
        if forecast.pressure is not None:
            if forecast.pressure < 870 or forecast.pressure > 1090:
                errors.append(f"気圧が異常範囲: {forecast.pressure}hPa")
        
        # 視程の妥当性チェック（設定されている場合）
        if forecast.visibility is not None:
            if forecast.visibility < 0 or forecast.visibility > 100:
                errors.append(f"視程が異常範囲: {forecast.visibility}km")
        
        # UV指数の妥当性チェック（設定されている場合）
        if forecast.uv_index is not None:
            if forecast.uv_index < 0 or forecast.uv_index > 15:
                errors.append(f"UV指数が異常範囲: {forecast.uv_index}")
        
        # 雲量の妥当性チェック（設定されている場合）
        if forecast.cloud_cover is not None:
            if forecast.cloud_cover < 0 or forecast.cloud_cover > 100:
                errors.append(f"雲量が異常範囲: {forecast.cloud_cover}%")
        
        # 天気と降水量の整合性チェック
        if forecast.weather in [WeatherCondition.RAIN, WeatherCondition.HEAVY_RAIN]:
            if forecast.precipitation_mm < 0.1:
                errors.append(f"雨天なのに降水量が少なすぎます: {forecast.precipitation_mm}mm")
        elif forecast.weather == WeatherCondition.CLEAR:
            if forecast.precipitation_mm > 1.0:
                errors.append(f"晴天なのに降水量があります: {forecast.precipitation_mm}mm")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def is_stable_weather(forecast: WeatherForecast) -> bool:
        """安定した天気かどうかを判定
        
        天気の変化が少なく、穏やかな状態かを判定
        
        Args:
            forecast: 判定対象の天気予報
            
        Returns:
            bool: 安定した天気の場合True
        """
        # 不安定な天気条件
        unstable_conditions = [
            WeatherCondition.THUNDER,
            WeatherCondition.STORM,
            WeatherCondition.SEVERE_STORM,
        ]
        
        if forecast.weather in unstable_conditions:
            return False
        
        # 風速が強い場合は不安定
        if forecast.wind_speed > 10:
            return False
        
        # 降水量が多い場合は不安定
        if forecast.precipitation_mm > 10:
            return False
        
        return True
    
    @staticmethod
    def get_weather_stability(forecast: WeatherForecast) -> str:
        """天気の安定性を文字列で取得
        
        Args:
            forecast: 判定対象の天気予報
            
        Returns:
            str: 安定/やや不安定/不安定/非常に不安定
        """
        # 特殊な気象状況は非常に不安定
        if forecast.weather.is_special_condition:
            return "非常に不安定"
        
        # 各要素のスコアを計算
        stability_score = 0
        
        # 天気条件によるスコア
        if forecast.weather in [WeatherCondition.CLEAR, WeatherCondition.PARTLY_CLOUDY]:
            stability_score += 3
        elif forecast.weather == WeatherCondition.CLOUDY:
            stability_score += 2
        elif forecast.weather == WeatherCondition.RAIN:
            stability_score += 1
        
        # 風速によるスコア
        if forecast.wind_speed < 5:
            stability_score += 2
        elif forecast.wind_speed < 10:
            stability_score += 1
        
        # 降水量によるスコア
        if forecast.precipitation_mm < 1:
            stability_score += 2
        elif forecast.precipitation_mm < 5:
            stability_score += 1
        
        # スコアに基づいて判定
        if stability_score >= 6:
            return "安定"
        elif stability_score >= 4:
            return "やや不安定"
        elif stability_score >= 2:
            return "不安定"
        else:
            return "非常に不安定"
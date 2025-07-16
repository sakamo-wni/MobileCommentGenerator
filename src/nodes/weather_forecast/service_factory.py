"""
Weather forecast service factory

サービスの依存性注入を管理するファクトリークラス
"""

from __future__ import annotations
from src.nodes.weather_forecast.services import (
    LocationService,
    WeatherAPIService,
    ForecastProcessingService,
    TemperatureAnalysisService
)


class WeatherForecastServiceFactory:
    """天気予報サービスのファクトリークラス
    
    依存性注入パターンを使用してサービスインスタンスを管理
    テスト時にはモックサービスを注入可能
    """
    
    def __init__(
        self,
        location_service: LocationService | None = None,
        weather_api_service: WeatherAPIService | None = None,
        forecast_processing_service: ForecastProcessingService | None = None,
        temperature_analysis_service: TemperatureAnalysisService | None = None
    ):
        """サービスファクトリーの初期化
        
        Args:
            location_service: 地点サービス（Noneの場合はデフォルト実装を使用）
            weather_api_service: API通信サービス（Noneの場合はAPIキーが必要）
            forecast_processing_service: 予報処理サービス
            temperature_analysis_service: 温度分析サービス
        """
        self._location_service = location_service
        self._weather_api_service = weather_api_service
        self._forecast_processing_service = forecast_processing_service
        self._temperature_analysis_service = temperature_analysis_service
        self._api_key: str | None = None
    
    def set_api_key(self, api_key: str) -> None:
        """APIキーを設定"""
        self._api_key = api_key
    
    def get_location_service(self) -> LocationService:
        """地点サービスを取得"""
        if self._location_service is None:
            self._location_service = LocationService()
        return self._location_service
    
    def get_weather_api_service(self) -> WeatherAPIService:
        """API通信サービスを取得"""
        if self._weather_api_service is None:
            if self._api_key is None:
                raise ValueError("WeatherAPIServiceを使用するにはAPIキーが必要です")
            self._weather_api_service = WeatherAPIService(self._api_key)
        return self._weather_api_service
    
    def get_forecast_processing_service(self) -> ForecastProcessingService:
        """予報処理サービスを取得"""
        if self._forecast_processing_service is None:
            self._forecast_processing_service = ForecastProcessingService()
        return self._forecast_processing_service
    
    def get_temperature_analysis_service(self) -> TemperatureAnalysisService:
        """温度分析サービスを取得"""
        if self._temperature_analysis_service is None:
            self._temperature_analysis_service = TemperatureAnalysisService()
        return self._temperature_analysis_service
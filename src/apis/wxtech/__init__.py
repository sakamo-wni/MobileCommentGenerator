"""
WxTech API モジュール

天気予報APIとの通信を管理するモジュール
"""

from src.apis.wxtech.client import WxTechAPIClient, get_japan_1km_mesh_weather_forecast
from src.apis.wxtech.errors import WxTechAPIError

__all__ = [
    "WxTechAPIClient",
    "WxTechAPIError",
    "get_japan_1km_mesh_weather_forecast",
]
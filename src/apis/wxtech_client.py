"""
WxTech API クライアント(後方互換性のためのラッパー)

このファイルは後方互換性のために残されています。
新しいコードでは src.apis.wxtech モジュールを直接インポートしてください。
"""

import warnings

# 後方互換性のためのインポート
from src.apis.wxtech import (
    WxTechAPIClient,
    WxTechAPIError,
    get_japan_1km_mesh_weather_forecast,
)

# 非推奨警告
warnings.warn(
    "src.apis.wxtech_client は非推奨です。"
    "代わりに src.apis.wxtech を使用してください。",
    DeprecationWarning,
    stacklevel=2,
)

# すべてのエクスポートを再エクスポート
__all__ = [
    "WxTechAPIClient",
    "WxTechAPIError",
    "get_japan_1km_mesh_weather_forecast",
]

"""天気コメント検証システム - 互換性のためのエイリアス"""

from __future__ import annotations
import warnings

# 後方互換性のため、validators パッケージから WeatherCommentValidator をインポート
from .validators.weather_comment_validator import WeatherCommentValidator

# 新しいリファクタリングされたバージョンへの移行を推奨
warnings.warn(
    "weather_comment_validator.WeatherCommentValidator は非推奨です。"
    "weather_specific.WeatherCommentValidatorRefactored を使用してください。",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['WeatherCommentValidator']
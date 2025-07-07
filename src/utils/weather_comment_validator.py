"""天気コメント検証システム - 互換性のためのエイリアス"""

# 後方互換性のため、validators パッケージから WeatherCommentValidator をインポート
from .validators.weather_comment_validator import WeatherCommentValidator

__all__ = ['WeatherCommentValidator']
"""天気コメント生成システム - UI定数定義"""


class ProgressConstants:
    """プログレス関連の定数"""
    COMPLETE_DELAY = 0.5  # プログレス完了後の待機時間（秒）
    UPDATE_INTERVAL = 0.1  # プログレス更新間隔（秒）


class LayoutConstants:
    """レイアウト関連の定数"""
    DEFAULT_COLUMN_RATIO = [1, 2]  # デフォルトのカラム比率
    SIDEBAR_MIN_WIDTH = 300  # サイドバー最小幅（ピクセル）


class DisplayConstants:
    """表示関連の定数"""
    MAX_DISPLAY_HISTORY = 10  # 履歴表示の最大数
    COMMENT_PREVIEW_LENGTH = 100  # コメントプレビューの最大文字数
    ERROR_DISPLAY_DURATION = 5  # エラー表示時間（秒）


class IconConstants:
    """アイコン関連の定数"""
    WEATHER = "🌤️"
    LOCATION = "📍"
    TIME = "⏰"
    TEMPERATURE = "🌡️"
    WIND = "💨"
    HUMIDITY = "💧"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    CLOUD = "☁️"
    TARGET = "🎯"
    DETAIL = "📊"
    CALENDAR = "📅"


# 互換性のためのエイリアス（段階的な移行用）
class UIConstants:
    """UI関連の定数定義（非推奨：個別のクラスを使用してください）"""
    
    # プログレス関連
    PROGRESS_COMPLETE_DELAY = ProgressConstants.COMPLETE_DELAY
    PROGRESS_UPDATE_INTERVAL = ProgressConstants.UPDATE_INTERVAL
    
    # レイアウト関連
    DEFAULT_COLUMN_RATIO = LayoutConstants.DEFAULT_COLUMN_RATIO
    SIDEBAR_MIN_WIDTH = LayoutConstants.SIDEBAR_MIN_WIDTH
    
    # 表示関連
    MAX_DISPLAY_HISTORY = DisplayConstants.MAX_DISPLAY_HISTORY
    COMMENT_PREVIEW_LENGTH = DisplayConstants.COMMENT_PREVIEW_LENGTH
    ERROR_DISPLAY_DURATION = DisplayConstants.ERROR_DISPLAY_DURATION
    
    # アイコン
    ICON_WEATHER = IconConstants.WEATHER
    ICON_LOCATION = IconConstants.LOCATION
    ICON_TIME = IconConstants.TIME
    ICON_TEMPERATURE = IconConstants.TEMPERATURE
    ICON_WIND = IconConstants.WIND
    ICON_HUMIDITY = IconConstants.HUMIDITY
    ICON_SUCCESS = IconConstants.SUCCESS
    ICON_ERROR = IconConstants.ERROR
    ICON_WARNING = IconConstants.WARNING
    ICON_INFO = IconConstants.INFO

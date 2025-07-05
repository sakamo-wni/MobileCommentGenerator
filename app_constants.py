"""天気コメント生成システム - UI定数定義"""


class UIConstants:
    """UI関連の定数定義"""

    # プログレス関連
    PROGRESS_COMPLETE_DELAY = 0.5  # プログレス完了後の待機時間（秒）
    PROGRESS_UPDATE_INTERVAL = 0.1  # プログレス更新間隔（秒）

    # レイアウト関連
    DEFAULT_COLUMN_RATIO = [1, 2]  # デフォルトのカラム比率
    SIDEBAR_MIN_WIDTH = 300  # サイドバー最小幅（ピクセル）

    # 表示関連
    MAX_DISPLAY_HISTORY = 10  # 履歴表示の最大数
    COMMENT_PREVIEW_LENGTH = 100  # コメントプレビューの最大文字数

    # エラー表示
    ERROR_DISPLAY_DURATION = 5  # エラー表示時間（秒）

    # アイコン
    ICON_WEATHER = "🌤️"
    ICON_LOCATION = "📍"
    ICON_TIME = "⏰"
    ICON_TEMPERATURE = "🌡️"
    ICON_WIND = "💨"
    ICON_HUMIDITY = "💧"
    ICON_SUCCESS = "✅"
    ICON_ERROR = "❌"
    ICON_WARNING = "⚠️"
    ICON_INFO = "ℹ️"

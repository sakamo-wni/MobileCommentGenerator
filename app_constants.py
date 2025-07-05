"""UIおよびアプリケーション全体の定数定義"""

# UI関連の定数
UI_SLEEP_DURATION = 0.5  # 進捗完了後の待機時間（秒）
PROGRESS_MIN = 0.0  # プログレスバーの最小値
PROGRESS_MAX = 1.0  # プログレスバーの最大値

# 表示関連
RESULT_HEADER = "### 🌤️ 生成結果"
INPUT_HEADER = "📍 入力設定"
RESULT_SECTION_HEADER = "💬 生成結果"
GENERATION_TIME_FORMAT = "🕐 生成時刻: {}"
GENERATION_BUTTON_TEXT = "🎯 コメント生成"

# エラーメッセージ
NO_LOCATION_ERROR = "地点が選択されていません"
LOCATION_LIMIT_WARNING = "⚠️ 選択された地点数が上限（{}地点）を超えています。"
API_KEY_WARNING = "⚠️ WXTECH_API_KEYが設定されていません。天気予報データの取得ができません。"

# 成功メッセージ
GENERATION_COMPLETE_SUCCESS = "✅ コメント生成が完了しました！ ({}地点成功)"
GENERATION_PROGRESS = "生成中... {} ({}/{})"
GENERATION_COMPLETE = "完了！{}/{}地点の生成が成功しました"
GENERATION_ALL_FAILED = "エラー：すべての地点でコメント生成に失敗しました"

# サイドバー
SIDEBAR_SETTINGS_HEADER = "設定"
SIDEBAR_API_KEY_HEADER = "APIキー設定"
SIDEBAR_HISTORY_HEADER = "生成履歴"

# デバッグ
DEBUG_INFO_HEADER = "デバッグ情報"

# フッター
FOOTER_VERSION = "**Version**: 1.0.0"
FOOTER_LAST_UPDATED = "**Last Updated**: 2025-06-06"
FOOTER_BY = "**By**: WNI Team"

# カラム比率
MAIN_COLUMN_RATIO = [1, 2]  # 入力パネル：結果表示の比率

# サンプルコメント
SAMPLE_COMMENTS = """
**晴れの日**: 爽やかな朝ですね  
**雨の日**: 傘をお忘れなく  
**曇りの日**: 過ごしやすい一日です  
**雪の日**: 足元にお気をつけて
"""

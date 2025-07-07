"""
Weather forecast node constants

天気予報ノードで使用する定数定義
"""

# API関連の定数
API_MAX_RETRIES = 3  # API呼び出しの最大リトライ回数
API_INITIAL_RETRY_DELAY = 1.0  # 初回リトライ遅延（秒）
API_RETRY_BACKOFF_MULTIPLIER = 2  # リトライ遅延の指数バックオフ乗数

# 時刻関連の定数
DEFAULT_TARGET_HOURS = [9, 12, 15, 18]  # デフォルトの予報対象時刻
DATE_BOUNDARY_HOUR = 6  # 日付境界時刻（この時刻より前は前日扱い）

# 分析関連の定数
TREND_ANALYSIS_MIN_FORECASTS = 2  # トレンド分析に必要な最小予報数
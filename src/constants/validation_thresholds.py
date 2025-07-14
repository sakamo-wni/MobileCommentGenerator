"""Validation threshold constants."""

# Temperature thresholds for symptom checks (Celsius)
HEATSTROKE_WARNING_TEMP = 35.0  # 熱中症警告温度
COLD_PREVENTION_TEMP = 15.0     # 防寒対策推奨温度
COMFORTABLE_HIGH_TEMP = 30.0     # 快適上限温度

# Time-specific check hours
TIME_CHECK_HOURS = [9, 12, 15, 18]
SUNNY_CHECK_HOURS = [9, 15, 18]

# Text similarity thresholds
MIN_TEXT_LENGTH_FOR_SIMILARITY = 10
TEXT_LENGTH_RATIO_THRESHOLD = 2.0  # Maximum acceptable length ratio
SIMILARITY_RATIO_HIGH = 0.7
SIMILARITY_RATIO_MEDIUM = 0.6

# Character count thresholds
MIN_PHRASE_LENGTH = 4  # Minimum phrase length for meaningful comparison
"""Weather-related constants."""

# Temperature boundaries (Celsius)
TEMPERATURE_MIN = -50.0
TEMPERATURE_MAX = 60.0
TEMPERATURE_COMFORTABLE_MIN = 10.0
TEMPERATURE_COMFORTABLE_MAX = 30.0

# Humidity boundaries (percentage)
HUMIDITY_MIN = 0.0
HUMIDITY_MAX = 100.0

# Wind speed boundaries (m/s)
WIND_SPEED_MIN = 0.0
WIND_SPEED_MAX = 200.0
WIND_SPEED_THRESHOLD_STRONG = 15.0

# Precipitation thresholds (mm)
PRECIPITATION_THRESHOLD_NONE = 0.5
PRECIPITATION_THRESHOLD_LIGHT = 0.1
PRECIPITATION_THRESHOLD_LIGHT_RAIN = 2.0
PRECIPITATION_THRESHOLD_MODERATE = 5.0
PRECIPITATION_THRESHOLD_HEAVY = 10.0
PRECIPITATION_THRESHOLD_VERY_HEAVY = 30.0

# Weather condition thresholds
CLEAR_WEATHER_CLOUD_COVERAGE_MAX = 20  # percentage
PARTLY_CLOUDY_CLOUD_COVERAGE_MAX = 60  # percentage

# Wind direction degrees
WIND_DIRECTION_MIN_DEGREES = 0
WIND_DIRECTION_MAX_DEGREES = 360

# Special weather priority threshold
SPECIAL_WEATHER_PRIORITY_THRESHOLD = 4

# Comment generation constants
COMMENT_MAX_LENGTH = 15  # Maximum comment length in characters
COMMENT_CANDIDATE_LIMIT = 10  # Number of candidates to pass to LLM
CONTINUOUS_RAIN_THRESHOLD_HOURS = 4  # Hours for continuous rain detection

# Temperature thresholds for heatstroke warnings
HEATSTROKE_THRESHOLD_TEMP = 35.0  # Temperature for heatstroke warnings (Celsius)
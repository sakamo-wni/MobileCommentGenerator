# Rain Comment Selection Issue Analysis

## Problem Summary
When there's rain in the forecast at a later time (e.g., 15:00) but not at the base time (09:00), the system fails to select rain-related comments.

**Example Case: Nagano (長野)**
- 09:00: No rain (0mm) - Base time
- 12:00: No rain
- 15:00: Rain (1mm) ⚠️
- 18:00: No rain

**Result**: Selected comment "穏やかな空　蒸し暑い" (calm sky, humid) - No mention of rain!

## Root Cause Analysis

### 1. Data Collection (✅ Working Correctly)
In `src/nodes/weather_forecast_node.py`:
- Lines 353-377: Collects forecasts for 4 time points (9:00, 12:00, 15:00, 18:00)
- Line 384: Stores all 4 forecasts as `period_forecasts` in metadata
- Line 389: Creates `weather_trend` from these forecasts

### 2. Comment Filtering (✅ Working Correctly)
In `src/nodes/comment_selector/utils.py` (`prepare_weather_candidates` method):
- Lines 106-119: Retrieves `period_forecasts` from state metadata
- Lines 110-118: Checks ALL time points for rain
- Line 132: If rain is found at ANY time point, prioritizes rain comments

### 3. LLM Prompt Generation (❌ BUG HERE!)
In `src/nodes/comment_selector/llm_selector.py` (`_format_weather_context` method):
- Lines 124-178: Creates weather context for LLM
- Lines 164-172: ONLY checks `weather_data.precipitation` (base time 09:00)
- **MISSING**: No check of `period_forecasts` for rain at other times!

### 4. LLM Selection
The LLM receives incomplete information:
```
現在の天気情報:
- 場所: 長野
- 日時: 2024年7月8日 09時
- 天気: 晴れ
- 気温: 25.8°C
- 湿度: 73%
- 降水量: 0.0mm  ← Only 09:00 data!
- 風速: 2.0m/s
```

The LLM doesn't know about the 1mm rain at 15:00, so it selects a non-rain comment.

## The Fix Needed

The `_format_weather_context` method needs to be updated to include information about all 4 time points, especially highlighting any precipitation:

```python
def _format_weather_context(self, weather_data: WeatherForecast, location_name: str, target_datetime: datetime, state: Optional[CommentGenerationState] = None) -> str:
    """天気情報をLLM用に整形（時系列分析を含む）"""
    
    # Basic weather info...
    
    # ADD: Check period_forecasts for rain at other times
    if state and hasattr(state, 'generation_metadata'):
        period_forecasts = state.generation_metadata.get('period_forecasts', [])
        if period_forecasts:
            # Check for rain in any time point
            rain_times = []
            for forecast in period_forecasts:
                if forecast.precipitation > 0:
                    time_str = forecast.datetime.strftime('%H時')
                    rain_times.append(f"{time_str}: {forecast.precipitation}mm")
            
            if rain_times:
                context += "\n【重要】本日の降水予報:\n"
                for rain_time in rain_times:
                    context += f"- {rain_time}\n"
                context += "【最重要】雨に関するコメントを最優先で選択してください\n"
```

## Impact
This bug causes the system to miss rain events that occur outside the base time (09:00), leading to inappropriate comment selection that doesn't warn users about upcoming rain.
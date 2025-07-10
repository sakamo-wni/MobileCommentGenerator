# Weather Constants Import Update Examples

## Summary of Changes

All imports from `weather_constants.py` need to be updated to use the new `get_weather_constants()` function from `config.py`. This ensures that constants can be dynamically configured via environment variables.

## Detailed Examples

### 1. src/nodes/comment_selector/validation.py

**Current Code (line 16):**
```python
from src.config.weather_constants import WEATHER_CHANGE_THRESHOLD
```

**Updated Code:**
```python
from src.config.config import get_weather_constants

# Add at module level after imports:
weather_constants = get_weather_constants()
WEATHER_CHANGE_THRESHOLD = weather_constants.WEATHER_CHANGE_THRESHOLD
```

**Usage in the file remains the same:**
- Line 441: `if type_changes >= WEATHER_CHANGE_THRESHOLD:`
- Line 151: `if type_changes >= WEATHER_CHANGE_THRESHOLD:`

### 2. src/formatters/weather_timeline_formatter.py

**Current Code (line 12):**
```python
from src.config.weather_constants import WEATHER_CHANGE_THRESHOLD
```

**Updated Code:**
```python
from src.config.config import get_weather_constants
```

**In the `__init__` method (line 20):**
```python
def __init__(self):
    self.cache = ForecastCache()
    self.jst = pytz.timezone("Asia/Tokyo")
    # Add this line:
    self.weather_constants = get_weather_constants()
```

**Update usage (line 151):**
```python
# Change from:
if type_changes >= WEATHER_CHANGE_THRESHOLD:
# To:
if type_changes >= self.weather_constants.WEATHER_CHANGE_THRESHOLD:
```

### 3. src/utils/validators/weather_validator.py

**Current Code (lines 6 and 178):**
```python
from src.config.weather_constants import SUNNY_WEATHER_KEYWORDS
# ... later in the file ...
from src.config.weather_constants import PrecipitationThresholds
```

**Updated Code:**
```python
from src.config.config import get_weather_constants
```

**In the `__init__` method (line 23):**
```python
def __init__(self):
    super().__init__()
    # Add these lines:
    weather_constants = get_weather_constants()
    self.SUNNY_WEATHER_KEYWORDS = weather_constants.SUNNY_WEATHER_KEYWORDS
    self.PrecipitationThresholds = weather_constants.PrecipitationThresholds
    
    self._initialize_weather_forbidden_words()
```

**Update usage:**
- Line 158: Change `SUNNY_WEATHER_KEYWORDS` to `self.SUNNY_WEATHER_KEYWORDS`
- Line 180: Change `PrecipitationThresholds.HEAVY_RAIN` to `self.PrecipitationThresholds.HEAVY_RAIN`
- Line 187: Change `PrecipitationThresholds.MODERATE_RAIN` to `self.PrecipitationThresholds.MODERATE_RAIN`

### 4. src/utils/validators/weather_specific/temperature_condition_validator.py

**Current Code (lines 7-10):**
```python
from src.config.weather_constants import (
    HEATSTROKE_WARNING_TEMP,
    HEATSTROKE_SEVERE_TEMP,
    COLD_WARNING_TEMP,
)
```

**Updated Code:**
```python
from src.config.config import get_weather_constants
```

**In the `__init__` method (line 19):**
```python
def __init__(self):
    # Add these lines:
    weather_constants = get_weather_constants()
    self.HEATSTROKE_WARNING_TEMP = weather_constants.HEATSTROKE_WARNING_TEMP
    self.HEATSTROKE_SEVERE_TEMP = weather_constants.HEATSTROKE_SEVERE_TEMP
    self.COLD_WARNING_TEMP = weather_constants.COLD_WARNING_TEMP
    
    # Existing code:
    self.temperature_forbidden_words = {
        # ...
    }
```

**Update usage:**
- Line 113: Change `HEATSTROKE_SEVERE_TEMP` to `self.HEATSTROKE_SEVERE_TEMP`
- Line 119: Change `COLD_WARNING_TEMP` to `self.COLD_WARNING_TEMP`
- Line 154: Change `HEATSTROKE_WARNING_TEMP` to `self.HEATSTROKE_WARNING_TEMP`
- Line 164: Change `COLD_WARNING_TEMP` to `self.COLD_WARNING_TEMP`

### 5. src/utils/validators/weather_specific/weather_condition_validator.py

**Current Code (line 8):**
```python
from src.config.weather_constants import SUNNY_WEATHER_KEYWORDS
```

**Updated Code:**
```python
from src.config.config import get_weather_constants
```

**In the `__init__` method (line 18):**
```python
def __init__(self, config_path: Optional[str] = None):
    """
    初期化
    
    Args:
        config_path: 禁止ワード設定ファイルのパス。Noneの場合はデフォルトパスを使用
    """
    # Add these lines:
    weather_constants = get_weather_constants()
    self.SUNNY_WEATHER_KEYWORDS = weather_constants.SUNNY_WEATHER_KEYWORDS
    
    self.weather_forbidden_words = self._load_forbidden_words(config_path)
```

**Update usage (line 37):**
```python
# Change from:
if any(sunny_word in weather_desc_lower for sunny_word in SUNNY_WEATHER_KEYWORDS):
# To:
if any(sunny_word in weather_desc_lower for sunny_word in self.SUNNY_WEATHER_KEYWORDS):
```

### 6. src/utils/validators/weather_specific/consistency_validator.py

**Current Code (line 7):**
```python
from src.config.weather_constants import SUNNY_WEATHER_KEYWORDS
```

**Updated Code:**
```python
from src.config.config import get_weather_constants
```

**In the `__init__` method (line 16):**
```python
def __init__(self):
    # Add these lines:
    weather_constants = get_weather_constants()
    self.SUNNY_WEATHER_KEYWORDS = weather_constants.SUNNY_WEATHER_KEYWORDS
    
    # Existing code:
    self.contradictory_pairs = {
        # ...
    }
```

**Update usage (line 43):**
```python
# Change from:
if any(sunny_word in weather_desc for sunny_word in SUNNY_WEATHER_KEYWORDS):
# To:
if any(sunny_word in weather_desc for sunny_word in self.SUNNY_WEATHER_KEYWORDS):
```

## Testing the Changes

After making these updates, you can test that the constants are being loaded correctly:

```python
# Test script
from src.config.config import get_weather_constants

# Get constants
constants = get_weather_constants()

# Print some values
print(f"WEATHER_CHANGE_THRESHOLD: {constants.WEATHER_CHANGE_THRESHOLD}")
print(f"HEATSTROKE_WARNING_TEMP: {constants.HEATSTROKE_WARNING_TEMP}")
print(f"SUNNY_WEATHER_KEYWORDS: {constants.SUNNY_WEATHER_KEYWORDS}")

# Test with environment variable override
import os
os.environ['WEATHER_CHANGE_THRESHOLD'] = '3'
constants = get_weather_constants()
print(f"WEATHER_CHANGE_THRESHOLD (after env override): {constants.WEATHER_CHANGE_THRESHOLD}")
```

## Benefits of This Approach

1. **Configurable**: Constants can be overridden via environment variables
2. **Centralized**: All weather constants are managed in one place
3. **Type-safe**: Using SimpleNamespace provides attribute access with IDE support
4. **Backward compatible**: Usage patterns in the code remain similar
5. **Testable**: Easy to mock or override constants for testing
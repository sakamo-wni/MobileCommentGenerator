# 環境変数プレフィックス統一ガイド

## 移行計画

### 現在の環境変数

#### Weather関連
- `WXTECH_API_KEY` → `APP_WXTECH_API_KEY`
- `DEFAULT_WEATHER_LOCATION` → `APP_DEFAULT_WEATHER_LOCATION`
- `WEATHER_FORECAST_HOURS` → `APP_WEATHER_FORECAST_HOURS`
- `WEATHER_FORECAST_HOURS_AHEAD` → `APP_WEATHER_FORECAST_HOURS_AHEAD`
- `WEATHER_API_TIMEOUT` → `APP_WEATHER_API_TIMEOUT`
- `WEATHER_API_MAX_RETRIES` → `APP_WEATHER_API_MAX_RETRIES`
- `WEATHER_API_RATE_LIMIT_DELAY` → `APP_WEATHER_API_RATE_LIMIT_DELAY`
- `WEATHER_CACHE_TTL` → `APP_WEATHER_CACHE_TTL`
- `WEATHER_ENABLE_CACHING` → `APP_WEATHER_ENABLE_CACHING`
- `FORECAST_CACHE_RETENTION_DAYS` → `APP_FORECAST_CACHE_RETENTION_DAYS`
- `TEMP_DIFF_THRESHOLD_PREVIOUS_DAY` → `APP_TEMP_DIFF_THRESHOLD_PREVIOUS_DAY`
- `TEMP_DIFF_THRESHOLD_12HOURS` → `APP_TEMP_DIFF_THRESHOLD_12HOURS`
- `DAILY_TEMP_RANGE_THRESHOLD_LARGE` → `APP_DAILY_TEMP_RANGE_THRESHOLD_LARGE`
- `DAILY_TEMP_RANGE_THRESHOLD_MEDIUM` → `APP_DAILY_TEMP_RANGE_THRESHOLD_MEDIUM`
- `TEMP_THRESHOLD_HOT` → `APP_TEMP_THRESHOLD_HOT`
- `TEMP_THRESHOLD_WARM` → `APP_TEMP_THRESHOLD_WARM`
- `TEMP_THRESHOLD_COOL` → `APP_TEMP_THRESHOLD_COOL`
- `TEMP_THRESHOLD_COLD` → `APP_TEMP_THRESHOLD_COLD`

#### LangGraph関連
- `LANGGRAPH_ENABLE_WEATHER` → `APP_LANGGRAPH_ENABLE_WEATHER`
- `LANGGRAPH_AUTO_LOCATION` → `APP_LANGGRAPH_AUTO_LOCATION`
- `LANGGRAPH_WEATHER_CONTEXT_WINDOW` → `APP_LANGGRAPH_WEATHER_CONTEXT_WINDOW`
- `LANGGRAPH_MIN_CONFIDENCE` → `APP_LANGGRAPH_MIN_CONFIDENCE`

#### アプリケーション全般
- `DEBUG` → `APP_DEBUG`
- `LOG_LEVEL` → `APP_LOG_LEVEL`

## 移行戦略

1. **後方互換性の維持**: 移行期間中は両方の環境変数名をサポート
2. **段階的移行**: 
   - Phase 1: 新しい環境変数名を優先的に読み込み、存在しない場合は古い名前にフォールバック
   - Phase 2: 非推奨警告の追加
   - Phase 3: 古い環境変数名のサポート終了

## 実装例

```python
def get_env_with_fallback(new_name: str, old_name: str, default: str = "") -> str:
    """新旧両方の環境変数名をサポート"""
    value = os.getenv(new_name)
    if value is None:
        value = os.getenv(old_name, default)
        if value != default:
            import warnings
            warnings.warn(
                f"環境変数 '{old_name}' は非推奨です。'{new_name}' を使用してください。",
                DeprecationWarning,
                stacklevel=2
            )
    return value
```
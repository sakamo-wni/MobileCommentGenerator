# weather_data.py 分割に伴う移行ガイド

このガイドでは、`weather_data.py`の分割に伴う変更点と移行方法について説明します。

## 概要

巨大な`weather_data.py`（417行）を以下の4つのモジュールに分割しました：

- `weather_enums.py` - 列挙型（WeatherCondition, WindDirection）
- `weather_models.py` - コアデータモデル（WeatherForecast）
- `weather_collection.py` - コレクション管理（WeatherForecastCollection）
- `weather_analysis.py` - ビジネスロジック（分析関数）

## 後方互換性

既存のコードとの互換性を保つため、`weather_data.py`は互換性レイヤーとして残されています。
既存のインポートは変更不要です：

```python
# 既存のコード（変更不要）
from src.data.weather_data import WeatherForecast, WeatherCondition
```

## 破壊的変更

### 1. location → location_id

`WeatherForecast`の`location`フィールドが`location_id`に変更されました。

#### 移行前
```python
forecast = WeatherForecast(
    location="tokyo",  # 旧フィールド名
    datetime=now,
    temperature=25.0,
    # ...
)
print(forecast.location)
```

#### 移行後
```python
forecast = WeatherForecast(
    location_id="tokyo",  # 新フィールド名
    datetime=now,
    temperature=25.0,
    # ...
)
print(forecast.location_id)
```

#### 互換性サポート

一時的に`location`プロパティを使用できますが、DeprecationWarningが表示されます：

```python
# 非推奨だが動作する
print(forecast.location)  # DeprecationWarning: Use 'location_id' instead
```

### 2. 削除されたフィールド

以下のフィールドは削除されましたが、プロパティとして後方互換性を提供しています：

- `weather_code` → `weather_condition`を使用してください
- `wind_direction_degrees` → `wind_direction`列挙型を使用してください

```python
# 非推奨だが動作する
code = forecast.weather_code  # DeprecationWarning
degrees = forecast.wind_direction_degrees  # DeprecationWarning

# 推奨
condition = forecast.weather_condition
direction = forecast.wind_direction
```

## 新機能

### 1. WindDirectionの16方位対応

```python
from src.data.weather_enums import WindDirection

# 16方位すべてをサポート
wind = WindDirection.NORTH_NORTHEAST  # 北北東
wind = WindDirection.from_degrees(22.5)  # 角度から変換
```

### 2. 新しいフィールド

`WeatherForecast`に以下のフィールドが追加されました：

- `feels_like` - 体感温度
- `pressure` - 気圧
- `cloud_coverage` - 雲量
- `visibility` - 視程
- `uv_index` - UV指数

### 3. 型安全な分析結果

```python
from src.data.weather_analysis import analyze_weather_trend, WeatherTrendResult

result: WeatherTrendResult = analyze_weather_trend(collection)
# TypedDictにより型安全
print(result["temperature_trend"])  # "rising" | "falling" | "stable"
```

## 段階的移行の推奨手順

1. **ステップ1**: 既存コードはそのまま動作確認
   - `weather_data.py`経由のインポートは引き続き機能します

2. **ステップ2**: DeprecationWarningの確認
   ```bash
   python -W default::DeprecationWarning your_script.py
   ```

3. **ステップ3**: 新しいインポートパスへの更新
   ```python
   # 旧
   from src.data.weather_data import WeatherCondition
   
   # 新（推奨）
   from src.data.weather_enums import WeatherCondition
   ```

4. **ステップ4**: フィールド名の更新
   - `location` → `location_id`
   - `weather_code` → `weather_condition`の使用

5. **ステップ5**: 新機能の活用
   - 16方位の風向き
   - 体感温度などの新フィールド
   - 型安全な分析関数

## トラブルシューティング

### ImportError が発生する場合

```python
# エラーが出る場合
from src.data.weather_data import analyze_weather_trend  # 分析関数は移動

# 正しいインポート
from src.data.weather_analysis import analyze_weather_trend
```

### 型チェックエラー

```python
# mypy/pylanceでエラーになる場合
from src.data.weather_analysis import WeatherTrendResult

# 明示的な型注釈を使用
result: WeatherTrendResult = analyze_weather_trend(collection)
```

## サポート

質問や問題がある場合は、GitHubのIssueを作成してください。
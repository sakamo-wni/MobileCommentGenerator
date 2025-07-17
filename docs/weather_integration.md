# 天気予報統合機能 (Issue #3)

このドキュメントでは、Issue #3で実装された天気予報統合機能の概要と使用方法を説明します。

## 概要

この機能は、Weathernews WxTech APIを使用して天気予報データを取得し、LangGraphのノードとして統合することで、コメント生成システムに天気情報を組み込むことができます。

## 主な機能

### 1. 天気データクラス (`src/data/weather_data.py`)
- **WeatherForecast**: 単一の天気予報データを管理
- **WeatherForecastCollection**: 複数の天気予報データを管理
- **WeatherCondition/WindDirection**: 天気状況と風向きの列挙型

### 2. 地点管理 (`src/data/location_manager.py`)
- **Location**: 地点情報（名前、都道府県、緯度経度）を管理
- **LocationManager**: 日本の主要都市データベースと地点検索機能

### 3. WxTech APIクライアント (`src/apis/wxtech_client.py`)
- **WxTechAPIClient**: WxTech APIとの通信を担当
- リトライ機能、レート制限対応、エラーハンドリング
- 同期・非同期両対応

### 4. LangGraphノード (`src/nodes/weather_forecast_node.py`)
- **WeatherForecastNode**: LangGraphノードとして天気予報を統合
- 天気概要生成、推奨事項提案
- 会話への天気情報統合

### 5. 設定管理 (`src/config/weather_config.py`)
- 環境変数による設定管理
- 設定検証機能

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env` ファイルを作成し、以下の設定を追加：

```env
# 必須設定
WXTECH_API_KEY=your_wxtech_api_key_here

# オプション設定（デフォルト値あり）
DEFAULT_WEATHER_LOCATION=東京
WEATHER_FORECAST_HOURS=24
WEATHER_API_TIMEOUT=30
WEATHER_API_MAX_RETRIES=3
WEATHER_API_RATE_LIMIT_DELAY=0.1
WEATHER_CACHE_TTL=300
WEATHER_ENABLE_CACHING=true

# LangGraph統合設定
LANGGRAPH_ENABLE_WEATHER=true
LANGGRAPH_AUTO_LOCATION=false
LANGGRAPH_WEATHER_CONTEXT_WINDOW=24
LANGGRAPH_MIN_CONFIDENCE=0.7

# 一般設定
DEBUG=false
LOG_LEVEL=INFO
```

## 使用例

### 1. 基本的な天気予報取得

```python
import asyncio
from src.apis.wxtech_client import WxTechAPIClient

async def basic_weather_example():
    api_key = "your_api_key"
    
    with WxTechAPIClient(api_key) as client:
        # 東京の天気予報を取得
        forecast_collection = client.get_forecast(35.6762, 139.6503)
        
        print(f"地点: {forecast_collection.location_id}")
        
        current_forecast = forecast_collection.get_current_forecast()
        if current_forecast:
            print(f"現在の天気: {current_forecast.weather_description}")
            print(f"気温: {current_forecast.temperature}°C")
            print(f"降水量: {current_forecast.precipitation}mm")

# 実行
asyncio.run(basic_weather_example())
```

### 2. 地点名による天気予報取得

```python
from src.apis.wxtech_client import WxTechAPIClient
from src.data.location_manager import get_location_manager

def location_based_weather_example():
    api_key = "your_api_key"
    location_manager = get_location_manager()
    
    # 地点検索
    osaka = location_manager.get_location("大阪")
    
    with WxTechAPIClient(api_key) as client:
        if osaka:
            forecast_collection = client.get_forecast_by_location(osaka)
            print(f"{osaka.name}の天気予報を取得しました")
            
            # 日次サマリー
            summary = forecast_collection.get_daily_summary()
            print(f"最高気温: {summary['max_temperature']}°C")
            print(f"最低気温: {summary['min_temperature']}°C")
            print(f"総降水量: {summary['total_precipitation']}mm")
```

### 3. LangGraphノードとしての使用

```python
import asyncio
from src.nodes.weather_forecast_node import get_weather_forecast_for_location

async def langgraph_integration_example():
    api_key = "your_api_key"
    
    # 天気予報データを取得
    result = await get_weather_forecast_for_location(
        location="東京",
        api_key=api_key,
        forecast_hours=12  # 12時間分の予報
    )
    
    if result.get('error_message'):
        print(f"エラー: {result['error_message']}")
        return
    
    # 天気概要を表示
    weather_summary = result['weather_summary']
    current_weather = weather_summary['current_weather']
    recommendations = weather_summary['recommendations']
    
    print(f"現在の天気: {current_weather['description']}")
    print(f"快適度: {current_weather['comfort_level']}")
    
    if recommendations:
        print("推奨事項:")
        for rec in recommendations:
            print(f"- {rec}")

# 実行
asyncio.run(langgraph_integration_example())
```

### 4. 会話への天気情報統合

```python
import asyncio
from langchain_core.messages import HumanMessage
from src.nodes.weather_forecast_node import integrate_weather_into_conversation

async def conversation_integration_example():
    api_key = "your_api_key"
    
    # 初期メッセージ
    messages = [
        HumanMessage(content="今日の予定について相談したいです")
    ]
    
    # 天気情報を統合
    enhanced_messages = await integrate_weather_into_conversation(
        messages=messages,
        location="東京",
        api_key=api_key
    )
    
    # 統合後のメッセージを表示
    for i, message in enumerate(enhanced_messages):
        print(f"メッセージ {i+1}: {message.content[:100]}...")

# 実行
asyncio.run(conversation_integration_example())
```

### 5. カスタム地点の追加

```python
from src.data.location_manager import get_location_manager, Location

def custom_location_example():
    location_manager = get_location_manager()
    
    # カスタム地点を追加
    custom_location = Location(
        name="カスタム地点",
        prefecture="カスタム県",
        latitude=36.0,
        longitude=140.0,
        elevation=100.0
    )
    
    location_manager.add_location(custom_location)
    
    # 追加した地点を検索
    found = location_manager.get_location("カスタム地点")
    if found:
        print(f"地点追加成功: {found.name} ({found.latitude}, {found.longitude})")
    
    # 最寄りの地点を検索
    nearest = location_manager.get_nearest_location(36.1, 140.1, max_distance_km=20)
    if nearest:
        print(f"最寄りの地点: {nearest.name}")
```

## 高度な使用例

### 1. 天気情報のキャッシュ処理

```python
import asyncio
import time
from src.apis.wxtech_client import WxTechAPIClient

class WeatherCache:
    def __init__(self, ttl_seconds=300):  # 5分間キャッシュ
        self.cache = {}
        self.ttl = ttl_seconds
    
    def _is_expired(self, timestamp):
        return time.time() - timestamp > self.ttl
    
    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if not self._is_expired(timestamp):
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, time.time())

# グローバルキャッシュ
weather_cache = WeatherCache()

async def cached_weather_example():
    api_key = "your_api_key"
    location = "東京"
    
    # キャッシュから取得を試行
    cached_data = weather_cache.get(location)
    if cached_data:
        print("キャッシュからデータを取得")
        return cached_data
    
    # APIから新しいデータを取得
    print("APIからデータを取得")
    result = await get_weather_forecast_for_location(location, api_key)
    
    if not result.get('error_message'):
        weather_cache.set(location, result)
    
    return result
```

### 2. 複数地点の並列処理

```python
import asyncio
from src.nodes.weather_forecast_node import get_weather_forecast_for_location

async def parallel_weather_example():
    api_key = "your_api_key"
    locations = ["東京", "大阪", "福岡", "札幌"]
    
    # 並列でデータ取得
    tasks = [
        get_weather_forecast_for_location(location, api_key)
        for location in locations
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for location, result in zip(locations, results):
        if isinstance(result, Exception):
            print(f"{location}: エラー - {str(result)}")
        elif result.get('error_message'):
            print(f"{location}: {result['error_message']}")
        else:
            current = result['weather_summary']['current_weather']
            print(f"{location}: {current['description']}, {current['temperature']}°C")

# 実行
asyncio.run(parallel_weather_example())
```

## エラーハンドリング

### 一般的なエラーと対処法

1. **APIキーエラー**
   ```python
   try:
       forecast = client.get_forecast(35.6762, 139.6503)
   except WxTechAPIError as e:
       if "認証エラー" in str(e):
           print("APIキーを確認してください")
       elif "レート制限" in str(e):
           print("リクエスト頻度を下げてください")
   ```

2. **座標エラー**
   ```python
   try:
       forecast = client.get_forecast(lat, lon)
   except ValueError as e:
       print(f"座標が無効です: {e}")
   ```

3. **地点不明エラー**
   ```python
   location = location_manager.get_location("不明な地点")
   if not location:
       print("地点が見つかりません")
       # 検索候補を表示
       suggestions = location_manager.search_locations("部分的な名前")
       if suggestions:
           print("候補:", [loc.name for loc in suggestions[:5]])
   ```

## パフォーマンス考慮事項

1. **レート制限**: デフォルトで0.1秒の遅延が設定されています
2. **タイムアウト**: API リクエストは30秒でタイムアウトします
3. **リトライ**: 失敗時は最大3回リトライされます
4. **キャッシュ**: 頻繁なアクセスにはキャッシュ機能の実装を推奨

## テスト

```bash
# 全テスト実行
python -m pytest tests/

# 個別テスト実行
python -m pytest tests/test_weather_data.py
python -m pytest tests/test_location_manager.py
python -m pytest tests/test_wxtech_client.py

# カバレッジ付きテスト
python -m pytest tests/ --cov=src --cov-report=html
```

## トラブルシューティング

### よくある問題

1. **環境変数が読み込まれない**
   - `.env` ファイルがプロジェクトルートにあることを確認
   - `python-dotenv` がインストールされていることを確認

2. **APIレスポンスが空**
   - 座標が日本国内の有効な範囲内にあることを確認
   - APIキーの権限を確認

3. **パフォーマンスが遅い**
   - `rate_limit_delay` を調整
   - キャッシュ機能の実装を検討

## 今後の拡張可能性

1. **他の気象APIとの統合**
2. **予報精度の向上**
3. **地域特化型の推奨機能**
4. **時系列データの分析機能**
5. **気象警報との連携**

## 関連ファイル

- `src/data/weather_data.py` - 天気データクラス
- `src/data/location_manager.py` - 地点管理
- `src/apis/wxtech_client.py` - API クライアント
- `src/nodes/weather_forecast_node.py` - LangGraph ノード
- `src/config/weather_config.py` - 設定管理
- `tests/` - テストファイル群

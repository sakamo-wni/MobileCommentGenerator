# キャッシュ戦略の最適化

## 概要

本ドキュメントでは、MobileCommentGeneratorにおけるキャッシュ戦略の最適化について説明します。

## 実装内容

### 1. 統一キャッシュマネージャー (`src/utils/cache_manager.py`)

アプリケーション全体のキャッシュを一元管理するマネージャーを実装しました。

#### 主な機能

- **シングルトンパターン**: アプリケーション全体で単一のインスタンスを共有
- **メモリプレッシャー対応**: システムメモリが逼迫した際の自動エビクション
- **統計情報追跡**: キャッシュヒット率、メモリ使用量などの詳細な統計
- **キャッシュウォーミング**: 事前にデータを投入する機能
- **効率スコア計算**: キャッシュの総合的なパフォーマンス評価

#### 使用例

```python
from src.utils.cache_manager import get_cache_manager, get_cache

# キャッシュマネージャーの取得
manager = get_cache_manager()

# 特定のキャッシュを取得
cache = get_cache("api_responses")

# データの保存と取得
cache.set("key", "value", ttl=300)
value = cache.get("key")

# 統計情報の取得
stats = manager.get_stats_summary()
print(f"全体ヒット率: {stats['overall_hit_rate']:.2%}")
```

### 2. 改善されたキャッシュデコレーター (`src/utils/cache_decorators.py`)

より柔軟なキャッシュ制御を可能にするデコレーターを実装しました。

#### smart_cache デコレーター

```python
from src.utils.cache_decorators import smart_cache

@smart_cache(
    cache_name="weather_api",
    ttl=600,
    condition=lambda result: result is not None
)
def get_weather_data(location: str) -> dict:
    # API呼び出し
    return fetch_from_api(location)

# キャッシュをバイパスしたい場合
data = get_weather_data("東京", _bypass_cache=True)
```

#### 主な特徴

- **条件付きキャッシュ**: 結果に基づいてキャッシュするかを決定
- **キャッシュバイパス**: デバッグや強制更新時に使用
- **非同期関数サポート**: async/await関数でも同じデコレーターを使用可能

### 3. キャッシュ監視UI (`src/ui/components/cache_monitor.py`)

Streamlitベースのキャッシュ監視コンポーネントを実装しました。

#### 表示内容

- **サマリー統計**: 総キャッシュ数、メモリ使用量、ヒット率など
- **詳細テーブル**: 各キャッシュの個別統計
- **パフォーマンスグラフ**: 時系列でのヒット率、メモリ使用量の推移
- **制御パネル**: キャッシュのクリア機能

### 4. 改善されたAPIクライアント (`src/apis/wxtech/cached_client_v2.py`)

統一キャッシュマネージャーを使用するAPIクライアントを実装しました。

```python
from src.apis.wxtech.cached_client_v2 import CachedWxTechAPIClientV2

# クライアントの作成
client = CachedWxTechAPIClientV2(api_key="...")

# 天気予報の取得（自動的にキャッシュされる）
forecast = client.get_forecast(lat=35.6895, lon=139.6917)

# キャッシュのウォーミング
locations = [location1, location2, location3]
client.warm_cache_for_locations(locations)
```

## デフォルトキャッシュ設定

以下のキャッシュがデフォルトで作成されます：

| キャッシュ名 | TTL | 最大サイズ | 最大メモリ | 用途 |
|------------|-----|-----------|-----------|------|
| api_responses | 5分 | 500 | 50MB | API応答の汎用キャッシュ |
| comments | 1時間 | 1000 | 30MB | 生成されたコメント |
| weather_forecasts | 10分 | 200 | 20MB | 天気予報データ |
| wxtech_api | 10分 | 200 | 20MB | WxTech API専用 |

## パフォーマンス改善

### メモリ使用量の削減

- **LRUエビクション**: 最も使用されていないエントリを自動削除
- **メモリプレッシャー対応**: システムメモリが80%を超えると自動的にエントリを削減
- **TTLによる自動削除**: 期限切れエントリの定期的なクリーンアップ

### レスポンス時間の改善

- **高速なキー検索**: ハッシュベースのキー管理
- **スレッドセーフ**: 並行アクセスでも安全に動作
- **キャッシュウォーミング**: 事前にデータを投入可能

## 設定のカスタマイズ

### 環境変数

```bash
# WxTech APIキャッシュのTTL（秒）
export WXTECH_CACHE_TTL=600

# キャッシュサイズ
export WXTECH_CACHE_SIZE=200
```

### プログラムでの設定

```python
from src.utils.cache_manager import CacheConfig, get_cache_manager

# カスタム設定でキャッシュを作成
config = CacheConfig(
    default_ttl_seconds=3600,
    max_size=5000,
    max_memory_mb=100,
    enable_memory_pressure_handling=True,
    memory_pressure_threshold=0.7
)

manager = get_cache_manager()
manager.create_cache("custom_cache", config)
```

## 監視とデバッグ

### ログ出力

キャッシュ操作は適切なログレベルで記録されます：

```python
import logging

# デバッグログを有効化
logging.getLogger("src.utils.cache_manager").setLevel(logging.DEBUG)
```

### 統計情報の取得

```python
# プログラムから統計を取得
stats = manager.get_stats_summary()

# 個別キャッシュの詳細統計
cache_stats = manager.get_all_stats()["api_responses"]
print(f"ヒット率: {cache_stats.basic_stats['hit_rate']:.2%}")
print(f"効率スコア: {cache_stats.cache_efficiency_score:.2f}")
```

### StreamlitUIでの監視

```python
from src.ui.components.cache_monitor import display_cache_monitor

# Streamlitアプリ内で
display_cache_monitor(show_details=True)
```

## ベストプラクティス

1. **適切なTTLの設定**
   - 頻繁に変化するデータ: 1-5分
   - 比較的安定したデータ: 10-30分
   - ほとんど変化しないデータ: 1時間以上

2. **キャッシュキーの設計**
   - 一意性を保証
   - 可能な限り短く
   - デバッグしやすい形式

3. **エラーハンドリング**
   - エラーレスポンスはキャッシュしない
   - 部分的な結果もキャッシュ対象外に

4. **メモリ管理**
   - 定期的な統計情報の確認
   - 必要に応じてキャッシュサイズの調整
   - メモリプレッシャー閾値の適切な設定

## 今後の改善案

1. **Redis/Memcached統合**: 分散キャッシュのサポート
2. **キャッシュの永続化**: ディスクへの保存機能
3. **より高度な統計**: P99レイテンシ、キャッシュミスコストなど
4. **自動チューニング**: 使用パターンに基づく自動最適化
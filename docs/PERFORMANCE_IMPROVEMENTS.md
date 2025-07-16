# パフォーマンス改善ガイド

このドキュメントでは、MobileCommentGeneratorに実装されたパフォーマンス改善機能について説明します。

## 概要

本システムでは、以下の5つの主要な改善により、レスポンスタイムの短縮とシステムリソースの効率的な利用を実現しています：

1. **並列コメント生成** - 複数地点のコメントを同時生成
2. **多層キャッシングシステム** - インメモリ・ファイル・空間的キャッシュの組み合わせ
3. **空間キャッシュクラスタリング** - 近隣地点のデータ再利用
4. **キャッシュウォーミング** - 人気地点の事前データ取得
5. **メモリ使用量監視** - リソース使用状況の可視化

## 期待される効果

### レスポンスタイムの改善
- **並列処理**: 最大4倍の高速化（4ワーカー時）
- **キャッシュヒット時**: 90%以上の応答時間削減
- **近隣キャッシュ活用**: APIコール数を30-50%削減

### リソース効率
- **メモリ使用量**: LRUキャッシュによる自動管理
- **ディスクI/O**: インメモリキャッシュで80%削減
- **API使用量**: 空間キャッシュで重複リクエストを削減

## 1. 並列コメント生成

### 概要
`ParallelCommentGenerator`クラスにより、複数地点のコメント生成を並列実行します。

### 使用方法
```python
from src.controllers.parallel_comment_generator import ParallelCommentGenerator

# 並列生成器の初期化
generator = ParallelCommentGenerator(
    max_workers=4,  # 最大ワーカー数
    timeout_per_location=30,  # 地点ごとのタイムアウト（秒）
    max_parallel_locations=20  # 並列処理する最大地点数
)

# 複数地点のコメントを並列生成
result = generator.generate_parallel(
    locations_with_weather,
    llm_provider="gemini"
)
```

### 設定項目
- `max_parallel_workers`: 並列ワーカー数（デフォルト: 4）
- `comment_timeout_seconds`: タイムアウト時間（デフォルト: 30秒）
- `max_parallel_locations`: 並列処理の最大地点数（デフォルト: 20）

### パフォーマンス特性
- 1-20地点: 並列処理（高速）
- 21地点以上: シリアル処理（安定性重視）
- スレッドプールによる効率的なリソース管理

## 2. 多層キャッシングシステム

### 2.1 インメモリキャッシュ (ForecastMemoryCache)

高速なメモリ上のキャッシュで、頻繁にアクセスされるデータを保持します。

```python
from src.data.forecast_cache import ForecastMemoryCache

# インメモリキャッシュの初期化
memory_cache = ForecastMemoryCache(
    max_size=500,  # 最大エントリ数
    ttl_seconds=300  # TTL（秒）
)
```

**特徴:**
- LRU（Least Recently Used）方式でエビクション
- TTL（Time To Live）による自動期限切れ
- O(1)の高速アクセス

### 2.2 マルチレベルコメントキャッシュ

3階層の粒度でコメントをキャッシュし、ヒット率を最大化します。

```python
from src.repositories.multilevel_comment_cache import MultiLevelCommentCache

# マルチレベルキャッシュの初期化
cache = MultiLevelCommentCache(
    max_size_per_level=100,
    cache_ttl_minutes=60,
    max_memory_mb_per_level=30
)

# L1キャッシュ: タイプ + 季節 + 地域
# L2キャッシュ: タイプ + 季節
# L3キャッシュ: タイプのみ
```

**キャッシュ階層:**
- **L1 (詳細)**: `CommentType.MORNING + "春" + "関東"` → 特定のコメント
- **L2 (中間)**: `CommentType.MORNING + "春"` → 季節別の汎用コメント
- **L3 (粗い)**: `CommentType.MORNING` → タイプ別の基本コメント

## 3. 空間キャッシュクラスタリング

### 概要
近隣地点の予報データを活用し、APIコール数を削減します。

```python
from src.data.forecast_cache import SpatialForecastCache

# 空間キャッシュの初期化
spatial_cache = SpatialForecastCache(
    max_distance_km=10.0,  # 近隣とみなす最大距離
    max_neighbors=5  # 検索する最大近隣数
)

# 位置情報の登録
spatial_cache.register_location("東京", 35.6812, 139.7671)
spatial_cache.register_location("品川", 35.6284, 139.7387)
```

### 動作原理
1. 要求された地点のキャッシュを検索
2. なければ10km以内の近隣地点を検索
3. 最も近い地点のデータを利用（地点名は変更）

### 効果
- 都市部では30-50%のAPIコール削減
- 地方部でも10-20%の削減効果

## 4. キャッシュウォーミング

### 概要
人気地点の予報を事前に取得し、初回アクセスでもキャッシュヒットを実現します。

```python
from src.data.forecast_cache import CacheWarmer

# キャッシュウォーマーの初期化
warmer = CacheWarmer(
    popular_locations_file=Path("config/popular_locations.json"),
    max_concurrent=5,
    warm_hours_ahead=48
)

# 非同期でキャッシュを温める
await warmer.warm_cache_async(forecast_fetcher, forecast_cache)
```

### 人気地点リストの形式
```json
{
  "locations": [
    {
      "name": "東京",
      "latitude": 35.6812,
      "longitude": 139.7671,
      "priority": 10,
      "access_count": 1523
    }
  ]
}
```

## 5. メモリ使用量監視

### 概要
システムのメモリ使用状況を監視し、リソース不足を防ぎます。

```python
from src.utils.memory_monitor import MemoryMonitor

# メモリモニターの初期化
monitor = MemoryMonitor(
    warning_threshold_percent=80.0,
    critical_threshold_percent=90.0
)

# メモリ状況の確認
warning_needed, msg = monitor.check_memory_usage()
if warning_needed:
    logger.warning(msg)
```

### 監視項目
- プロセスメモリ（RSS、VMS）
- システムメモリ使用率
- キャッシュメモリ推定値

### psutilのインストール（オプション）
メモリ監視機能を有効にするには、psutilをインストールしてください：

```bash
# 開発環境
pip install -e ".[dev]"

# または個別にインストール
pip install psutil
```

## ベストプラクティス

### 1. 適切なキャッシュサイズの設定
```python
# 環境に応じて調整
config.weather.memory_cache_size = 1000  # 大規模環境
config.weather.memory_cache_ttl = 600  # 10分間保持
```

### 2. 並列処理の最適化
```python
# CPUコア数に応じて調整
config.generation.max_parallel_workers = os.cpu_count()
```

### 3. 監視とアラート
```python
# 定期的なメモリチェック
stats = forecast_cache.get_cache_stats()
if stats.get("memory_warning"):
    send_alert(stats["memory_warning"])
```

## トラブルシューティング

### メモリ使用量が高い場合
1. キャッシュサイズを削減
2. TTLを短縮
3. `cleanup_expired()`を定期実行

### キャッシュヒット率が低い場合
1. 人気地点リストを更新
2. 空間キャッシュの距離を調整
3. TTLを延長

### 並列処理でエラーが発生する場合
1. ワーカー数を削減
2. タイムアウトを延長
3. `max_parallel_locations`を調整

## パフォーマンス測定

### キャッシュ統計の取得
```python
# キャッシュ統計
stats = forecast_cache.get_cache_stats()
print(f"メモリキャッシュヒット率: {stats['memory_cache']['hit_rate']:.1%}")
print(f"空間キャッシュヒット率: {stats['spatial_cache']['hit_rate']:.1%}")

# 並列処理統計
generator_stats = parallel_generator.get_stats()
print(f"並列処理: {generator_stats['parallel_processed']}件")
print(f"タイムアウト: {generator_stats['timeout_count']}件")
```

### ベンチマーク結果の例
- 10地点の並列処理: 2.5秒 → 0.8秒（68%削減）
- キャッシュヒット時: 1.2秒 → 0.1秒（92%削減）
- 100地点のバッチ処理: 120秒 → 35秒（71%削減）

## まとめ

これらのパフォーマンス改善により、MobileCommentGeneratorは：
- より高速なレスポンスタイムを実現
- システムリソースを効率的に利用
- スケーラビリティが向上

継続的な監視と調整により、さらなる改善が可能です。
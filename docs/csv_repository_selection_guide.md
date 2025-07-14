# CSVリポジトリ実装ガイド

## 概要

MobileCommentGeneratorでは、LazyCommentRepository（遅延読み込み実装）を使用してCSVファイルからコメントデータを管理しています。この実装により、メモリ効率的かつ高速な起動を実現しています。

## LazyCommentRepositoryの特徴

### メリット
- ✅ **メモリ効率的**: 必要なファイルのみを読み込み
- ✅ **高速な起動**: 初期化時にファイルを読み込まない
- ✅ **大規模データセット対応**: メモリ制限のある環境でも動作
- ✅ **キャッシュ機能**: 一度読み込んだデータは高速アクセス可能
- ✅ **並列読み込み対応**: 複数ファイルの同時読み込みが可能

### 動作原理
1. 初期化時はファイルの存在確認のみ
2. データアクセス時に必要なファイルを読み込み
3. 読み込んだデータはメモリにキャッシュ
4. TTL（Time To Live）によりキャッシュを自動管理

## 使用方法

### 基本的な使用例

```python
from src.repositories.lazy_comment_repository import LazyCommentRepository

# リポジトリの初期化
repository = LazyCommentRepository()

# 季節ごとのコメント取得
spring_comments = repository.get_comments_by_season("春")

# 天気コメントのみ取得
weather_comments = repository.get_weather_comments_by_season("夏")

# アドバイスコメントのみ取得
advice_comments = repository.get_advice_by_season("秋")

# キーワード検索
search_results = repository.search_comments(
    keyword="晴れ",
    season="春",
    comment_type=CommentType.WEATHER_COMMENT
)
```

### 高度な使用方法

```python
# 事前読み込み（パフォーマンス最適化）
repository.preload_season("春")  # 春のデータを事前に読み込む

# キャッシュのクリア
repository.clear_cache()

# 統計情報の取得
stats = repository.get_statistics()
print(f"読み込まれたファイル数: {stats['loaded_files']}")
print(f"キャッシュヒット率: {stats['cache_stats']['hit_rate']:.1%}")
```

## パフォーマンス特性

### メモリ使用量
- 初期化時: 最小限（ファイルリストのみ）
- データアクセス後: アクセスしたファイルのみメモリに保持

### レスポンス時間
- 初回アクセス: ファイル読み込みのため若干遅い
- 2回目以降: キャッシュから高速アクセス

## 設定オプション

### 環境変数
環境変数による設定は不要です。LazyCommentRepositoryが常に使用されます。

### 初期化パラメータ

```python
repository = LazyCommentRepository(
    output_dir="output",           # CSVファイルのディレクトリ
    cache_ttl_minutes=60,         # キャッシュの有効期限（分）
    enable_parallel_loading=True   # 並列読み込みの有効化
)
```

## ベストプラクティス

### 1. 効率的なデータアクセス
```python
# 良い例: 必要な季節のみアクセス
spring_weather = repository.get_weather_comments_by_season("春")

# 避けるべき例: 全季節を順番にアクセス（必要ない場合）
all_comments = []
for season in ["春", "夏", "秋", "冬"]:
    all_comments.extend(repository.get_comments_by_season(season))
```

### 2. 事前読み込みの活用
```python
# バッチ処理の場合は事前読み込みが有効
seasons_to_process = ["春", "夏"]
for season in seasons_to_process:
    repository.preload_season(season)

# その後の処理は高速
for season in seasons_to_process:
    comments = repository.get_comments_by_season(season)
    # 処理...
```

### 3. エラーハンドリング
```python
try:
    comments = repository.get_comments_by_season("春")
except FileNotFoundError:
    print("CSVファイルが見つかりません。output/ディレクトリを確認してください。")
except Exception as e:
    print(f"エラーが発生しました: {e}")
```

## トラブルシューティング

### Q: CSVファイルが見つからないエラー
**解決策**:
1. `output/`ディレクトリにCSVファイルが存在することを確認
2. ファイル名の形式が正しいことを確認（例: `春_weather_comment_enhanced100.csv`）

### Q: メモリ使用量が増加する
**解決策**:
1. 定期的に`clear_cache()`を呼び出す
2. `cache_ttl_minutes`を短く設定する

### Q: 初回アクセスが遅い
**解決策**:
1. 頻繁に使用するデータは`preload_season()`で事前読み込み
2. アプリケーション起動時に必要なデータを読み込んでおく

## まとめ

LazyCommentRepositoryは、メモリ効率と起動速度を重視した実装です。適切に使用することで、大規模なデータセットでも効率的にコメント管理が可能になります。
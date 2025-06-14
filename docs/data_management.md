# データ管理機能

## 概要

MobileCommentGeneratorは時間の経過とともに蓄積されるデータを効率的に管理するための機能を提供しています。

## 管理対象データ

### 1. forecast_cache（天気予報キャッシュ）
- **場所**: `data/forecast_cache/*.csv`
- **内容**: 各地点の天気予報データのキャッシュ
- **増加ペース**: 1日あたり約100-200行/地点
- **推奨管理**: 30日以上古いデータは削除

### 2. generation_history（生成履歴）
- **場所**: `data/generation_history.json`
- **内容**: コメント生成の履歴
- **増加ペース**: 1回の生成で1エントリ
- **推奨管理**: 100MB超えたらアーカイブ

## 設定

`config/s3_config.yaml`で管理パラメータを設定できます：

```yaml
data_management:
  # forecast_cacheの保持日数
  forecast_cache_retention_days: 30
  
  # generation_historyの最大サイズ（MB）
  generation_history_max_size_mb: 100
  
  # generation_historyのアーカイブ間隔（日）
  generation_history_archive_interval_days: 7
```

環境変数でも設定可能：
- `FORECAST_CACHE_RETENTION_DAYS`
- `GENERATION_HISTORY_MAX_SIZE_MB`
- `GENERATION_HISTORY_ARCHIVE_DAYS`

## 使用方法

### コマンドラインでの実行

```bash
# 統計情報の確認（ドライラン）
python scripts/cleanup_data.py --dry-run

# 実際にクリーンアップを実行
python scripts/cleanup_data.py

# 保持日数を指定
python scripts/cleanup_data.py --retention-days 14

# forecast_cacheのみクリーンアップ
python scripts/cleanup_data.py --skip-history

# generation_historyのみアーカイブ
python scripts/cleanup_data.py --skip-forecast

# 古いアーカイブも削除（5個より古いものを削除）
python scripts/cleanup_data.py --clean-archives --keep-archives 5
```

### プログラムからの使用

```python
from src.utils.data_manager import DataManager

# マネージャーを初期化
manager = DataManager()

# 統計情報を取得
stats = manager.get_data_statistics()
print(f"forecast_cacheファイル数: {stats['forecast_cache']['file_count']}")
print(f"generation_historyサイズ: {stats['generation_history']['size_mb']}MB")

# forecast_cacheをクリーンアップ（30日より古いデータを削除）
result = manager.clean_forecast_cache(retention_days=30)
print(f"削除された行数: {result['deleted_rows']}")

# generation_historyをアーカイブ
result = manager.archive_generation_history()
print(f"アーカイブされたエントリ数: {result['archived_entries']}")

# 古いアーカイブを削除（最新5個を保持）
result = manager.cleanup_old_archives(keep_count=5)
print(f"削除されたアーカイブ数: {result['deleted_count']}")
```

### 定期実行（cron）

毎日午前3時に自動クリーンアップを実行する例：

```bash
# crontabに追加
0 3 * * * cd /path/to/MobileCommentGenerator && python scripts/cleanup_data.py >> logs/cleanup.log 2>&1
```

## アーカイブ

### アーカイブの仕組み

1. `generation_history.json`が設定サイズを超えると、古いエントリを分離
2. 古いエントリは`data/archive/generation_history_YYYYMMDD_HHMMSS.json.gz`に圧縮保存
3. 元ファイルには新しいエントリのみ残る

### アーカイブファイルの確認

```python
# アーカイブリストを取得
archives = manager.get_archive_list()
for archive in archives:
    print(f"{archive['filename']}: {archive['size_mb']:.2f}MB")
```

### アーカイブの復元

必要に応じて、gzipで圧縮されたアーカイブを解凍して内容を確認できます：

```bash
# アーカイブを解凍して確認
gunzip -c data/archive/generation_history_20250114_030000.json.gz | jq '.[0:5]'
```

## モニタリング

### ログ

クリーンアップ処理のログは以下の形式で出力されます：

```
2025-01-14 03:00:00 - INFO - Cleaning forecast cache older than 30 days...
2025-01-14 03:00:05 - INFO - Cleaned forecast_cache_東京.csv: 1500 rows deleted
2025-01-14 03:00:10 - INFO - Forecast cache cleanup complete: {'processed_files': 23, 'deleted_rows': 35000}
```

### アラート設定の推奨

以下の条件でアラートを設定することを推奨します：

1. **forecast_cache**
   - 任意のCSVファイルが10,000行を超えた場合
   - 合計サイズが1GBを超えた場合

2. **generation_history**
   - ファイルサイズが200MBを超えた場合
   - エントリ数が100,000を超えた場合

3. **アーカイブ**
   - アーカイブディレクトリの合計サイズが5GBを超えた場合

## トラブルシューティング

### Q: クリーンアップが失敗する
A: 以下を確認してください：
- ファイルの書き込み権限
- ディスク容量
- 他のプロセスがファイルを使用していないか

### Q: アーカイブが大きくなりすぎる
A: `--clean-archives`オプションで古いアーカイブを削除するか、S3などの外部ストレージへの移動を検討してください。

### Q: パフォーマンスが低下する
A: 大きなCSVファイルの処理には時間がかかります。オフピーク時間に実行することを推奨します。
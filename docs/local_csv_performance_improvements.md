# ローカルCSVリポジトリのパフォーマンス改善ガイド

## 現在の実装

現在の `LazyCommentRepository` は必要な時にのみCSVファイルを読み込む遅延読み込み方式を採用しています。これによりメモリ効率的かつ高速な起動を実現し、大規模なデータセットでも問題なく動作します。

## 改善案

### 1. 遅延読み込み実装 (`local_comment_repository_lazy.py`)

メモリ効率を重視した実装で、以下の特徴があります：

- **イテレータベースの読み込み**: ファイルを一度に読み込まず、必要な分だけ逐次処理
- **ページネーション**: 大量のコメントを扱う際にページ単位で取得
- **検索機能**: キーワード検索時もメモリ効率的に処理

```python
# 使用例
lazy_repo = LazyCommentRepository()

# ページネーション付き取得
comments = lazy_repo.get_comments_paginated(
    season="春", 
    comment_type="weather_comment",
    page=1,
    page_size=50
)

# キーワード検索
results = lazy_repo.search_comments("桜", limit=100)
```

### 2. CSVファイル形式の検証強化

現在の実装に追加された検証機能：

- **ヘッダー検証**: 期待されるカラムが存在するか確認
- **データ型検証**: count値が数値であることを確認
- **コメント長検証**: 200文字を超える場合は切り詰め
- **空コメントスキップ**: 空のエントリを除外

### 3. インデックスファイルの活用

大規模データセット向けの改善案：

```python
# メタデータファイルの例 (output/metadata.json)
{
    "春_weather_comment_enhanced100.csv": {
        "total_count": 1000,
        "file_size": 50000,
        "last_modified": "2024-01-01T00:00:00",
        "top_comments": [
            {"text": "春らしい陽気", "count": 500},
            {"text": "桜が満開", "count": 400}
        ]
    }
}
```

### 4. データベース移行

最終的な解決策として、CSVからSQLiteへの移行：

```python
# SQLiteを使用した実装例
import sqlite3

class SQLiteCommentRepository:
    def __init__(self, db_path: str = "comments.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY,
                season TEXT,
                comment_type TEXT,
                comment_text TEXT,
                count INTEGER,
                created_at TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_season_type 
            ON comments(season, comment_type)
        """)
```

## 推奨事項

1. **現在のデータサイズ評価**: まず `output/` ディレクトリのサイズを確認
2. **段階的な移行**: 
   - 〜100MB: 現在の実装で十分
   - 100MB〜1GB: 遅延読み込み実装を検討
   - 1GB以上: データベース移行を推奨
3. **モニタリング**: メモリ使用量とレスポンス時間を定期的に監視

## ベンチマーク

以下のようなベンチマークテストの実装を推奨：

```python
import time
import psutil
import os

def benchmark_repository(repo, name):
    process = psutil.Process(os.getpid())
    
    # メモリ使用量（初期化前）
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # 初期化時間
    start = time.time()
    repo_instance = repo()
    init_time = time.time() - start
    
    # メモリ使用量（初期化後）
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    
    # コメント取得時間
    start = time.time()
    comments = repo_instance.get_recent_comments(limit=100)
    fetch_time = time.time() - start
    
    print(f"{name}:")
    print(f"  初期化時間: {init_time:.3f}秒")
    print(f"  メモリ増加: {mem_after - mem_before:.1f}MB")
    print(f"  取得時間: {fetch_time:.3f}秒")
```
# CSVリポジトリ実装の選択ガイド

## 概要

MobileCommentGeneratorでは、2種類のCSVリポジトリ実装を提供しています。このガイドでは、それぞれの特徴と適切な選択基準について説明します。

## 実装の比較

### 標準実装（LocalCommentRepository）

**メリット**:
- ✅ 高速なレスポンス（キャッシュ済み）
- ✅ 複数回のアクセスで効率的
- ✅ シンプルな実装

**デメリット**:
- ❌ 初期化時にメモリを消費
- ❌ 大規模データセットでメモリ不足の可能性
- ❌ 起動時間が遅い（全ファイル読み込み）

### 遅延読み込み実装（LazyLocalCommentRepository）

**メリット**:
- ✅ メモリ効率的
- ✅ 高速な起動
- ✅ 大規模データセット対応
- ✅ ページネーション機能

**デメリット**:
- ❌ 初回アクセス時は遅い
- ❌ ファイルI/Oが頻繁
- ❌ 実装がやや複雑

## 選択基準

### データサイズによる選択

```python
import os
from pathlib import Path

def check_csv_size(output_dir="output"):
    """CSVファイルの合計サイズを確認"""
    total_size = 0
    output_path = Path(output_dir)
    
    for csv_file in output_path.glob("*.csv"):
        total_size += csv_file.stat().st_size
    
    size_mb = total_size / (1024 * 1024)
    print(f"CSVファイル合計サイズ: {size_mb:.2f} MB")
    
    if size_mb < 50:
        print("推奨: 標準実装（LocalCommentRepository）")
    elif size_mb < 200:
        print("推奨: どちらでも可（使用パターンに依存）")
    else:
        print("推奨: 遅延読み込み実装（LazyLocalCommentRepository）")
    
    return size_mb

# 使用例
check_csv_size()
```

### 使用パターンによる選択

#### 標準実装を選ぶべきケース

1. **Webアプリケーション**
   - 複数のリクエストで同じデータを使用
   - レスポンス速度が重要
   - メモリに余裕がある

2. **バッチ処理**
   - 全地点・全季節のデータを処理
   - 起動時間よりも処理速度が重要

3. **開発・テスト環境**
   - データサイズが小さい
   - デバッグが容易

#### 遅延読み込み実装を選ぶべきケース

1. **メモリ制限環境**
   - コンテナ環境（メモリ上限あり）
   - 小規模サーバー
   - エッジデバイス

2. **特定データのみ使用**
   - 特定の季節のみ
   - 特定の地点のみ
   - キーワード検索中心

3. **大規模データセット**
   - CSVファイルが200MB超
   - コメント数が数十万件
   - 将来的な拡張を想定

## 実装の切り替え方法

### 環境変数による切り替え

```python
import os
from src.repositories.local_comment_repository import LocalCommentRepository
from src.repositories.local_comment_repository_lazy import LazyLocalCommentRepository

def get_comment_repository():
    """環境に応じたリポジトリを取得"""
    use_lazy = os.getenv("USE_LAZY_CSV_REPO", "false").lower() == "true"
    
    if use_lazy:
        return LazyLocalCommentRepository()
    else:
        return LocalCommentRepository()

# 使用例
repo = get_comment_repository()
```

### 設定ファイルによる切り替え

```python
import yaml
from pathlib import Path

def get_repository_from_config(config_path="config/local_csv_config.yaml"):
    """設定ファイルからリポジトリを取得"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    implementation = config.get("repository", {}).get("implementation", "standard")
    
    if implementation == "lazy":
        from src.repositories.local_comment_repository_lazy import LazyLocalCommentRepository
        return LazyLocalCommentRepository(
            output_dir=config["repository"]["output_dir"]
        )
    else:
        from src.repositories.local_comment_repository import LocalCommentRepository
        return LocalCommentRepository(
            output_dir=config["repository"]["output_dir"]
        )
```

## パフォーマンス測定

### ベンチマークスクリプト

```python
import time
import psutil
import os
from contextlib import contextmanager

@contextmanager
def measure_performance(name):
    """パフォーマンス測定コンテキストマネージャー"""
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024
    start_time = time.time()
    
    yield
    
    elapsed_time = time.time() - start_time
    mem_after = process.memory_info().rss / 1024 / 1024
    mem_increase = mem_after - mem_before
    
    print(f"\n{name}:")
    print(f"  実行時間: {elapsed_time:.3f}秒")
    print(f"  メモリ増加: {mem_increase:.1f}MB")
    print(f"  最終メモリ: {mem_after:.1f}MB")

# 標準実装のテスト
with measure_performance("標準実装"):
    from src.repositories.local_comment_repository import LocalCommentRepository
    repo = LocalCommentRepository()
    comments = repo.get_recent_comments(limit=100)
    print(f"  取得件数: {len(comments)}")

# 遅延読み込み実装のテスト
with measure_performance("遅延読み込み実装"):
    from src.repositories.local_comment_repository_lazy import LazyLocalCommentRepository
    lazy_repo = LazyLocalCommentRepository()
    comments = lazy_repo.get_top_comments_by_season("春", top_n=50)
    print(f"  取得件数: {len(comments)}")
```

## 移行ガイド

### 標準実装から遅延読み込みへの移行

```python
# Before (標準実装)
repo = LocalCommentRepository()
comments = repo.get_recent_comments(limit=100)

# After (遅延読み込み)
lazy_repo = LazyLocalCommentRepository()
# get_recent_commentsは実装されていないため、代替方法を使用
comments = []
for season in ["春", "夏", "秋", "冬"]:
    season_comments = lazy_repo.get_top_comments_by_season(season, top_n=20)
    comments.extend(season_comments)
```

### APIの違い

| メソッド | 標準実装 | 遅延読み込み実装 |
|---------|---------|----------------|
| get_recent_comments() | ✅ | ❌ |
| get_all_available_comments() | ✅ | ❌ |
| get_comments_paginated() | ❌ | ✅ |
| search_comments() | ❌ | ✅ |
| get_top_comments_by_season() | ❌ | ✅ |

## トラブルシューティング

### Q: メモリ不足エラーが発生する

**解決策**:
1. 遅延読み込み実装に切り替える
2. 不要な季節のCSVファイルを別ディレクトリに移動
3. CSVファイルのサイズを削減（使用頻度の低いコメントを削除）

### Q: レスポンスが遅い

**解決策**:
1. 標準実装に切り替える（メモリに余裕がある場合）
2. SSDにCSVファイルを配置
3. 必要なデータのみを読み込むようにクエリを最適化

### Q: どちらを選ぶべきか分からない

**推奨アプローチ**:
1. まず標準実装で開始
2. メモリ使用量を監視
3. 問題が発生したら遅延読み込みに切り替え

## まとめ

- **小〜中規模データ（〜100MB）**: 標準実装を推奨
- **大規模データ（200MB〜）**: 遅延読み込み実装を推奨
- **メモリ制限環境**: 遅延読み込み実装を推奨
- **高速レスポンス重視**: 標準実装を推奨

適切な実装を選択することで、効率的なコメント管理が可能になります。
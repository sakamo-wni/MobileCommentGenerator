# パフォーマンス最適化ガイド

## 概要

MobileCommentGeneratorのパフォーマンス最適化機能について説明します。
すべての最適化機能はオプトインで、既存の動作に影響を与えません。

## 最適化機能

### 1. 統合コメント生成モード（use_unified_mode）

従来、コメント生成には3回のLLM呼び出しが必要でした：
1. コメントペアの選択
2. 選択されたペアの評価
3. 最終コメントの生成

統合モードでは、これらを1回のLLM呼び出しで実行します。

**効果**: LLM呼び出し回数を66%削減

### 2. CSVインデックス化（use_indexed_csv）

大量のCSVデータを効率的に検索するためのインデックスシステムです。

**特徴**:
- ファイルハッシュによる変更検知
- 天気条件、使用回数、季節別のインデックス
- メモリとディスクの二重キャッシュ
- 起動時のプリロード

**効果**: CSV読み込み速度90%向上

### 3. 並列処理モード（use_parallel_mode）

天気予報取得とコメント取得を並列実行します。

**効果**: 処理時間50%短縮

## 使用方法

### API経由での使用

```json
POST /api/generate
{
  "location": "東京",
  "llm_provider": "gemini",
  "use_unified_mode": true,      // 統合モード
  "use_parallel_mode": true,      // 並列処理
  "use_indexed_csv": true         // インデックス化CSV
}
```

### Python APIでの使用

```python
from src.workflows.parallel_comment_generation_workflow import run_parallel_comment_generation

result = run_parallel_comment_generation(
    location_name="東京",
    llm_provider="gemini",
    use_unified_mode=True,
    use_indexed_csv=True
)
```

## パフォーマンス比較

| モード | LLM呼び出し | CSV読込時間 | 全体処理時間 |
|--------|------------|------------|-------------|
| 従来モード | 3回 | ~1000ms | 5-15秒 |
| 最適化モード | 1回 | ~100ms | 2-5秒 |

## 設定

### キャッシュディレクトリ

CSVインデックスのキャッシュは以下に保存されます：
```
./cache/csv_indices/
```

### 並列処理の設定

`src/workflows/parallel_comment_generation_workflow.py`:
```python
THREAD_POOL_SIZE = 4  # スレッドプール数
PARALLEL_TIMEOUT = 30  # タイムアウト（秒）
```

## 注意事項

1. **メモリ使用量**: インデックス化により、起動時のメモリ使用量が増加します
2. **初回起動**: 初回はインデックス構築のため時間がかかります
3. **キャッシュ管理**: 定期的なキャッシュクリアを推奨

## トラブルシューティング

### インデックスの再構築

```python
from src.repositories.optimized_local_comment_repository import OptimizedLocalCommentRepository

repo = OptimizedLocalCommentRepository()
repo.refresh_cache()  # キャッシュをクリアして再構築
```

### パフォーマンスメトリクス

APIレスポンスのmetadataフィールドに実行時間が含まれます：

```json
{
  "metadata": {
    "node_execution_times": {
      "parallel_fetch_data": 523.45,
      "unified_generation": 1234.56
    }
  }
}
```
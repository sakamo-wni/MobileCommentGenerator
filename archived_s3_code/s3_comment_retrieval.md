# S3過去コメント取得機能 (Issue #4) - DEPRECATED

> **注意**: このドキュメントは古い実装に関するものです。現在、システムはS3の代わりにローカルCSVファイルを使用するように変更されました。新しい実装については、`src/repositories/local_comment_repository.py`を参照してください。

このドキュメントでは、Issue #4で実装されたS3過去コメント取得機能の概要と使用方法を説明します。

## 概要

この機能は、S3バケット `it-literacy-457604437098-ap-northeast-1` に保存された過去コメントJSONLファイルを取得・解析し、現在の天気条件に類似したコメントを検索する機能です。LangGraphワークフローのノードとして統合されています。

## 主な機能

### 1. 過去コメントデータ管理 (`src/data/past_comment.py`)
- **PastComment**: 単一の過去コメントデータを管理
- **PastCommentCollection**: 複数の過去コメントをコレクションとして管理
- **CommentType**: コメントタイプの列挙型（weather_comment, advice, unknown）

### 2. S3リポジトリ (`src/repositories/s3_comment_repository.py`)
- **S3CommentRepository**: S3からJSONLファイルを取得・解析
- 期間指定・日付範囲・類似度検索機能
- エラーハンドリング・接続テスト機能

### 3. LangGraphノード (`src/nodes/retrieve_past_comments_node.py`)
- **RetrievePastCommentsNode**: LangGraphノードとしての過去コメント取得
- 天気条件に基づく類似コメント検索
- コメントタイプバランス調整機能

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. AWS認証情報の設定

```bash
# 環境変数での設定
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=ap-northeast-1
export S3_COMMENT_BUCKET=it-literacy-457604437098-ap-northeast-1
```

または `.env` ファイルに設定：

```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=ap-northeast-1
S3_COMMENT_BUCKET=it-literacy-457604437098-ap-northeast-1
```

## 使用例

### 1. 基本的なS3リポジトリの使用

```python
from src.repositories.s3_comment_repository import S3CommentRepository, S3CommentRepositoryConfig

# 設定からリポジトリ作成
config = S3CommentRepositoryConfig()
repo = config.create_repository()

# 接続テスト
if repo.test_connection():
    print("S3接続成功")
    
    # 利用可能期間の取得
    periods = repo.list_available_periods()
    print(f"利用可能期間: {periods}")
    
    # 特定期間のコメント取得
    if periods:
        latest_period = periods[0]
        collection = repo.fetch_comments_by_period(latest_period)
        print(f"取得コメント数: {len(collection.comments)}")
```

### 2. 地点・天気条件でのフィルタリング

```python
# 特定地点のコメント取得
tokyo_collection = repo.fetch_comments_by_period(
    period="202406",
    location="東京"
)

# 天気条件でのフィルタリング
sunny_collection = repo.fetch_comments_by_period(
    period="202406",
    weather_condition="晴れ"
)

print(f"東京のコメント: {len(tokyo_collection.comments)}件")
print(f"晴れのコメント: {len(sunny_collection.comments)}件")
```

### 3. 類似コメント検索

```python
# 現在の天気条件に類似するコメントを検索
similar_comments = repo.search_similar_comments(
    target_weather_condition="晴れ",
    target_temperature=25.0,
    target_location="東京",
    months_back=6,
    max_results=10,
    min_similarity=0.3
)

for comment in similar_comments:
    print(f"類似コメント: {comment.comment_text} "
          f"({comment.location}, {comment.weather_condition})")
```

### 4. LangGraphノードとしての使用

```python
from src.nodes.retrieve_past_comments_node import RetrievePastCommentsNode
from datetime import datetime

# ノードの初期化
node = RetrievePastCommentsNode()

# 状態辞書の準備
state = {
    'location_name': '東京',
    'weather_data': {
        'weather_condition': '晴れ',
        'temperature': 25.0
    },
    'target_datetime': datetime.now()
}

# ノード実行
result = node(state)

# 結果の確認
past_comments = result.get('past_comments', [])
metadata = result.get('comment_retrieval_metadata', {})

print(f"取得コメント数: {len(past_comments)}")
print(f"メタデータ: {metadata}")
```

### 5. 単体関数としての使用

```python
import asyncio
from src.nodes.retrieve_past_comments_node import retrieve_past_comments_for_condition

async def example():
    # 指定条件での過去コメント取得
    comments = await retrieve_past_comments_for_condition(
        location_name='大阪',
        weather_condition='曇り',
        temperature=20.0,
        max_comments=5
    )
    
    for comment in comments:
        print(f"コメント: {comment['comment_text']}")

asyncio.run(example())
```

## データ構造

### PastComment データクラス

```python
@dataclass
class PastComment:
    location: str                    # 地点名
    datetime: datetime              # 投稿日時
    weather_condition: str          # 天気状況
    comment_text: str               # コメント本文
    comment_type: CommentType       # コメントタイプ
    temperature: Optional[float]    # 気温（℃）
    weather_code: Optional[str]     # 天気コード
    humidity: Optional[float]       # 湿度（%）
    wind_speed: Optional[float]     # 風速（m/s）
    precipitation: Optional[float]  # 降水量（mm）
    source_file: Optional[str]      # 元ファイル名
    raw_data: Dict[str, Any]        # 元のJSONデータ
```

### S3ファイル構造

```
S3バケット: it-literacy-457604437098-ap-northeast-1
パス構造: downloaded_jsonl_files_archive/YYYYMM/YYYYMM.jsonl

例:
- downloaded_jsonl_files_archive/202406/202406.jsonl
- downloaded_jsonl_files_archive/202405/202405.jsonl
```

### JSONLファイル形式

```json
{"location": "東京", "datetime": "2024-06-05T12:00:00+09:00", "weather_condition": "晴れ", "comment_text": "いい天気ですね", "comment_type": "weather_comment", "temperature": 25.0}
{"location": "東京", "datetime": "2024-06-05T12:00:00+09:00", "weather_condition": "晴れ", "comment_text": "日焼け対策を", "comment_type": "advice", "temperature": 25.0}
```

## 高度な機能

### 1. 類似度計算アルゴリズム

```python
def calculate_similarity_score(
    self, 
    target_weather_condition: str,
    target_temperature: Optional[float] = None,
    target_location: Optional[str] = None
) -> float:
    """
    類似度スコア計算（0.0-1.0）
    
    重み配分:
    - 天気状況: 50%
    - 気温: 30%
    - 地点: 20%
    """
```

### 2. コメントタイプバランス調整

```python
# 取得されるコメントのタイプバランスを自動調整
balanced_comments = node._balance_comment_types(all_comments)

# 例: max_comments_per_type = 10 の場合
# - weather_comment: 5件
# - advice: 5件
```

### 3. フォールバック戦略

1. **類似天気状況検索**: 天気条件・気温・地点での類似検索
2. **地点検索**: 地点のみでの検索
3. **全体検索**: 全体からの最近コメント取得

### 4. エラーハンドリング

```python
try:
    collection = repo.fetch_comments_by_period('202406')
except S3CommentRepositoryError as e:
    print(f"S3エラー: {e}")
except ValueError as e:
    print(f"パラメータエラー: {e}")
```

## パフォーマンス考慮事項

### 1. 取得制限
- **デフォルト検索期間**: 6ヶ月
- **最大コメント数**: タイプごとに10件
- **最小類似度**: 0.3

### 2. キャッシュ戦略
- 頻繁にアクセスされるデータのメモリキャッシュ
- 期間別ファイルの効率的な読み込み

### 3. メモリ最適化
- 大量データ処理時のストリーミング読み込み
- 不要なデータの早期解放

## トラブルシューティング

### よくある問題

1. **AWS認証エラー**
   ```python
   # 認証情報の確認
   import boto3
   session = boto3.Session()
   credentials = session.get_credentials()
   print(f"Access Key: {credentials.access_key}")
   ```

2. **S3接続エラー**
   ```python
   # 接続テスト
   if not repo.test_connection():
       print("S3接続に失敗しました")
       # バケット名・リージョンの確認
   ```

3. **データが見つからない**
   ```python
   # 利用可能期間の確認
   periods = repo.list_available_periods()
   if not periods:
       print("利用可能なデータがありません")
   ```

4. **JSONLパースエラー**
   - 不正なJSON行は自動でスキップされます
   - ログでパースエラーの詳細を確認可能

## テスト

```bash
# 全テスト実行
python -m pytest tests/test_past_comment.py
python -m pytest tests/test_s3_comment_repository.py
python -m pytest tests/test_retrieve_past_comments_node.py

# カバレッジ付きテスト
python -m pytest tests/ --cov=src --cov-report=html
```

## 今後の拡張予定

1. **キャッシュ機能の実装**
2. **検索アルゴリズムの改善**
3. **より詳細な統計情報**
4. **バッチ処理機能**
5. **他のストレージ形式対応**

## 関連ファイル

### Core Implementation
- `src/data/past_comment.py` - 過去コメントデータクラス
- `src/repositories/s3_comment_repository.py` - S3リポジトリ
- `src/nodes/retrieve_past_comments_node.py` - LangGraphノード

### Tests
- `tests/test_past_comment.py` - データクラステスト
- `tests/test_s3_comment_repository.py` - リポジトリテスト
- `tests/test_retrieve_past_comments_node.py` - ノードテスト

### Configuration
- `requirements.txt` - 依存関係（boto3, jsonlines等）

# ローカルCSVリポジトリ使用ガイド

## 概要

MobileCommentGeneratorは、過去のコメントデータをローカルCSVファイルから読み込みます。このガイドでは、CSVファイルの形式、配置方法、および使用方法について説明します。

## CSVファイルの形式

### ファイル命名規則

CSVファイルは以下の命名規則に従う必要があります：

```
{季節}_{タイプ}_enhanced100.csv
```

- **季節**: `春`, `夏`, `秋`, `冬`, `梅雨`, `台風`
- **タイプ**: `weather_comment`, `advice`

例：
- `春_weather_comment_enhanced100.csv`
- `梅雨_advice_enhanced100.csv`

### CSVフォーマット

#### weather_commentファイル

```csv
weather_comment,count
春らしい陽気です,100
桜が満開です,50
暖かい一日になりそう,30
```

#### adviceファイル

```csv
advice,count
花粉症対策を忘れずに,80
日焼け止めも必要です,40
薄着でも大丈夫そう,20
```

### データ要件

1. **ヘッダー行**: 必須。正しいカラム名を含む必要があります
2. **count列**: 人気度を示す数値（整数）
3. **コメント長**: 推奨15文字以内、最大200文字
4. **文字エンコーディング**: UTF-8（BOM付きも可）

## ファイル配置

CSVファイルは `output/` ディレクトリに配置します：

```
MobileCommentGenerator/
└── output/
    ├── 春_weather_comment_enhanced100.csv
    ├── 春_advice_enhanced100.csv
    ├── 夏_weather_comment_enhanced100.csv
    ├── 夏_advice_enhanced100.csv
    ├── 秋_weather_comment_enhanced100.csv
    ├── 秋_advice_enhanced100.csv
    ├── 冬_weather_comment_enhanced100.csv
    ├── 冬_advice_enhanced100.csv
    ├── 梅雨_weather_comment_enhanced100.csv
    ├── 梅雨_advice_enhanced100.csv
    ├── 台風_weather_comment_enhanced100.csv
    └── 台風_advice_enhanced100.csv
```

## 実装の選択

### 1. 標準実装 (LocalCommentRepository)

**特徴**:
- 初期化時に全CSVファイルをメモリにキャッシュ
- 高速なアクセス
- メモリ使用量は全データサイズに比例

**推奨される使用場面**:
- CSVファイルの合計サイズが100MB未満
- 頻繁にコメントを取得する場合
- レスポンス速度が重要な場合

```python
from src.repositories.local_comment_repository import LocalCommentRepository

# 標準実装の使用
repo = LocalCommentRepository()
comments = repo.get_recent_comments(limit=100)
```

### 2. 遅延読み込み実装 (LazyLocalCommentRepository)

**特徴**:
- 必要な時にのみファイルを読み込み
- メモリ効率的
- 初回アクセス時は若干遅い

**推奨される使用場面**:
- CSVファイルの合計サイズが100MB以上
- メモリ使用量を抑えたい場合
- 特定の季節のデータのみを使用する場合

```python
from src.repositories.local_comment_repository_lazy import LazyLocalCommentRepository

# 遅延読み込み実装の使用
lazy_repo = LazyLocalCommentRepository()

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

## エラーハンドリング

### CSVファイルが見つからない場合

```python
# LocalCommentRepositoryは自動的にディレクトリを作成
repo = LocalCommentRepository("custom/output/path")
# ログ: "Output directory not found: custom/output/path, creating it..."
```

### 不正なCSVフォーマット

システムは以下のエラーを検出し、ログに記録します：

1. **ヘッダーなし**: `CSV file {path} has no headers`
2. **必須カラムなし**: `CSV file {path} missing expected column '{column}'`
3. **不正なcount値**: `Invalid count value '{value}' in {path} line {line}`
4. **空のコメント**: スキップされ、デバッグログに記録
5. **長すぎるコメント**: 200文字で切り詰め、警告ログ

## パフォーマンスチューニング

### メモリ使用量の監視

```python
import psutil
import os

def check_memory_usage():
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"現在のメモリ使用量: {mem_mb:.1f} MB")

# リポジトリ初期化前
check_memory_usage()

# リポジトリ初期化
repo = LocalCommentRepository()

# リポジトリ初期化後
check_memory_usage()
```

### CSVファイルサイズの確認

```bash
# output/ディレクトリのサイズを確認
du -sh output/

# 各CSVファイルのサイズを確認
ls -lh output/*.csv
```

## トラブルシューティング

### Q: コメントが読み込まれない

**確認事項**:
1. CSVファイルが `output/` ディレクトリに存在するか
2. ファイル名が命名規則に従っているか
3. CSVファイルのエンコーディングがUTF-8か
4. ヘッダー行が正しいか

### Q: メモリ使用量が多い

**対処法**:
1. 遅延読み込み実装に切り替える
2. 不要な季節のCSVファイルを別ディレクトリに移動
3. CSVファイルから使用頻度の低いコメントを削除

### Q: パフォーマンスが遅い

**対処法**:
1. 標準実装（キャッシュあり）を使用
2. CSVファイルをSSDに配置
3. より高性能なマシンで実行

## ベストプラクティス

1. **定期的なデータ整理**: 使用頻度の低いコメントは定期的に削除
2. **バックアップ**: CSVファイルは定期的にバックアップ
3. **バージョン管理**: CSVファイルの変更履歴を記録
4. **検証スクリプト**: CSVファイルの形式を自動検証するスクリプトを用意

```python
# CSV検証スクリプトの例
def validate_csv_files(output_dir="output"):
    from pathlib import Path
    import csv
    
    errors = []
    output_path = Path(output_dir)
    
    for csv_file in output_path.glob("*.csv"):
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    errors.append(f"{csv_file}: No headers")
                    continue
                
                # 必須カラムの確認
                if "weather_comment" in csv_file.name:
                    if "weather_comment" not in reader.fieldnames:
                        errors.append(f"{csv_file}: Missing 'weather_comment' column")
                elif "advice" in csv_file.name:
                    if "advice" not in reader.fieldnames:
                        errors.append(f"{csv_file}: Missing 'advice' column")
                
                if "count" not in reader.fieldnames:
                    errors.append(f"{csv_file}: Missing 'count' column")
                
        except Exception as e:
            errors.append(f"{csv_file}: {str(e)}")
    
    return errors

# 検証実行
errors = validate_csv_files()
if errors:
    print("検証エラー:")
    for error in errors:
        print(f"  - {error}")
else:
    print("すべてのCSVファイルが正常です")
```
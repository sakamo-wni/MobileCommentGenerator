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

## LazyCommentRepositoryの使用

MobileCommentGeneratorでは、LazyCommentRepository（遅延読み込み実装）を使用してCSVファイルを管理します。

**特徴**:
- 必要な時にのみファイルを読み込み
- メモリ効率的
- 大規模データセット対応
- キャッシュ機能により2回目以降は高速アクセス

```python
from src.repositories.lazy_comment_repository import LazyCommentRepository

# リポジトリの初期化
repo = LazyCommentRepository()

# 季節ごとのコメント取得
spring_comments = repo.get_comments_by_season("春")

# 天気コメントのみ取得
weather_comments = repo.get_weather_comments_by_season("夏")

# アドバイスコメントのみ取得
advice = repo.get_advice_by_season("秋")

# キーワード検索
results = repo.search_comments(
    keyword="晴れ",
    season="春",
    comment_type=CommentType.WEATHER_COMMENT
)
```

## エラーハンドリング

### CSVファイルが見つからない場合

```python
# LazyCommentRepositoryでカスタムディレクトリを指定
repo = LazyCommentRepository(output_dir="custom/output/path")
# 注意: ディレクトリが存在しない場合はFileNotFoundErrorが発生
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
repo = LazyCommentRepository()

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
1. キャッシュをクリアする（repo.clear_cache()）
2. 不要な季節のCSVファイルを別ディレクトリに移動
3. CSVファイルから使用頻度の低いコメントを削除

### Q: パフォーマンスが遅い

**対処法**:
1. 事前読み込みを活用（repo.preload_season()）
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
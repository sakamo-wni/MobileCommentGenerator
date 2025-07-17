# 例外システム統一計画

## 現状分析

### 1. 既存の2つの例外システム

#### A. 単純な例外クラス（新しく分割したもの）
- 場所: `src/exceptions/` の個別ファイル
- 特徴: 単純な継承構造、国際化なし

#### B. AppExceptionベースのシステム
- 場所: `src/exceptions/error_types.py`
- 特徴: 
  - ErrorType列挙型でエラー種別を管理
  - 国際化サポート（日本語/英語）
  - エラー詳細情報の構造化
  - API応答用のシリアライズ機能

### 2. 重複する例外クラスのマッピング

| 単純な例外クラス | AppExceptionベース | ErrorType |
|---|---|---|
| ConfigurationError | ConfigError | CONFIG_ERROR |
| DataValidationError | ValidationError | VALIDATION_ERROR |
| DataParsingError | - | PARSING_ERROR |
| NetworkError | - | NETWORK_ERROR |
| APITimeoutError | - | TIMEOUT_ERROR |
| APIError | - | API_ERROR |
| WeatherDataUnavailableError | WeatherFetchError | WEATHER_FETCH |
| DataError | DataAccessError | DATA_ACCESS |
| FileIOError | - | SYSTEM_ERROR |

## 移行計画

### フェーズ1: 旧例外クラスを非推奨化（完了）
1. ✅ 各例外ファイルに非推奨警告を追加
2. ✅ バージョン2.0.0での削除予定を明記
3. ✅ 移行先の具体例を提供

### フェーズ2: AppExceptionベースへの統合（完了）
1. ✅ __init__.pyを更新して新しい例外システムからインポート
2. ✅ 後方互換性のためのエイリアスを提供
3. ✅ 非推奨エイリアスに警告メッセージを追加
4. ✅ error_types.pyに必要なErrorTypeを追加

### フェーズ3: 使用箇所の更新（進行中）
1. ✅ ConfigurationErrorの使用箇所を更新
2. ✅ テストコードのインポートを更新
3. ⏳ 他の例外クラスの使用箇所を段階的に更新

## 実装状況

### 完了した作業

1. **error_types.pyへの新しいErrorType追加**
   - ✅ RATE_LIMIT_ERROR
   - ✅ API_RESPONSE_ERROR  
   - ✅ FILE_IO_ERROR
   - ✅ LOCATION_NOT_FOUND
   - ✅ COMMENT_GENERATION_ERROR
   - ✅ MISSING_DATA_ERROR

2. **新しい例外クラスの追加**
   - ✅ RateLimitError
   - ✅ APIResponseError
   - ✅ FileIOError
   - ✅ LocationNotFoundError
   - ✅ CommentGenerationError
   - ✅ MissingDataError

3. **__init__.pyの更新**
   - ✅ error_types.pyからのインポートに統一
   - ✅ 後方互換性のためのエイリアス追加
   - ✅ 非推奨警告の実装

4. **旧例外ファイルの非推奨化**
   - ✅ api_errors.py
   - ✅ data_errors.py
   - ✅ business_errors.py
   - ✅ system_errors.py

### 今後の作業

1. **コードベース全体での使用箇所更新**
   - 旧例外クラスの使用箇所を特定
   - AppExceptionベースの例外に置き換え

2. **テストの拡充**
   - 新しい例外クラスのテスト作成
   - 国際化機能のテスト

3. **バージョン2.0.0での削除**
   - 旧例外ファイルの削除
   - 非推奨エイリアスの削除

## 移行ガイド

### 旧例外から新例外への移行例

```python
# 旧: api_errors.py
from src.exceptions import APIError
raise APIError("APIエラーが発生しました")

# 新: error_types.pyベース
from src.exceptions import AppException, ErrorType
raise AppException(ErrorType.API_ERROR, "APIエラーが発生しました")
```

```python
# 旧: data_errors.py
from src.exceptions import DataValidationError
raise DataValidationError("データ検証エラー")

# 新: error_types.pyベース
from src.exceptions import ValidationError
raise ValidationError("データ検証エラー")
```

## 利点
1. **一貫性のあるエラーハンドリング**: すべての例外がAppExceptionベース
2. **国際化サポートの統一**: 日本語/英語のメッセージが統一管理
3. **エラー情報の構造化**: ErrorTypeによるエラー種別の明確化
4. **API応答の標準化**: to_dict()メソッドによるAPIレスポンスの統一
5. **保守性の向上**: 重複コードの削減

## 注意点
1. **既存コードへの影響を最小限に**: エイリアスによる後方互換性維持
2. **段階的な移行**: バージョン2.0.0までの移行期間を設定
3. **十分なテストカバレッジ**: 新しい例外クラスの動作確認
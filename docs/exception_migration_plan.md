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

## 統合後の構造案

```python
# src/exceptions/error_types.py に追加するErrorType
class ErrorType(Enum):
    # ... 既存のタイプ ...
    
    # API関連（追加）
    API_KEY_ERROR = "api_key_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    API_RESPONSE_ERROR = "api_response_error"
    
    # ビジネスロジック関連（追加）
    LOCATION_NOT_FOUND = "location_not_found"
    COMMENT_GENERATION_ERROR = "comment_generation_error"
    
    # データ関連（追加）
    MISSING_DATA_ERROR = "missing_data_error"
    
    # システム関連（追加）
    FILE_IO_ERROR = "file_io_error"
```

## 利点
1. 一貫性のあるエラーハンドリング
2. 国際化サポートの統一
3. エラー情報の構造化
4. API応答の標準化
5. 保守性の向上

## 注意点
1. 既存コードへの影響を最小限に抑える
2. 段階的な移行で安定性を確保
3. 十分なテストカバレッジを確保
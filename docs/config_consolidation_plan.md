# 設定ファイル統合計画

## 現状の問題点

### 1. 設定クラスの重複
- `unified_config.py`: APIConfig, WeatherConfig, AppConfig, ServerConfig
- `app_settings.py`: AppConfig (weather, langgraph含む)
- `app_config.py`: APIKeys, UISettings, GenerationSettings, DataSettings

### 2. 責任の分散
- APIキー管理が3箇所に分散
- 環境変数の読み込みが各クラスで重複
- デフォルト値の管理が分散

## 統合方針

### 1. 設定ファイルの役割を明確化

#### `src/config/config.py` (新規作成)
統一された設定管理クラス
```python
@dataclass
class Config:
    api: APIConfig
    weather: WeatherConfig
    app: AppSettings
    server: ServerConfig
    llm: LLMConfig
    data: DataConfig
```

#### `src/config/env_schema.py` (新規作成)
環境変数のスキーマ定義と検証
```python
class EnvSchema:
    # 必須環境変数
    required: List[str]
    # オプション環境変数とデフォルト値
    optional: Dict[str, Any]
```

### 2. 段階的な移行計画

#### Phase 1: 基盤整備（現在のブランチで実施）
1. `Config`クラスの作成
2. 環境変数スキーマの定義
3. 既存コードとの互換性レイヤー作成

#### Phase 2: 段階的移行
1. 新規コードは新しい`Config`クラスを使用
2. 既存コードを段階的に移行
3. 旧設定クラスに非推奨警告を追加

#### Phase 3: 完全移行
1. すべてのコードを新設定に移行
2. 旧設定ファイルを削除
3. ドキュメント更新

### 3. フロントエンドとの統合

#### `shared/src/config/common.ts`
フロントエンドとバックエンドで共有する設定
```typescript
export interface CommonConfig {
  api: {
    timeout: number;
    retryCount: number;
  };
  batch: {
    concurrentLimit: number;
    requestTimeout: number;
  };
  date: {
    format: string;
    timezone: string;
  };
}
```

### 4. 環境変数の役割明確化

#### 環境変数で管理すべきもの
- APIキー、シークレット
- 環境依存の設定（ポート番号、URL）
- 機能フラグ（DEBUG、ENV）

#### 設定ファイルで管理すべきもの
- ビジネスロジックの定数
- デフォルト値
- バリデーションルール

### 5. 実装優先順位

1. **高優先度**
   - 新しい`Config`クラスの作成
   - 環境変数スキーマの定義
   - 互換性レイヤーの実装

2. **中優先度**
   - 共通設定のsharedパッケージへの移動
   - APIキー管理の統一

3. **低優先度**
   - YAMLファイルの整理
   - ドキュメントの更新

## 期待される効果

1. **設定管理の簡素化**
   - 1つの統一されたエントリーポイント
   - 明確な責任分離

2. **保守性の向上**
   - 設定の重複削除
   - 型安全性の向上

3. **開発効率の向上**
   - 設定の場所が明確
   - 環境変数の文書化

## 次のステップ

1. この計画のレビューと承認
2. Phase 1の実装開始
3. 既存コードへの影響調査
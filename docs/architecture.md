# プロジェクト構成とLangGraphワークフロー

## 📁 プロジェクト構成

```
MobileCommentGenerator/
├── src/                                    # バックエンドソースコード
│   ├── workflows/                          # LangGraphワークフロー実装
│   ├── nodes/                              # 各処理ノードの実装
│   ├── llm/                                # LLMプロバイダー統合
│   ├── data/                               # データモデル・管理
│   ├── apis/                               # 外部API統合
│   └── utils/                              # ユーティリティ関数
├── frontend/                               # Nuxt.js 3 フロントエンド（Vue版）
│   ├── pages/                              # ページコンポーネント
│   ├── components/                         # UIコンポーネント
│   ├── composables/                        # Composition API
│   └── nuxt.config.ts                      # Nuxt設定
├── react-version/                          # React版フロントエンド（新規）
│   ├── src/                                # Reactソースコード
│   ├── public/                             # 静的ファイル
│   └── vite.config.ts                      # Vite設定
├── shared/                                 # 共通ロジック・型定義
│   ├── types/                              # 共通型定義
│   ├── api/                                # APIクライアント
│   ├── composables/                        # 共通ロジック
│   └── utils/                              # 共通ユーティリティ
├── tests/                                  # テストスイート
├── docs/                                   # ドキュメント
├── examples/                               # 使用例
├── config/                                 # 設定ファイル
├── app.py                                  # Streamlit UI
├── api_server.py                           # FastAPI サーバー
├── output/                                 # CSVファイル出力ディレクトリ
├── .github/                                # GitHub Actions CI/CD
│   └── workflows/                          # ワークフロー定義
├── pnpm-workspace.yaml                     # pnpmモノレポ設定
├── uv.lock                                 # uvロックファイル
├── requirements.txt                        # 従来の依存関係ファイル
├── pytest.ini                              # pytest設定
├── mypy.ini                                # mypy設定
├── Makefile                                # ビルド・実行スクリプト
├── setup.sh                                # セットアップスクリプト
└── README.md                               # プロジェクト概要
```

## 🔄 LangGraphワークフロー

以下はMobileCommentGeneratorの正確なワークフロー構造です：

```mermaid
graph TB
    Start([開始]) --> input[InputNode<br/>入力検証・初期化]
    
    input --> fetch_forecast[FetchForecastNode<br/>天気予報取得]
    
    fetch_forecast --> retrieve_comments[RetrieveCommentsNode<br/>過去コメント取得]
    
    retrieve_comments --> select_pair[SelectCommentPairNode<br/>LLMによる適応的ペア選択]
    
    select_pair --> should_evaluate{評価すべきか？<br/>should_evaluate}
    
    should_evaluate -->|evaluate| evaluate_candidate[EvaluateCandidateNode<br/>候補評価]
    should_evaluate -->|generate| generate_comment[GenerateCommentNode<br/>コメント生成]
    
    evaluate_candidate --> should_retry{リトライ必要？<br/>should_retry}
    
    should_retry -->|retry<br/>最大5回| select_pair
    should_retry -->|continue| generate_comment
    
    generate_comment --> output[OutputNode<br/>出力整形]
    
    output --> End([終了])
    
    style input fill:#e1f5fe
    style fetch_forecast fill:#f3e5f5
    style retrieve_comments fill:#e8f5e9
    style select_pair fill:#fff3e0
    style evaluate_candidate fill:#fce4ec
    style generate_comment fill:#fff8e1
    style output fill:#e0f2f1
    
    style should_evaluate fill:#ffebee
    style should_retry fill:#ffebee
```

### ワークフローの詳細説明

1. **InputNode**: 入力パラメータの検証と初期状態の設定
2. **FetchForecastNode**: WxTech APIから天気予報データを取得（12時間周期）
3. **RetrieveCommentsNode**: ローカルCSVファイルから過去のコメントデータを取得
4. **SelectCommentPairNode**: LLMが天気に基づいて最適なコメントペアを選択
5. **EvaluateCandidateNode**: 選択されたペアの評価（評価基準に基づく検証）
6. **GenerateCommentNode**: 最終的なコメント生成
7. **OutputNode**: 生成結果の整形と出力

### 条件分岐

- **should_evaluate**: LLMプロバイダーが設定されていない場合は評価をスキップ
- **should_retry**: 評価が失敗した場合、最大5回までリトライ

## 🌟 主要特徴

- **LangGraphワークフロー**: 状態管理とエラーハンドリングロジックを体系的に実装
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic対応  
- **適応性ベース選抜**: ローカルCSVから最適なペアを適応性に基づいてLLM選抜
- **表現ルール遵守**: NG表現禁止・値域制限・文字数規制の自動チェック
- **12時間周期天気予報**: デフォルトで12時間周期のデータを使用
- **デュアルUI実装**: Streamlit（開発用）+ Nuxt.js 3（Vue版） + React（新規）
- **FastAPI統合**: RESTful APIでフロントエンドとバックエンドを分離
- **天気予報キャッシュ**: 効率的な天気データ管理とキャッシュ機能
- **モノレポ構成**: pnpmワークスペースによる効率的な依存管理

## 🏗️ アーキテクチャ設計原則

### 1. 関心の分離
- **ノード**: 単一責任の原則に基づいた独立した処理単位
- **ワークフロー**: ノード間の調整とステート管理
- **データモデル**: ビジネスロジックから独立したデータ構造

### 2. 拡張性
- **プロバイダーパターン**: 新しいLLMプロバイダーの追加が容易
- **設定駆動**: YAMLファイルによる動的な設定管理
- **モジュラー設計**: 機能の追加・削除が独立して可能

### 3. エラーハンドリング
- **グレースフルデグラデーション**: 部分的な障害でも継続動作
- **リトライメカニズム**: 一時的な障害への自動対応
- **詳細なエラーログ**: デバッグのための包括的なログ出力

### 4. パフォーマンス
- **遅延読み込み**: 大規模CSVファイルの効率的な処理
- **キャッシュ機能**: 天気予報データの再利用
- **並列処理**: 可能な限りの並列実行
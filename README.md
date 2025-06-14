# 天気予報コメント生成システム ☁️

LangGraphとLLMを活用した天気予報コメント自動生成システムです。指定した各地点の天気情報と過去のコメントデータをもとに、LLM（大規模言語モデル）を利用して短い天気コメント（約15文字）を自動生成します。

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🗂️ プロジェクト構成

```
mobile-comment-generator/
├── src/                        # バックエンドPythonアプリケーション
│   ├── data/                   # データクラス管理
│   │   ├── comment_generation_state.py  # ワークフロー状態管理
│   │   ├── comment_pair.py     # コメントペアデータモデル
│   │   ├── evaluation_criteria.py      # 評価基準定義
│   │   ├── location_manager.py # 地点データ管理
│   │   ├── past_comment.py     # 過去コメント管理
│   │   ├── weather_data.py     # 天気データモデル
│   │   ├── weather_trend.py    # 天気傾向分析
│   │   └── Chiten.csv          # 地点マスターデータ
│   ├── apis/                   # 外部API連携
│   │   └── wxtech_client.py    # WxTech天気API統合
│   ├── algorithms/             # アルゴリズム実装
│   │   ├── comment_evaluator.py        # コメント評価ロジック
│   │   └── similarity_calculator.py    # 類似度計算
│   ├── nodes/                  # LangGraphノード
│   │   ├── input_node.py       # 入力ノード
│   │   ├── weather_forecast_node.py    # 天気予報取得ノード
│   │   ├── retrieve_past_comments_node.py # 過去コメント取得ノード
│   │   ├── select_comment_pair_node.py  # コメント選択ノード
│   │   ├── evaluate_candidate_node.py   # 候補評価ノード
│   │   ├── generate_comment_node.py     # コメント生成ノード
│   │   ├── output_node.py      # 出力ノード
│   │   └── mock_nodes.py       # モックノード（テスト用）
│   ├── workflows/              # ワークフロー実装
│   │   └── comment_generation_workflow.py
│   ├── llm/                    # LLM統合
│   │   ├── llm_client.py       # LLMクライアント基底
│   │   ├── llm_manager.py      # LLMマネージャー
│   │   ├── prompt_builder.py   # プロンプト構築
│   │   ├── prompt_templates.py # プロンプトテンプレート
│   │   └── providers/          # LLMプロバイダー実装
│   │       ├── base_provider.py        # 基底プロバイダー
│   │       ├── openai_provider.py      # OpenAI統合
│   │       ├── gemini_provider.py      # Google Gemini統合
│   │       └── anthropic_provider.py   # Anthropic Claude統合
│   ├── repositories/           # データリポジトリ
│   │   ├── local_comment_repository.py # ローカルデータアクセス
│   │   └── s3_comment_repository.py    # S3データアクセス
│   ├── ui/                     # Streamlit UI
│   │   ├── streamlit_components.py     # UIコンポーネント
│   │   ├── streamlit_utils.py  # UIユーティリティ
│   │   └── pages/              # マルチページ構成
│   │       └── statistics.py   # 統計情報ページ
│   └── config/                 # 設定管理
│       ├── weather_config.py   # 天気予報設定
│       └── comment_config.py   # コメント生成設定
├── frontend/                   # Vue.js/Nuxt.jsプロジェクト（分離済み）
├── tests/                      # テストスイート
│   ├── integration/            # 統合テスト専用
│   └── test_*.py               # 各種ユニットテスト
├── scripts/                    # ユーティリティスクリプト
├── data/                       # データファイル（CSV等）
├── output/                     # 生成されたCSVファイル
├── config/                     # 設定ファイル
├── docs/                       # ドキュメント
├── .env.example                # 環境変数例
├── app.py                      # Streamlitメインエントリポイント
├── enhanced_comment_generator.py # 拡張コメント生成器
├── tests/                      # テストファイル
│   ├── unit/                  # 単体テスト
│   └── integration/           # 統合テスト
│       └── test_weather_validation_system.py  # 天気検証システム統合テスト
├── requirements.txt            # Python依存関係
├── requirements-dev.txt        # 開発用依存関係
├── requirements-streamlit.txt  # Streamlit用依存関係
├── pyproject.toml              # プロジェクト設定
├── pytest.ini                  # pytest設定
├── mypy.ini                    # mypy設定
├── Makefile                    # ビルド・実行スクリプト
├── setup.sh                    # セットアップスクリプト
└── README.md                   # このファイル
```

## 🌟 主な特徴

- **LangGraphワークフロー**: 状態とエラーハンドリングロジックを体系的に実装
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic Claude対応  
- **適応性ベース選択**: 過去コメントから最適なペアを選択
- **表現ルール適用**: NGワード・文字数制限の自動チェック
- **12時間後天気予報**: デフォルトで12時間後の天気データを使用
- **複合UI実装**: Streamlit（バックエンド）+ Nuxt.js（フロントエンド・分離済み）

## 📊 現在の進捗状況

### ✅ Phase 1: 基礎機能（100%完了）
- [x] **地点データ管理システム**: CSV読み込み・更新検証・位置情報取得機能
- [x] **天気予報統合機能**: WxTech API統合（12時間後データ対応）
- [x] **過去コメント取得**: enhanced50.csvベースのデータ解析・頻度選択検証
- [x] **LLM統合**: マルチプロバイダー対応（OpenAI/Gemini/Anthropic）

### ✅ Phase 2: LangGraphワークフロー（100%完了）
- [x] **SelectCommentPairNode**: コメント頻度選択ベースによる選択
- [x] **EvaluateCandidateNode**: 複数の評価基準による検証
- [x] **基本ワークフロー**: 実装済みノードでの骨格実装
- [x] **InputNode/OutputNode**: 本実装完了
- [x] **GenerateCommentNode**: LLM統合実装
- [x] **統合テスト**: エンドtoエンドテスト実装
- [x] **ワークフロー可視化**: 実行トレース記録ツール

### ✅ Phase 3: Streamlit UI（100%完了）
- [x] **基本UI実装**: 地点選択・LLMプロバイダー選択・コメント生成
- [x] **詳細情報表示**: 天気情報・過去コメント・評価結果表示
- [x] **バッチ処理**: 複数地点一括処理機能
- [x] **CSV出力**: 生成結果のエクスポート機能
- [x] **エラーハンドリング**: ユーザーフレンドリーなエラー表示

### 🔧 Phase 4: フロントエンド分離（部分完了）
- [x] **フロントエンド分離**: Vue.js/Nuxt.jsを独立プロジェクトに移行
- [x] **プロジェクト構造の明確化**: frontend/とsrc/の責任分離
- [ ] **API実装**: RESTful APIエンドポイント
- [ ] **統合ドキュメント**: フロントエンド・バックエンド連携ガイド

### 🚀 Phase 5: デプロイメント（0%完了）
- [ ] **AWSデプロイメント**: Lambda/ECS・CloudWatch統合

## 🔧 セットアップ

### 環境要件
- Python 3.10以上
- uv（推奨）またはpip
- Node.js 18以上（フロントエンド用）

### バックエンド

#### Method 1: 自動セットアップスクリプト（推奨）

```bash
# 1. リポジトリクローン
git clone https://github.com/sakamo-wni/MobileCommentGenerator.git
cd MobileCommentGenerator

# 2. ワンコマンドセットアップ
chmod +x setup.sh
./setup.sh dev

# 3. 仮想環境有効化
source .venv/bin/activate

# 4. 動作確認
python -c "import langgraph; print('✅ Setup successful!')"
```

#### Method 2: Makefileを使用

```bash
# 1. リポジトリクローン
git clone https://github.com/sakamo-wni/MobileCommentGenerator.git
cd MobileCommentGenerator

# 2. ワンコマンドセットアップ
make setup

# 3. 仮想環境有効化
source .venv/bin/activate

# 4. 利用可能なコマンド確認
make help
```

#### 🔧 手動セットアップ

```bash
# 1. 仮想環境作成
uv venv --python 3.11
source .venv/bin/activate

# 2. 依存関係インストール
uv pip install -r requirements.txt              # 基本版
uv pip install -r requirements-dev.txt          # 開発版

# 3. 環境変数設定
cp .env.example .env
# .envファイルでAPIキーを設定

# 4. 動作確認
streamlit run app.py
```

### フロントエンド

```bash
# フロントエンドディレクトリへ移動
cd frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev
```

ブラウザで http://localhost:3000 を開いてください

## 🔑 API キー設定

### 必須設定
`.env`ファイルでLLMプロバイダーのAPIキーを設定:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 天気予報データ
WXTECH_API_KEY=your_wxtech_api_key_here

# AWS（オプション）
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

## ⚙️ 天気予報時刻の設定

システムはデフォルトで**12時間後の天気予報データ**を使用してコメントを生成します。この設定は環境変数で簡単に変更できます。

### 環境変数での設定

`.env`ファイルに以下の環境変数を追加してください：

```bash
# 何時間後の予報を使用するか（デフォルト: 12）
WEATHER_FORECAST_HOURS_AHEAD=12
```

### 設定例

```bash
# 6時間後の予報を使用する場合
WEATHER_FORECAST_HOURS_AHEAD=6

# 24時間後（翌日同時刻）の予報を使用する場合
WEATHER_FORECAST_HOURS_AHEAD=24

# 3時間後の予報を使用する場合
WEATHER_FORECAST_HOURS_AHEAD=3
```

### 設定の確認

設定した時刻は、UIの各地点詳細情報で「⏰ 予報時刻」として表示されます。表示される時刻は日本標準時（JST）に自動変換されます。

**注意**: この設定により、すべてのコンポーネントで統一的に指定した時間後の予報が使用されます。

## 🚀 使用方法

### Streamlit UI（推奨）

```bash
make run-streamlit
```

1. ブラウザで http://localhost:8501 を開く
2. 左パネルから地点とLLMプロバイダーを選択
3. 「コメント生成」ボタンをクリック
4. 生成されたコメントと詳細情報を確認

### フロントエンド（Vue.js）

```bash
make run-frontend
```

1. ブラウザで http://localhost:3000 を開く
2. モダンなWebUIでコメント生成機能を利用

### プログラマティック使用

```python
from src.workflows.comment_generation_workflow import run_comment_generation
from datetime import datetime

# 単一地点のコメント生成
result = run_comment_generation(
    location_name="東京",
    target_datetime=datetime.now(),
    llm_provider="openai"
)

print(f"生成コメント: {result['final_comment']}")
```

## 🖥️ よく使うコマンド

```bash
# アプリ起動
make run-streamlit                      # Streamlit UI
make run-frontend                       # Vue.js フロントエンド

# 開発ツール
make test                               # テスト実行
make lint                               # コード品質チェック
make format                             # コードフォーマット

# メンテナンス
make clean                              # 一時ファイル削除
make update-deps                        # 依存関係更新
```

## 🧪 テスト

```bash
# 全テスト実行
make test

# カバレッジ付きテスト
make test-cov

# 統合テスト
make test-integration

# クイックテスト（主要機能のみ）
make quick-test
```

## 🎨 開発ツール

### コード品質
```bash
make lint                               # コード品質チェック
make format                             # コードフォーマット
make type-check                         # 型チェック
```

### 設定済みツール
- **Black**: コードフォーマッター（100文字）
- **isort**: インポート整理
- **mypy**: 型チェック
- **ruff**: 高速リンター
- **pytest**: テストフレームワーク

## 📊 プロジェクト情報

### 技術スタック

**バックエンド:**
- Python 3.10+
- LangGraph 0.0.35+
- LangChain 0.1.0+
- Streamlit 1.28.0+
- OpenAI/Gemini/Anthropic APIs

**フロントエンド:**
- Vue.js 3.5.16
- Nuxt.js 3.17.4
- TypeScript 5.3.0

**データ処理:**
- Pandas 2.1.4+
- NumPy 1.26.2+
- Scikit-learn 1.3.2+

**AWS (オプション):**
- Boto3 1.34.0+
- AWS CLI 1.32.0+

### メタデータ
- **バージョン**: 1.0.0
- **ライセンス**: MIT
- **最終更新**: 2025-06-12
- **開発チーム**: WNI Team

## 🎯 パフォーマンス

- **応答時間**: 平均3-5秒（地点あたり）
- **精度**: 過去データベースとの適合性90%+
- **対応地点**: 全国1000+地点
- **LLMプロバイダー**: 3社対応

## 🔄 更新履歴

- **v1.0.0** (2025-06-12): Phase 3完了 - Streamlit UI実装・README.md更新
- **v0.3.0** (2025-06-06): Phase 2完了 - LangGraphワークフロー実装
- **v0.2.0** (2025-06-04): Phase 1完了 - 基礎機能実装
- **v0.1.0** (2025-06-01): プロジェクト開始

## 🤝 コントリビューション

1. Issue作成で問題報告・機能要望
2. Fork & Pull Request での貢献
3. [開発ガイドライン](docs/CONTRIBUTING.md)に従った開発

## 🔧 トラブルシューティング

### よくある問題

**依存関係の競合**
```bash
# 環境をリセット
make clean-venv
make setup
```

**APIキーエラー**
- `.env`ファイルにAPIキーが正しく設定されているか確認
- 環境変数が読み込まれているか確認: `echo $OPENAI_API_KEY`

**天気データ取得エラー**
- WXTECH_API_KEYが正しく設定されているか確認
- ネットワーク接続を確認

**LLMプロバイダーエラー**
- 選択したプロバイダーのAPIキーが設定されているか確認
- APIの利用制限に達していないか確認

## 📞 サポート

問題や質問がございましたら、GitHubのIssuesで報告してください。

---

**このセットアップガイドで問題が解決しない場合は、GitHubのIssuesで報告してください。**
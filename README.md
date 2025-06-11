# 天気予報コメント生成システム ☁️

LangGraphとLLMを活用した天気予報コメント自動生成システムです。指定した各地点の天気情報と過去のコメントデータをもとに、LLM（大規模言語モデル）を利用して短い天気コメント（約15文字）を自動生成します。

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🏗️ プロジェクト構成

```
mobile-comment-generator/
├── frontend/                    # Nuxt.js フロントエンドアプリケーション
│   ├── components/              # Vue.js コンポーネント
│   ├── pages/                   # ページルーティング
│   ├── composables/             # Vue Composition API
│   ├── types/                   # TypeScript型定義
│   ├── server/                  # サーバーサイド機能
│   ├── public/                  # 静的アセット
│   ├── package.json             # フロントエンド依存関係
│   ├── nuxt.config.ts           # Nuxt設定
│   └── README.md                # フロントエンド説明ドキュメント
├── src/                         # バックエンドPythonアプリケーション
│   ├── data/                    # データクラス管理
│   ├── apis/                    # 外部API連携
│   ├── repositories/            # データリポジトリ
│   ├── nodes/                   # LangGraphノード
│   ├── workflows/               # ワークフロー実装
│   ├── algorithms/              # 頻度選択アルゴリズム（新規）
│   ├── llm/                     # LLM統合
│   ├── ui/                      # Streamlit UI
│   └── config/                  # 設定管理
├── tests/                       # テストスイート
├── scripts/                     # ユーティリティスクリプト
├── docs/                        # ドキュメント
└── examples/                    # 使用例
```

## 主な特徴

- **LangGraphワークフロー**: 状況と例外エラーハンドリングロジックを体系的に実装
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic Claude対応  
- **適応性ベース選択**: 過去コメントから最適なペアを選択
- **表現ルール適用**: NGワード・文字数制限の自動チェック
- **複合UI実装**: Streamlit（バックエンド）+ Nuxt.js（フロントエンド）

## 現在の進捗状況（2025/6/8時点）

### ✅ Phase 1: 基礎構築（100%完了）
- [x] **地点データ管理システム**: CSV読込み・更新検証・位置情報取得機能
- [x] **天気予報統合機能**: WxTech API統合
- [x] **過去コメント取得**: CSV解析・頻度選択検証
- [x] **LLM統合**: マルチプロバイダー対応

### ✅ Phase 2: LangGraphワークフロー（100%完了）
- [x] **SelectCommentPairNode**: コメント頻度選択ベースによる選択
- [x] **EvaluateCandidateNode**: 複数の評価基準による検証
- [x] **基本ワークフロー**: 実装済みノードでの骨格実装
- [x] **InputNode/OutputNode**: 本実装完了
- [x] **GenerateCommentNode**: LLM統合実装
- [x] **統合テスト**: エンドtoエンドテスト実装
- [x] **ワークフロー可視化**: 実行トレース記録ツール

### ✅ Phase 3: フロントエンド分離（完了）
- [x] **フロントエンド分離**: Vue.js/Nuxt.jsを独立プロジェクトに移行
- [x] **プロジェクト構造の明確化**: frontend/とsrc/の責任分離
- [ ] **API実装**: RESTful APIエンドポイント
- [ ] **統合ドキュメント**: フロントエンド・バックエンド連携ガイド

### 🔧 Phase 4: デプロイメント（0%完了）
- [ ] **AWSデプロイメント**: Lambda/ECS・CloudWatch統合

## セットアップ

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
uv pip install -r requirements.txt           # 基本版
uv pip install -r requirements-dev.txt       # 開発版

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

## 🖥️ よく使うコマンド

```bash
# アプリ起動
make run-streamlit                 # Streamlit UI
make run-frontend                  # Vue.js フロントエンド

# 開発ツール
make test                          # テスト実行
make lint                          # コード品質チェック
make format                        # コードフォーマット

# メンテナンス
make clean                         # 一時ファイル削除
make update-deps                   # 依存関係更新
```

## 📦 パッケージ管理

### 依存関係の分類
- `requirements.txt` - 本番環境用の基本依存関係
- `requirements-dev.txt` - 開発環境用の追加依存関係

### uvの活用
- 高速インストール: `uv pip install -r requirements.txt`
- プロジェクト管理: `uv sync`
- Python管理: `uv python install 3.11`

## 🔐 トラブルシューティング

### よくある問題
1. **依存関係の競合**: `langchain-core>=0.1.42`で解決済み
2. **Python バージョン**: 3.10以上が必要
3. **uvが未インストール**: セットアップスクリプトが自動インストール

### 完全リセット
```bash
make clean-venv                    # 仮想環境削除
make setup                         # 再セットアップ
```

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
make lint                          # コード品質チェック
make format                        # コードフォーマット
make type-check                    # 型チェック
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
- **最終更新**: 2025-06-08
- **開発チーム**: WNI Team

## 📈 パフォーマンス

- **応答時間**: 平均3-5秒（地点あたり）
- **精度**: 過去データベースとの適合性90%+
- **対応地点**: 全国1000+地点
- **LLMプロバイダー**: 3社対応

## 🔄 更新履歴

- **v1.0.0** (2025-06-08): Phase 3完了 - フロントエンド分離
- **v0.3.0** (2025-06-06): Phase 2完了 - LangGraphワークフロー実装
- **v0.2.0** (2025-06-04): Phase 1完了 - 基礎機能実装
- **v0.1.0** (2025-06-01): プロジェクト開始

## 🤝 コントリビューション

1. Issue作成で問題報告・機能要望
2. Fork & Pull Request での貢献
3. [開発ガイドライン](docs/CONTRIBUTING.md)に従った開発

## 📞 サポート

問題や質問がございましたら、GitHubのIssuesで報告してください。

---

**このセットアップガイドで問題が解決しない場合は、GitHubのIssuesで報告してください。**
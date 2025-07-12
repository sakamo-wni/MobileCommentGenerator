# 🌦️ MobileCommentGenerator

天気予報に基づいて適応的なコメントを生成するAIシステム。LangGraphフレームワークを使用して構築され、過去のコメントデータを活用してコンテキストに応じたコメントを生成します。

## 📚 ドキュメント

- [🏗️ アーキテクチャ](docs/architecture.md) - プロジェクト構成とLangGraphワークフロー
- [🚀 デプロイメント](docs/deployment.md) - AWSデプロイメントガイド
- [🎨 フロントエンド](docs/frontend-guide.md) - Nuxt.js/React実装ガイド
- [📡 API](docs/api-guide.md) - API設定と使用方法
- [🛠️ 開発](docs/development.md) - 開発ツールとテスト

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

## 🚀 クイックスタート

### 1. 環境構築
```bash
# セットアップスクリプト使用
chmod +x setup.sh
./setup.sh dev
```

### 2. 環境変数設定
`.env`ファイルにAPIキーを設定：
```env
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here  
ANTHROPIC_API_KEY=your_key_here
WXTECH_API_KEY=your_key_here
```

### 2-1. パフォーマンスチューニング（オプション）
実行時間を大幅に短縮したい場合、以下の環境変数を設定できます：

```env
# 高速なLLMモデルを使用（GPT-3.5-turbo等）
LLM_PERFORMANCE_MODE=true

# 並列実行数を増やす（デフォルト: 3）
MAX_LLM_WORKERS=8

# 評価リトライ回数を減らす（デフォルト: 3）
MAX_EVALUATION_RETRIES=2
```

これらの設定により、処理時間を最大80%削減できます。

### 3. 実行
```bash
# APIサーバー起動
uv run ./start_api.sh

# フロントエンド起動（別ターミナル）
pnpm dev  # Nuxt.js版
# または
pnpm dev:react  # React版
```

## 📈 現在の進捗状況

### ✅ 完了済み
- LangGraphワークフロー実装
- マルチLLMプロバイダー対応
- Nuxt.js 3 + React デュアルフロントエンド
- FastAPI RESTful API
- 重複コメント防止機能

### 🚧 進行中
- AWSデプロイメント準備



## 📊 現在のアップデート内容 (v1.1.5)

- **重複コメント防止機能**: 完全同一・類似表現の自動検出と代替選抜
- **天気優先順位ルール**: 雨・雪・雷を最優先、気温35℃以上で熱中症警戒
- **適応的コメント選抜**: LLMによる天気状況に基づく最適なコメント選択
- **タイムゾーン対応**: JST時刻での翌朝9:00-18:00の天気予報に基づく生成


## 📖 使用方法

### Nuxt.jsフロントエンド（推奨）

```bash
# APIサーバー起動（ポート3001）
uv run ./start_api.sh
```

1. ブラウザで http://localhost:3000 を開く
2. 左パネルから地点と天気設定
3. 「🌦️ コメント生成」ボタンをクリック
4. 生成されたコメントと天気情報を確認

### React版フロントエンド（新規）

```bash
# React版開発サーバー起動（ポート5173）
pnpm dev:react
```

1. ブラウザで http://localhost:5173 を開く
2. 地点選択から希望の地点を選択
3. 生成設定でLLMプロバイダーを選択
4. 「コメント生成」ボタンをクリック
5. 生成されたコメントと天気情報を確認

### Streamlit UI（開発・デバッグ用）

```bash
uv run streamlit run app.py
```

1. ブラウザで http://localhost:8501 を開く
2. 左パネルからLLMプロバイダーを選択
3. 「🌦️ コメント生成」ボタンをクリック
4. 生成されたコメントと天気情報を確認

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
print(f"アドバイス: {result['advice_comment']}")
```


## 📔 貢献方法

1. Issueを作成して問題報告・機能要望
2. Fork & Pull Requestでの貢献
3. ドキュメントの改善提案も歓迎

詳細な開発ワークフローについては[開発ガイド](docs/development.md#開発ワークフロー)を参照してください。

## 📘 サポート

問題が解決しない場合は、[GitHub Issues](https://github.com/sakamo-wni/MobileCommentGenerator/issues)で報告してください。

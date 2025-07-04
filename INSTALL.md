# インストールガイド

## 前提条件

- Python 3.10以上
- pip または uv（推奨）

## インストール方法

### 1. 基本インストール（必須）

```bash
# pipを使用する場合
pip install -e .

# uvを使用する場合（推奨）
uv pip install -e .
```

### 2. 開発環境のセットアップ

開発に必要なツール（pytest、black、mypy等）をインストール：

```bash
# pipを使用する場合
pip install -e ".[dev]"

# uvを使用する場合
uv pip install -e ".[dev]"
```

### 3. 追加機能のインストール

#### Streamlit UIの追加機能

```bash
pip install -e ".[streamlit-extra]"
```

#### API開発環境

```bash
pip install -e ".[api]"
```

#### AWS連携機能

```bash
pip install -e ".[aws]"
```

#### すべての機能をインストール（開発環境用）

```bash
pip install -e ".[all]"
```

## 環境変数の設定

`.env`ファイルを作成し、必要なAPIキーを設定：

```env
# LLM Provider API Keys
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Weather API
WXTECH_API_KEY=your_wxtech_api_key

# AWS (オプション)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=ap-northeast-1
```

## 古いrequirements.txtからの移行

以下のコマンドで既存の環境を更新：

```bash
# 古い依存関係をアンインストール
pip uninstall -r requirements.txt -y
pip uninstall -r requirements-dev.txt -y
pip uninstall -r requirements-streamlit.txt -y

# 新しい方法でインストール
pip install -e ".[all]"
```

## トラブルシューティング

### 依存関係の競合が発生した場合

```bash
# 仮想環境をクリーンな状態にリセット
pip freeze | xargs pip uninstall -y
pip install -e ".[all]"
```

### 特定のパッケージバージョンが必要な場合

`pyproject.toml`の該当箇所を編集してから再インストール：

```bash
pip install -e . --upgrade
```
# 設定ガイド

このドキュメントでは、MobileCommentGeneratorの設定方法について説明します。

## 環境変数

アプリケーションは環境変数を使用して設定を管理します。`.env`ファイルまたはシステム環境変数で設定できます。

### 環境変数テンプレートの生成

以下のコマンドで環境変数のテンプレートを生成できます：

```bash
python -m src.config.env_schema > .env.template
```

### 必須環境変数

#### 本番環境（APP_ENV=production）で必須

- **WXTECH_API_KEY**: 天気予報データ取得用のWxTech APIキー
- **LLMプロバイダーのAPIキー**（以下のいずれか1つ以上）:
  - **OPENAI_API_KEY**: OpenAI APIキー
  - **ANTHROPIC_API_KEY**: Anthropic APIキー
  - **GEMINI_API_KEY**: Google Gemini APIキー

### 環境変数一覧

#### API設定

| 環境変数 | 説明 | デフォルト値 | 必須 |
|---------|------|------------|------|
| WXTECH_API_KEY | WxTech API key for weather data | "" | 本番環境で必須 |
| OPENAI_API_KEY | OpenAI API key | "" | いずれか1つ必須 |
| ANTHROPIC_API_KEY | Anthropic API key | "" | いずれか1つ必須 |
| GEMINI_API_KEY | Google Gemini API key | "" | いずれか1つ必須 |
| GEMINI_MODEL | Gemini model name | "gemini-1.5-flash" | - |
| OPENAI_MODEL | OpenAI model name | "gpt-4o-mini" | - |
| ANTHROPIC_MODEL | Anthropic model name | "claude-3-haiku-20240307" | - |
| API_TIMEOUT | API timeout in seconds | 30 | - |

#### 天気予報設定

| 環境変数 | 説明 | デフォルト値 | 範囲 |
|---------|------|------------|------|
| WEATHER_FORECAST_HOURS_AHEAD | Hours ahead for weather forecast | 12 | 1-72 |
| WEATHER_FORECAST_DAYS | Days of weather forecast | 3 | 1-7 |
| WEATHER_CACHE_TTL | Weather cache TTL in seconds | 3600 | 60以上 |
| WEATHER_CACHE_DIR | Weather cache directory | "data/forecast_cache" | - |

#### アプリケーション設定

| 環境変数 | 説明 | デフォルト値 | 選択肢 |
|---------|------|------------|--------|
| APP_ENV | Application environment | "development" | development, staging, production |
| DEBUG | Debug mode | false | true, false |
| LOG_LEVEL | Log level | "INFO" | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| DATA_DIR | Data output directory | "output" | - |
| CSV_DIR | CSV output directory | "output" | - |

#### サーバー設定

| 環境変数 | 説明 | デフォルト値 | 範囲 |
|---------|------|------------|------|
| API_HOST | API server host | "0.0.0.0" | - |
| API_PORT | API server port | 8000 | 1024-65535 |
| FRONTEND_PORT | Frontend server port | 3000 | 1024-65535 |
| CORS_ORIGINS | Allowed CORS origins (comma-separated) | "" | - |

#### LLM設定

| 環境変数 | 説明 | デフォルト値 | 範囲/選択肢 |
|---------|------|------------|------------|
| DEFAULT_LLM_PROVIDER | Default LLM provider | "gemini" | openai, anthropic, gemini |
| LLM_TEMPERATURE | LLM temperature | 0.7 | 0.0-2.0 |
| LLM_MAX_TOKENS | LLM max tokens | 1000 | 100-4000 |

## 設定ファイルの構造

アプリケーションは統一された設定管理システムを使用しています：

```python
from src.config.config import get_config

config = get_config()

# APIキーの取得
api_key = config.api.wxtech_api_key

# 天気設定の取得
forecast_hours = config.weather.forecast_hours_ahead

# アプリケーション設定の取得
debug_mode = config.app.debug
```

## 環境別設定例

### 開発環境（.env.development）

```bash
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# APIキー（開発用）
WXTECH_API_KEY=your-dev-wxtech-key
GEMINI_API_KEY=your-dev-gemini-key
```

### 本番環境（.env.production）

```bash
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# APIキー（本番用）
WXTECH_API_KEY=your-prod-wxtech-key
OPENAI_API_KEY=your-prod-openai-key
ANTHROPIC_API_KEY=your-prod-anthropic-key
GEMINI_API_KEY=your-prod-gemini-key

# サーバー設定
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## 設定の検証

アプリケーション起動時に設定の検証が自動的に行われます。
本番環境では、必須の環境変数が設定されていない場合、エラーが発生します。

## トラブルシューティング

### "WXTECH_API_KEY is required in production environment" エラー

本番環境でWXTECH_API_KEYが設定されていません。`.env`ファイルまたは環境変数で設定してください。

### "At least one LLM API key is required" エラー

本番環境では、少なくとも1つのLLM APIキー（OPENAI_API_KEY、ANTHROPIC_API_KEY、GEMINI_API_KEY）が必要です。

### ディレクトリが作成されない

DATA_DIR、CSV_DIR、WEATHER_CACHE_DIRで指定されたディレクトリは、アプリケーション起動時に自動的に作成されます。
書き込み権限があることを確認してください。
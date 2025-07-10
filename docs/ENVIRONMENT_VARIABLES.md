# 環境変数リファレンス

このドキュメントでは、MobileCommentGeneratorで使用可能なすべての環境変数について説明します。

## API設定

### 必須のAPIキー（本番環境）

| 環境変数 | 説明 | デフォルト値 | 必須 |
|---------|------|------------|------|
| `WXTECH_API_KEY` | WxTech Weather APIキー | なし | 本番環境で必須 |
| `OPENAI_API_KEY` | OpenAI APIキー | なし | LLMプロバイダーの1つ以上が必須 |
| `ANTHROPIC_API_KEY` | Anthropic Claude APIキー | なし | LLMプロバイダーの1つ以上が必須 |
| `GEMINI_API_KEY` | Google Gemini APIキー | なし | LLMプロバイダーの1つ以上が必須 |

### API動作設定

| 環境変数 | 説明 | デフォルト値 | 値の範囲 |
|---------|------|------------|---------|
| `API_TIMEOUT` | APIリクエストのタイムアウト時間（秒） | 30 | 1-300 |
| `API_RETRY_COUNT` | APIリクエストの最大リトライ回数 | 3 | 0-10 |

## アプリケーション設定

| 環境変数 | 説明 | デフォルト値 | 値の範囲 |
|---------|------|------------|---------|
| `APP_ENV` | 実行環境 | development | development, staging, production |
| `APP_DEBUG` | デバッグモード | false | true, false |
| `APP_LOG_LEVEL` | ログレベル | INFO | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `APP_DATA_DIR` | データディレクトリ | ./data | 任意のパス |
| `APP_CSV_DIR` | CSVファイルディレクトリ | ./data/csv | 任意のパス |

## サーバー設定

| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| `API_HOST` | APIサーバーのホスト | 0.0.0.0 |
| `API_PORT` | APIサーバーのポート | 8001 |
| `FRONTEND_PORT` | フロントエンドのポート | 5173 |
| `CORS_ORIGINS` | 許可するCORSオリジン（カンマ区切り） | localhost:5173 |

## LLM設定

| 環境変数 | 説明 | デフォルト値 | 値の範囲 |
|---------|------|------------|---------|
| `DEFAULT_LLM_PROVIDER` | デフォルトのLLMプロバイダー | gemini | openai, anthropic, gemini |
| `LLM_TEMPERATURE` | 生成の温度パラメータ | 0.7 | 0.0-2.0 |
| `LLM_MAX_TOKENS` | 最大トークン数 | 1000 | 1-4000 |
| `OPENAI_MODEL` | 使用するOpenAIモデル | gpt-4o-mini | 任意のOpenAIモデル |
| `ANTHROPIC_MODEL` | 使用するClaudeモデル | claude-3-haiku-20240307 | 任意のClaudeモデル |
| `GEMINI_MODEL` | 使用するGeminiモデル | gemini-1.5-flash | 任意のGeminiモデル |

## 天気予報設定

| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| `WEATHER_FORECAST_HOURS_AHEAD` | 予報を取得する時間（現在時刻から） | 12 |
| `WEATHER_FORECAST_DAYS` | 予報を取得する日数 | 3 |
| `WEATHER_CACHE_TTL` | 予報キャッシュの有効期限（秒） | 3600 |
| `WEATHER_CACHE_DIR` | 予報キャッシュディレクトリ | data/forecast_cache |

## 天気関連の閾値設定

### 気温閾値

| 環境変数 | 説明 | デフォルト値 (°C) |
|---------|------|-----------------|
| `TEMP_HOT_WEATHER_THRESHOLD` | 暑い天気の閾値 | 30.0 |
| `TEMP_WARM_WEATHER_THRESHOLD` | 暖かい天気の閾値 | 25.0 |
| `TEMP_COOL_WEATHER_THRESHOLD` | 涼しい天気の閾値 | 10.0 |
| `TEMP_COLD_WEATHER_THRESHOLD` | 寒い天気の閾値 | 5.0 |
| `TEMP_COLD_COMMENT_THRESHOLD` | 寒さコメントの閾値 | 12.0 |
| `TEMP_SIGNIFICANT_DAILY_DIFF` | 前日との有意な気温差 | 5.0 |
| `TEMP_HOURLY_SIGNIFICANT_DIFF` | 12時間での有意な気温差 | 3.0 |
| `TEMP_LARGE_DAILY_RANGE` | 大きな日較差 | 15.0 |
| `TEMP_MEDIUM_DAILY_RANGE` | 中程度の日較差 | 10.0 |

### 湿度閾値

| 環境変数 | 説明 | デフォルト値 (%) |
|---------|------|------------------|
| `HUMIDITY_HIGH_THRESHOLD` | 高湿度の閾値 | 80.0 |
| `HUMIDITY_LOW_THRESHOLD` | 低湿度の閾値 | 30.0 |
| `HUMIDITY_VERY_HIGH_THRESHOLD` | 非常に高い湿度の閾値 | 90.0 |
| `HUMIDITY_VERY_LOW_THRESHOLD` | 非常に低い湿度の閾値 | 20.0 |

### 降水量閾値

| 環境変数 | 説明 | デフォルト値 (mm) |
|---------|------|-------------------|
| `PRECIP_LIGHT_RAIN_THRESHOLD` | 小雨の閾値 | 1.0 |
| `PRECIP_MODERATE_RAIN_THRESHOLD` | 中雨の閾値 | 5.0 |
| `PRECIP_HEAVY_RAIN_THRESHOLD` | 大雨の閾値 | 10.0 |
| `PRECIP_VERY_HEAVY_RAIN_THRESHOLD` | 激しい雨の閾値 | 30.0 |
| `PRECIP_THUNDER_STRONG_THRESHOLD` | 雷雨強弱判定の閾値 | 5.0 |

### 風速閾値

| 環境変数 | 説明 | デフォルト値 (m/s) |
|---------|------|-------------------|
| `WIND_LIGHT_BREEZE_THRESHOLD` | 軽い風の閾値 | 3.0 |
| `WIND_MODERATE_BREEZE_THRESHOLD` | 中程度の風の閾値 | 7.0 |
| `WIND_STRONG_BREEZE_THRESHOLD` | 強い風の閾値 | 12.0 |
| `WIND_GALE_THRESHOLD` | 強風の閾値 | 20.0 |

### その他の天気定数

| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| `WEATHER_HEATSTROKE_WARNING_TEMP` | 熱中症警戒開始温度 | 34.0 |
| `WEATHER_HEATSTROKE_SEVERE_TEMP` | 熱中症厳重警戒温度 | 35.0 |
| `WEATHER_COLD_WARNING_TEMP` | 防寒対策が不要になる温度 | 15.0 |
| `WEATHER_CHANGE_THRESHOLD` | 「変わりやすい」と判定する変化回数 | 2 |

### データ検証範囲

| 環境変数 | 説明 | デフォルト値 |
|---------|------|------------|
| `VALIDATION_MIN_TEMPERATURE` | 最低気温の下限 | -50.0 |
| `VALIDATION_MAX_TEMPERATURE` | 最高気温の上限 | 60.0 |
| `VALIDATION_MIN_HUMIDITY` | 最低湿度 | 0.0 |
| `VALIDATION_MAX_HUMIDITY` | 最高湿度 | 100.0 |
| `VALIDATION_MIN_WIND_SPEED` | 最低風速 | 0.0 |
| `VALIDATION_MAX_WIND_SPEED` | 最高風速（台風含む） | 200.0 |
| `VALIDATION_MIN_PRECIPITATION` | 最低降水量 | 0.0 |
| `VALIDATION_MAX_PRECIPITATION` | 最高降水量（極端な場合） | 500.0 |

## 環境変数の設定方法

### 1. `.env`ファイルを使用する場合

プロジェクトルートに`.env`ファイルを作成し、必要な環境変数を設定します：

```bash
# API Keys
WXTECH_API_KEY=your_api_key_here
GEMINI_API_KEY=your_gemini_key_here

# Application Settings
APP_ENV=development
APP_DEBUG=true
APP_LOG_LEVEL=DEBUG

# Weather Thresholds (optional overrides)
TEMP_HOT_WEATHER_THRESHOLD=32.0
HUMIDITY_HIGH_THRESHOLD=85.0
```

### 2. システム環境変数として設定する場合

Linux/macOS:
```bash
export WXTECH_API_KEY="your_api_key_here"
export APP_ENV="production"
```

Windows (PowerShell):
```powershell
$env:WXTECH_API_KEY = "your_api_key_here"
$env:APP_ENV = "production"
```

### 3. Dockerを使用する場合

docker-compose.yml:
```yaml
services:
  app:
    environment:
      - WXTECH_API_KEY=${WXTECH_API_KEY}
      - APP_ENV=production
      - APP_DEBUG=false
```

## 注意事項

1. **セキュリティ**: APIキーなどの機密情報は、`.env`ファイルに記載し、`.gitignore`に追加してバージョン管理から除外してください。

2. **型変換**: 数値型の環境変数は自動的に適切な型に変換されます。無効な値が設定された場合はエラーになります。

3. **検証**: 設定値は起動時に検証され、不正な値（例：温度閾値の順序が逆など）がある場合はエラーメッセージが表示されます。

4. **優先順位**: 環境変数はデフォルト値を上書きします。`.env`ファイルの値よりもシステム環境変数が優先されます。
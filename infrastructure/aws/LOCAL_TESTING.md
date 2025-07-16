# ローカルテストガイド

SAM CLIを使用してAWS Lambda関数をローカルでテストする方法を説明します。

## 📋 前提条件

- Docker Desktop が起動していること
- AWS CLI が設定済みであること
- SAM CLI がインストール済みであること

## 🚀 クイックスタート

### 1. 環境変数の設定

`env.json.example` をコピーして `env.json` を作成：

```bash
cp env.json.example env.json
# 必要に応じて環境変数を編集
```

### 2. ソースコードの同期

Lambda関数にプロジェクトのソースコードをコピー：

```bash
make sync-code
```

### 3. ビルド

```bash
make build
```

### 4. ローカルAPIの起動

```bash
make local-api
```

APIは `http://localhost:3000` で利用可能になります。

## 🧪 テスト方法

### API エンドポイントのテスト

```bash
# ヘルスチェック
curl http://localhost:3000/health

# コメント生成リクエスト
curl -X POST http://localhost:3000/generate \
  -H "Content-Type: application/json" \
  -H "x-api-key: test-api-key" \
  -d '{
    "location_id": "関東_東京",
    "generation_params": {
      "comment_type": "general",
      "tone": "friendly"
    }
  }'
```

### Lambda関数の個別テスト

```bash
# API Handler
make invoke-api-handler

# Weather Fetcher
make invoke-weather-fetcher

# Comment Processor
make invoke-comment-processor

# Cache Warmer
make invoke-cache-warmer
```

## 🛠️ デバッグ

### ログの確認

SAM CLIのローカル実行では、ログは標準出力に表示されます。

### ブレークポイントデバッグ

VS Codeを使用する場合：

1. `.vscode/launch.json` を作成：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "SAM Local API",
      "type": "python",
      "request": "attach",
      "port": 5678,
      "host": "localhost",
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "/var/task"
        }
      ]
    }
  ]
}
```

2. Lambda関数にデバッガーを追加：

```python
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

3. デバッグモードで起動：

```bash
sam local start-api --debug-port 5678
```

## 📝 テストイベント

`events/` ディレクトリにテスト用のイベントファイルが用意されています：

- `api_generate_request.json` - コメント生成APIリクエスト
- `api_status_request.json` - ステータス確認APIリクエスト
- `sqs_comment_generation.json` - SQSメッセージイベント
- `weather_fetcher_request.json` - 天気データ取得リクエスト
- `cache_warmer_event.json` - キャッシュウォーマーイベント

カスタムイベントを作成してテスト：

```bash
sam local invoke ApiHandlerFunction -e events/my_custom_event.json
```

## 🗄️ ローカルDynamoDB

ローカルDynamoDBを使用する場合：

1. DynamoDB Localを起動：

```bash
make local-dynamodb
```

2. テーブルを作成：

```bash
aws dynamodb create-table \
  --table-name weather-comment-generator-dev-comments \
  --attribute-definitions \
    AttributeName=location_id,AttributeType=S \
    AttributeName=generated_at,AttributeType=S \
  --key-schema \
    AttributeName=location_id,KeyType=HASH \
    AttributeName=generated_at,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:8000
```

3. `env.json` を更新してローカルDynamoDBを使用：

```json
{
  "ApiHandlerFunction": {
    "AWS_SAM_LOCAL": "true",
    "DYNAMODB_ENDPOINT": "http://host.docker.internal:8000"
  }
}
```

## 🔧 トラブルシューティング

### ポート競合

```bash
# 使用中のポートを確認
lsof -i :3000

# 別のポートで起動
sam local start-api --port 3001
```

### Dockerの問題

```bash
# Dockerデーモンが起動しているか確認
docker ps

# Dockerをリスタート
# macOS: Docker Desktopを再起動
# Linux: sudo systemctl restart docker
```

### Lambda Layer の問題

```bash
# Layerの依存関係を再インストール
rm -rf layers/dependencies/python
pip install -r layers/dependencies/requirements.txt -t layers/dependencies/python/
```

## 📚 参考コマンド

```bash
# すべてのターゲットを表示
make help

# クリーンビルド
make clean build

# 特定の環境でテスト
make local-api ENV=staging
```
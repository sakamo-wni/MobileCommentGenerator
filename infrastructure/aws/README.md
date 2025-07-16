# AWS Lambda Infrastructure

Weather Comment GeneratorのAWS Lambdaサーバーレスインフラストラクチャです。

## 🏗️ アーキテクチャ

- **API Gateway** → **Lambda** → **SQS** → **Lambda** → **DynamoDB**
- 非同期処理によるスケーラブルな設計
- Step Functionsによるワークフローオーケストレーション
- EventBridgeによる定期的なキャッシュウォーミング

## 📁 ディレクトリ構造

```
infrastructure/aws/
├── lambda/                    # Lambda関数
│   ├── api_handler/          # APIリクエストハンドラ
│   ├── comment_processor/    # コメント生成処理
│   ├── weather_fetcher/      # 天気データ取得
│   └── cache_warmer/         # キャッシュウォーマー
├── statemachine/             # Step Functions定義
│   └── comment_generation.asl.yaml
├── scripts/                  # デプロイ・管理スクリプト
│   └── load_initial_data.py  # 初期データロード
├── template.yaml             # SAMテンプレート
├── deploy.sh                 # デプロイスクリプト
├── DEPLOYMENT.md            # 詳細なデプロイガイド
└── architecture.md          # アーキテクチャ設計書
```

## 🚀 クイックスタート

### 1. 前提条件
- AWS CLI設定済み
- SAM CLI インストール済み
- Python 3.11
- Docker Desktop

### 2. APIキー設定
```bash
aws secretsmanager create-secret \
  --name weather-comment-generator/api-keys \
  --secret-string '{"WXTECH_API_KEY":"your-key"}'
```

### 3. デプロイ
```bash
# 開発環境
./deploy.sh dev

# 本番環境
./deploy.sh prod
```

### 4. 初期データ投入
```bash
python scripts/load_initial_data.py \
  --stack-name weather-comment-generator-dev \
  --locations-csv ../../data/locations.csv
```

## 📊 主要コンポーネント

### Lambda関数

| 関数名 | 役割 | トリガー |
|--------|------|----------|
| api_handler | APIリクエスト処理 | API Gateway |
| comment_processor | コメント生成 | SQS |
| weather_fetcher | 天気データ取得 | Step Functions |
| cache_warmer | キャッシュ更新 | EventBridge (1時間毎) |

### DynamoDBテーブル

| テーブル | 用途 | キー |
|----------|------|------|
| comments | 生成済みコメント | location_id (PK), generated_at (SK) |
| weather-cache | 天気データキャッシュ | location_id (PK), forecast_time (SK) |
| locations | 地点マスタ | location_id (PK) |

## 🔧 設定

### 環境変数
- `ENVIRONMENT`: 環境名 (dev/staging/prod)
- `LOG_LEVEL`: ログレベル (INFO/DEBUG)
- `POWERTOOLS_SERVICE_NAME`: サービス名

### パフォーマンス設定
- Lambda同時実行数制限
- SQSバッチサイズ
- DynamoDB読み書きキャパシティ

## 📈 モニタリング

- CloudWatch Logs: 各Lambda関数のログ
- CloudWatch Metrics: パフォーマンスメトリクス
- X-Ray: 分散トレーシング
- CloudWatch Alarms: エラー通知

## 🔒 セキュリティ

- API Gateway: APIキー認証
- Secrets Manager: APIキー管理
- IAM: 最小権限の原則
- S3: パブリックアクセスブロック

## 📝 ドキュメント

- [デプロイガイド](./DEPLOYMENT.md) - 詳細なデプロイ手順
- [アーキテクチャ設計](./architecture.md) - システム設計の詳細

## 🤝 開発ガイド

### ローカルテスト
```bash
# SAMローカルAPI起動
sam local start-api

# Lambda関数の個別テスト
sam local invoke ApiHandlerFunction -e events/api_request.json
```

### デバッグ
```bash
# ログの確認
aws logs tail /aws/lambda/weather-comment-generator-dev-api-handler --follow
```
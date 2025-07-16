# AWS Lambda デプロイメントガイド

このドキュメントでは、Weather Comment GeneratorをAWS Lambdaにデプロイする手順を説明します。

## 📋 前提条件

### 必須ツール
- AWS CLI v2 (設定済み)
- SAM CLI v1.100+
- Python 3.11
- Docker Desktop
- Node.js 18+ (GitHub Actions用)

### AWSアカウント要件
- Lambda、DynamoDB、API Gateway、S3の使用権限
- AWS Secrets Managerへのアクセス権限
- CloudFormationスタック作成権限

## 🏗️ アーキテクチャ概要

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│ API Gateway │────▶│   Lambda    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                         ┌─────────────┐
                                         │     SQS     │
                                         └─────────────┘
                                               │
                                               ▼
                                         ┌─────────────┐
                                         │   Lambda    │
                                         │ (Processor) │
                                         └─────────────┘
                                               │
                    ┌──────────────────────────┴──────────────────────────┐
                    ▼                          ▼                          ▼
              ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
              │  DynamoDB   │          │  DynamoDB   │          │  DynamoDB   │
              │ (Comments)  │          │(Weather Cache)│         │ (Locations) │
              └─────────────┘          └─────────────┘          └─────────────┘
```

## 🚀 デプロイ手順

### 1. APIキーの設定

AWS Secrets Managerにアプリケーション用のAPIキーを設定します：

```bash
# シークレットの作成
aws secretsmanager create-secret \
  --name weather-comment-generator/api-keys \
  --description "API keys for Weather Comment Generator" \
  --secret-string '{
    "WXTECH_API_KEY": "your-wxtech-api-key",
    "OPENAI_API_KEY": "your-openai-api-key",
    "GEMINI_API_KEY": "your-gemini-api-key",
    "ANTHROPIC_API_KEY": "your-anthropic-api-key"
  }' \
  --region ap-northeast-1
```

### 2. ローカルでのビルドとテスト

```bash
# プロジェクトルートに移動
cd /path/to/MobileCommentGenerator

# インフラストラクチャディレクトリに移動
cd infrastructure/aws

# SAMアプリケーションのビルド
sam build --use-container

# ローカルでのテスト（オプション）
sam local start-api

# 別のターミナルでテスト
curl http://localhost:3000/health
```

### 3. デプロイの実行

#### 開発環境へのデプロイ

```bash
# デプロイスクリプトを使用
chmod +x deploy.sh
./deploy.sh dev

# または直接SAMコマンドを使用
sam deploy \
  --stack-name weather-comment-generator-dev \
  --s3-bucket your-deployment-bucket \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --parameter-overrides Environment=dev \
  --region ap-northeast-1
```

#### 本番環境へのデプロイ

```bash
# 本番環境用の設定でデプロイ
./deploy.sh prod
```

### 4. 初期データのロード

デプロイ後、地点データをDynamoDBにロードします：

```bash
# スクリプトディレクトリに移動
cd scripts

# 初期データのロード
python load_initial_data.py \
  --stack-name weather-comment-generator-dev \
  --locations-csv ../../data/locations.csv \
  --output-dir ./output

# 人気地点リストをS3にアップロード
aws s3 cp output/popular_locations.json \
  s3://weather-comment-generator-config-{account-id}/config/popular_locations.json
```

## 🔧 設定とカスタマイズ

### 環境変数

各Lambda関数で使用される主な環境変数：

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `DYNAMODB_COMMENTS_TABLE` | コメントテーブル名 | `weather-comment-generator-dev-comments` |
| `DYNAMODB_WEATHER_CACHE_TABLE` | 天気キャッシュテーブル名 | `weather-comment-generator-dev-weather-cache` |
| `DYNAMODB_LOCATIONS_TABLE` | 地点テーブル名 | `weather-comment-generator-dev-locations` |
| `SQS_QUEUE_URL` | SQSキューURL | `https://sqs.ap-northeast-1.amazonaws.com/...` |
| `SECRETS_ARN` | Secrets Manager ARN | `arn:aws:secretsmanager:ap-northeast-1:...` |

### Lambda関数の設定

`template.yaml`で各Lambda関数の設定を調整できます：

```yaml
MemorySize: 512  # メモリサイズ (MB)
Timeout: 30      # タイムアウト (秒)
ReservedConcurrentExecutions: 5  # 同時実行数制限
```

### API Gatewayの設定

APIの使用制限とスロットリング：

```yaml
Quota:
  Limit: 10000   # 1日あたりのAPIコール数
  Period: DAY
Throttle:
  BurstLimit: 100  # バーストリミット
  RateLimit: 50    # レートリミット（リクエスト/秒）
```

## 📊 モニタリング

### CloudWatch ダッシュボード

デプロイ後、以下のメトリクスを監視できます：

- Lambda関数の実行時間と成功率
- API Gatewayのリクエスト数とレイテンシ
- DynamoDBの読み書きキャパシティ
- SQSキューの長さ

### アラーム

以下のアラームが自動的に設定されます：

- API エラー率が閾値を超えた場合
- DLQにメッセージが入った場合
- Lambda関数のタイムアウト

## 🧪 動作確認

### ヘルスチェック

```bash
# API URLを取得
API_URL=$(aws cloudformation describe-stacks \
  --stack-name weather-comment-generator-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

# ヘルスチェック
curl -X GET "$API_URL/health"
```

### コメント生成リクエスト

```bash
# APIキーを取得
API_KEY=$(aws apigateway get-api-keys \
  --query "items[?name=='weather-comment-generator-dev-api-key'].id" \
  --output text | xargs -I {} aws apigateway get-api-key \
  --api-key {} --include-value --query 'value' --output text)

# コメント生成リクエスト
curl -X POST "$API_URL/generate" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "関東_東京",
    "generation_params": {
      "comment_type": "general",
      "tone": "friendly"
    }
  }'
```

## 🔄 CI/CD パイプライン

GitHub Actionsを使用した自動デプロイ：

### 必要なGitHub Secrets

以下のシークレットをGitHubリポジトリに設定：

- `AWS_DEPLOY_ROLE_ARN`: デプロイ用IAMロールのARN
- `SAM_DEPLOYMENT_BUCKET`: SAMデプロイ用S3バケット名
- `SLACK_WEBHOOK`: (オプション) Slack通知用Webhook URL

### デプロイフロー

1. `main`ブランチへのプッシュで本番環境へ自動デプロイ
2. `develop`ブランチへのプッシュでステージング環境へ自動デプロイ
3. PRでテストを実行
4. 手動デプロイも可能（workflow_dispatch）

## 🛠️ トラブルシューティング

### よくある問題と解決方法

#### 1. Lambda関数のタイムアウト

```bash
# タイムアウト時間を増やす
aws lambda update-function-configuration \
  --function-name weather-comment-generator-dev-comment-processor \
  --timeout 300
```

#### 2. DynamoDBスロットリング

```bash
# オンデマンドモードに切り替え
aws dynamodb update-table \
  --table-name weather-comment-generator-dev-comments \
  --billing-mode PAY_PER_REQUEST
```

#### 3. APIキーの問題

```bash
# シークレットの更新
aws secretsmanager update-secret \
  --secret-id weather-comment-generator/api-keys \
  --secret-string '{"WXTECH_API_KEY": "new-key", ...}'
```

## 📝 メンテナンス

### ログの確認

```bash
# Lambda関数のログを確認
aws logs tail /aws/lambda/weather-comment-generator-dev-api-handler --follow

# 特定の時間範囲のログを取得
aws logs filter-log-events \
  --log-group-name /aws/lambda/weather-comment-generator-dev-comment-processor \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### コスト最適化

1. **Lambda予約済み同時実行数**の調整
2. **DynamoDB**のオンデマンド/プロビジョンドモードの選択
3. **S3ライフサイクルポリシー**によるログのアーカイブ
4. **CloudWatch Logs**の保持期間設定

## 🔒 セキュリティベストプラクティス

1. **最小権限の原則**: 各Lambda関数に必要最小限の権限のみ付与
2. **シークレット管理**: APIキーはSecrets Managerで管理
3. **API Gateway**: APIキー認証とレート制限を設定
4. **VPC設定**: 必要に応じてLambda関数をVPC内に配置
5. **監査ログ**: CloudTrailでAPIコールを記録

## 📚 参考リンク

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [API Gateway Security](https://docs.aws.amazon.com/apigateway/latest/developerguide/security.html)
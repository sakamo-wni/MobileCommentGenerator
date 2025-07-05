# 🚀 AWSデプロイメントガイド

## 📋 概要

本ガイドでは AWS 上に MobileCommentGenerator システムを展開するための代表的な手順を説明します。ECS(Fargate) を軸にしつつ、EC2 での代替運用も視野に入れたロードマップをまとめました。

## 1. 初期準備

### AWS アカウントとIAM設定
- AWS アカウントを作成し、必要な IAM ユーザー／ロールを整備
- AWS CLI をインストールして `aws configure` で認証情報を設定
- ネットワークは VPC 内にパブリック／プライベートサブネットを作成し、セキュリティグループで HTTP/HTTPS ポートを開放

## 2. Docker イメージ管理(ECR)

### リポジトリ作成とイメージのプッシュ
- `aws ecr create-repository` でリポジトリを作成
- Docker イメージをビルドし、以下のコマンド例で ECR へ push

```bash
aws ecr get-login-password --region <REGION> | \
  docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com
docker build -t mobile-comment-generator .
docker tag mobile-comment-generator:latest \
  <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/mobile-comment-generator:latest
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/mobile-comment-generator:latest
```

## 3. ECS(Fargate) クラスタ構築

### クラスタとサービスの設定
- クラスタを作成し、タスク定義で上記イメージを指定
- サービスを作成して Application Load Balancer と接続
- CloudWatch Logs へログを送信し、Auto Scaling を有効化

## 4. GitHub Actions での CI/CD

### 自動デプロイメントパイプライン
- PR では `lint` と `test` を実行
- `main` マージ時に Docker ビルド → ECR push → ECS サービス更新を自動化
- 例: `aws ecs update-service --cluster <cluster> --service <service> --force-new-deployment`

## 5. EC2 デプロイ (代替案)

### Auto Scaling Group による運用
- Auto Scaling Group + Launch Template を用意し、起動時スクリプトで ECR からイメージを pull して `docker run` で起動
- ALB で複数インスタンスにトラフィックを分散し、CloudWatch Agent でメトリクス／ログを収集

## 6. 運用と周辺サービス

### モニタリングとデータ永続化
- CloudWatch Alarms で CPU や応答コードを監視し、必要に応じて通知
- データ永続化が必要な場合は RDS や DynamoDB をプライベートサブネットに配置
- S3 へのファイル保存や Secrets Manager での機密情報管理も検討する

## 🛠️ 詳細設定例

### タスク定義の例 (task-definition.json)
```json
{
  "family": "mobile-comment-generator",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api-server",
      "image": "<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/mobile-comment-generator:latest",
      "portMappings": [
        {
          "containerPort": 3001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:<REGION>:<ACCOUNT_ID>:secret:openai-api-key"
        },
        {
          "name": "GEMINI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:<REGION>:<ACCOUNT_ID>:secret:gemini-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mobile-comment-generator",
          "awslogs-region": "<REGION>",
          "awslogs-stream-prefix": "api"
        }
      }
    }
  ]
}
```

### ALB ヘルスチェック設定
```yaml
HealthCheckPath: /health
HealthCheckProtocol: HTTP
HealthCheckIntervalSeconds: 30
HealthCheckTimeoutSeconds: 5
HealthyThresholdCount: 2
UnhealthyThresholdCount: 3
```

## 📊 コスト最適化

### 推奨構成
- **開発環境**: t3.micro EC2 インスタンス
- **本番環境**: Fargate (0.5 vCPU, 1GB メモリ)
- **オートスケーリング**: 平均CPU使用率 70% でスケールアウト

### 月額コスト目安 (東京リージョン)
- Fargate: 約 $20-50/月
- ALB: 約 $20/月
- ECR: 約 $5/月
- CloudWatch: 約 $10/月

## 🔐 セキュリティベストプラクティス

1. **シークレット管理**
   - API キーは Secrets Manager で管理
   - IAM ロールは最小権限の原則に従う

2. **ネットワーク設計**
   - プライベートサブネットでコンテナを実行
   - ALB のみパブリックサブネットに配置

3. **監査とログ**
   - CloudTrail で API 呼び出しを記録
   - VPC Flow Logs でネットワークトラフィックを監視

上記を基に環境を整備すれば、可用性とスケーラビリティを両立した AWS 運用が可能になります。

## 📚 関連ドキュメント

- [README](../README.md) - プロジェクト概要
- [アーキテクチャ](./architecture.md) - システム構成
- [フロントエンド](./frontend-guide.md) - Nuxt.js/React実装ガイド
- [API](./api-guide.md) - API設定と使用方法
- [開発](./development.md) - 開発ツールとテスト
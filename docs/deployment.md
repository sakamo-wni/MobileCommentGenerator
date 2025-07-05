# AWSデプロイメントガイド

## 🚀 AWSデプロイメントロードマップ

以下は AWS 上に本システムを展開するための代表的な手順です。ECS(Fargate) を軸にしつつ、EC2 での代替運用も視野に入れたロードマップをまとめました。

## 1. 初期準備

### AWS アカウントとIAM設定
- AWS アカウントを作成し、必要な IAM ユーザー／ロールを整備
- AWS CLI をインストールして `aws configure` で認証情報を設定
- 必要な権限:
  - ECR (Elastic Container Registry)
  - ECS (Elastic Container Service)
  - EC2
  - VPC
  - CloudWatch
  - S3 (オプション)
  - Secrets Manager (オプション)

### ネットワーク構成
- VPC 内にパブリック／プライベートサブネットを作成
- セキュリティグループで HTTP/HTTPS ポートを開放
- NAT Gateway（プライベートサブネット用）の設定

## 2. Docker イメージ管理(ECR)

### リポジトリ作成
```bash
aws ecr create-repository --repository-name mobile-comment-generator --region <REGION>
```

### Docker イメージのビルドとプッシュ
```bash
# ECRへのログイン
aws ecr get-login-password --region <REGION> | \
  docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com

# イメージのビルド
docker build -t mobile-comment-generator .

# タグ付け
docker tag mobile-comment-generator:latest \
  <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/mobile-comment-generator:latest

# ECRへプッシュ
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/mobile-comment-generator:latest
```

## 3. ECS(Fargate) クラスタ構築

### クラスタ作成
```bash
aws ecs create-cluster --cluster-name mobile-comment-cluster
```

### タスク定義
```json
{
  "family": "mobile-comment-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "mobile-comment-container",
      "image": "<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/mobile-comment-generator:latest",
      "portMappings": [
        {
          "containerPort": 3001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "API_PORT",
          "value": "3001"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:<REGION>:<ACCOUNT_ID>:secret:openai-api-key"
        },
        {
          "name": "WXTECH_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:<REGION>:<ACCOUNT_ID>:secret:wxtech-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mobile-comment",
          "awslogs-region": "<REGION>",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### サービス作成
- Application Load Balancer との接続
- Auto Scaling の設定
- ヘルスチェックの設定

## 4. GitHub Actions での CI/CD

`.github/workflows/deploy.yml`:
```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: mobile-comment-generator
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster mobile-comment-cluster \
            --service mobile-comment-service \
            --force-new-deployment
```

## 5. EC2 デプロイ (代替案)

### Auto Scaling Group設定
```bash
# Launch Template作成
aws ec2 create-launch-template \
  --launch-template-name mobile-comment-template \
  --launch-template-data file://launch-template.json
```

### 起動時スクリプト (User Data)
```bash
#!/bin/bash
# Docker インストール
yum update -y
amazon-linux-extras install docker -y
service docker start
usermod -a -G docker ec2-user

# ECRからイメージをpull
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin <ECR_URI>
docker pull <ECR_URI>/mobile-comment-generator:latest

# コンテナ起動
docker run -d \
  --name mobile-comment \
  -p 80:3001 \
  --restart always \
  -e OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id openai-api-key --query SecretString --output text) \
  -e WXTECH_API_KEY=$(aws secretsmanager get-secret-value --secret-id wxtech-api-key --query SecretString --output text) \
  <ECR_URI>/mobile-comment-generator:latest
```

## 6. 運用と周辺サービス

### モニタリング
- CloudWatch Alarms で CPU や応答コードを監視
- CloudWatch Logs でアプリケーションログを収集
- X-Ray でトレーシング（オプション）

### データ永続化
- RDS: リレーショナルデータベース
- DynamoDB: NoSQLデータベース
- S3: ファイルストレージ
- EFS: 共有ファイルシステム

### セキュリティ
- Secrets Manager: API キーなど機密情報の管理
- Systems Manager Parameter Store: 設定値の管理
- WAF: Web Application Firewall
- Certificate Manager: SSL証明書の管理

### スケーリング
- ECS Service Auto Scaling
- EC2 Auto Scaling Groups
- RDS Read Replicas
- CloudFront CDN（静的コンテンツ配信）

## 7. 推奨構成

### 最小構成（開発・テスト環境）
- ECS Fargate: 1タスク（0.5 vCPU, 1GB メモリ）
- ALB: 単一AZ
- RDS: t3.micro（単一AZ）
- 推定月額: $50-100

### 本番環境構成
- ECS Fargate: 2-4タスク（1 vCPU, 2GB メモリ）
- ALB: マルチAZ
- RDS: t3.small（マルチAZ）
- CloudFront
- 推定月額: $200-400

### 高可用性構成
- ECS Fargate: 4-8タスク（2 vCPU, 4GB メモリ）
- ALB: マルチAZ + WAF
- RDS: m5.large（マルチAZ + Read Replica）
- ElastiCache
- CloudFront + S3
- 推定月額: $500-1000

## 8. デプロイ前チェックリスト

- [ ] 環境変数の設定完了
- [ ] セキュリティグループの適切な設定
- [ ] ヘルスチェックエンドポイントの実装
- [ ] ログ出力の設定
- [ ] バックアップ戦略の策定
- [ ] 監視アラートの設定
- [ ] ロールバック手順の文書化
- [ ] 負荷テストの実施

## 9. トラブルシューティング

### よくある問題と解決方法

1. **コンテナが起動しない**
   - CloudWatch Logs でエラーログを確認
   - タスク定義のメモリ/CPU設定を確認
   - 環境変数やシークレットの設定を確認

2. **ALBヘルスチェック失敗**
   - ヘルスチェックパスとポートを確認
   - セキュリティグループの設定を確認
   - アプリケーションの起動時間を考慮

3. **パフォーマンス問題**
   - CloudWatch メトリクスでリソース使用率を確認
   - Auto Scaling の閾値を調整
   - データベースのスロークエリを分析

上記を基に環境を整備すれば、可用性とスケーラビリティを両立した AWS 運用が可能になります。
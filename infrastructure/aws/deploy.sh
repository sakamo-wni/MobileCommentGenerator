#!/bin/bash
set -e

# デプロイスクリプト for AWS SAM

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 環境変数のチェック
ENVIRONMENT=${1:-dev}
STACK_NAME="weather-comment-generator-${ENVIRONMENT}"
REGION=${AWS_REGION:-ap-northeast-1}
S3_BUCKET=${SAM_S3_BUCKET:-"weather-comment-generator-deployment-${ENVIRONMENT}"}

echo -e "${GREEN}🚀 Deploying Weather Comment Generator to AWS Lambda${NC}"
echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Stack Name: ${YELLOW}${STACK_NAME}${NC}"
echo -e "Region: ${YELLOW}${REGION}${NC}"

# 必要なツールの確認
command -v sam >/dev/null 2>&1 || { echo -e "${RED}SAM CLI is required but not installed.${NC}" >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo -e "${RED}AWS CLI is required but not installed.${NC}" >&2; exit 1; }

# S3バケットの作成（存在しない場合）
echo -e "\n${GREEN}📦 Checking S3 deployment bucket...${NC}"
if ! aws s3 ls "s3://${S3_BUCKET}" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "S3 bucket ${S3_BUCKET} already exists"
else
    echo "Creating S3 bucket ${S3_BUCKET}..."
    if [ "${REGION}" = "us-east-1" ]; then
        aws s3 mb "s3://${S3_BUCKET}"
    else
        aws s3 mb "s3://${S3_BUCKET}" --region "${REGION}"
    fi
fi

# Lambda Layerの準備
echo -e "\n${GREEN}📚 Preparing Lambda Layer...${NC}"
mkdir -p layers/dependencies/python

# requirements.txtの作成
cat > layers/dependencies/requirements.txt << EOF
boto3>=1.26.0
aws-lambda-powertools>=2.25.0
pydantic>=2.5.0
httpx>=0.25.0
EOF

# 依存関係のインストール
pip install -r layers/dependencies/requirements.txt -t layers/dependencies/python/ --platform manylinux2014_aarch64 --only-binary=:all:

# プロジェクトコードのコピー
echo -e "\n${GREEN}📄 Copying project code...${NC}"
for func in api_handler comment_processor weather_fetcher cache_warmer; do
    if [ -d "lambda/${func}" ]; then
        # srcディレクトリをLambda関数にコピー
        cp -r ../../src "lambda/${func}/"
        # 不要なファイルを削除
        find "lambda/${func}/src" -name "*.pyc" -delete
        find "lambda/${func}/src" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
done

# SAM Build
echo -e "\n${GREEN}🔨 Building SAM application...${NC}"
sam build \
    --use-container \
    --parallel \
    --cached

# SAM Deploy
echo -e "\n${GREEN}🚀 Deploying to AWS...${NC}"
sam deploy \
    --stack-name "${STACK_NAME}" \
    --s3-bucket "${S3_BUCKET}" \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --parameter-overrides \
        Environment="${ENVIRONMENT}" \
    --no-fail-on-empty-changeset \
    --region "${REGION}"

# デプロイ結果の表示
echo -e "\n${GREEN}✅ Deployment completed!${NC}"
echo -e "\n${YELLOW}📊 Stack Outputs:${NC}"
aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs' \
    --output table

# APIキーの取得
echo -e "\n${YELLOW}🔑 API Key:${NC}"
API_KEY=$(aws apigateway get-api-keys \
    --region "${REGION}" \
    --query "items[?name=='${STACK_NAME}-api-key'].id" \
    --output text)

if [ -n "${API_KEY}" ]; then
    aws apigateway get-api-key \
        --api-key "${API_KEY}" \
        --region "${REGION}" \
        --include-value \
        --query 'value' \
        --output text
else
    echo "API Key not found. You may need to create one manually."
fi

# クリーンアップ
echo -e "\n${GREEN}🧹 Cleaning up build artifacts...${NC}"
rm -rf .aws-sam/
rm -rf layers/dependencies/python/

echo -e "\n${GREEN}🎉 Deployment complete!${NC}"
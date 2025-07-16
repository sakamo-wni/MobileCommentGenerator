.PHONY: build deploy test local-api local-invoke clean validate sync-code

# デフォルト環境
ENV ?= dev

# SAMビルド
build:
	sam build --use-container --parallel --cached

# バリデーション
validate:
	sam validate --lint

# デプロイ
deploy: build
	./deploy.sh $(ENV)

# ローカルAPI起動
local-api: build
	sam local start-api --port 3000 --env-vars env.json

# Lambda関数の個別実行
invoke-api-handler: build
	sam local invoke ApiHandlerFunction -e events/api_generate_request.json --env-vars env.json

invoke-weather-fetcher: build
	sam local invoke WeatherFetcherFunction -e events/weather_fetcher_request.json --env-vars env.json

invoke-comment-processor: build
	sam local invoke CommentProcessorFunction -e events/sqs_comment_generation.json --env-vars env.json

invoke-cache-warmer: build
	sam local invoke CacheWarmerFunction -e events/cache_warmer_event.json --env-vars env.json

# ローカルDynamoDBの起動
local-dynamodb:
	docker run -p 8000:8000 amazon/dynamodb-local

# テスト
test-unit:
	cd ../.. && pytest tests/test_lambda_handlers.py -v

test-integration: local-api
	cd ../.. && pytest tests/test_lambda_integration.py -v

# ログの確認
logs-api:
	aws logs tail /aws/lambda/weather-comment-generator-$(ENV)-api-handler --follow

logs-processor:
	aws logs tail /aws/lambda/weather-comment-generator-$(ENV)-comment-processor --follow

logs-fetcher:
	aws logs tail /aws/lambda/weather-comment-generator-$(ENV)-weather-fetcher --follow

logs-warmer:
	aws logs tail /aws/lambda/weather-comment-generator-$(ENV)-cache-warmer --follow

# srcディレクトリを各Lambda関数にコピー
sync-code:
	@echo "Syncing source code to Lambda functions..."
	@for func in api_handler comment_processor weather_fetcher cache_warmer; do \
		echo "Copying src to lambda/$$func/"; \
		rm -rf lambda/$$func/src; \
		cp -r ../../src lambda/$$func/; \
	done

# クリーンアップ
clean:
	rm -rf .aws-sam/
	rm -rf layers/dependencies/python/
	find lambda -name "src" -type d -exec rm -rf {} + 2>/dev/null || true
	find lambda -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 依存関係の更新
update-deps:
	pip-compile layers/dependencies/requirements.in -o layers/dependencies/requirements.txt

# スタック情報の表示
info:
	@echo "Environment: $(ENV)"
	@echo "Stack Name: weather-comment-generator-$(ENV)"
	@echo ""
	@aws cloudformation describe-stacks \
		--stack-name weather-comment-generator-$(ENV) \
		--query 'Stacks[0].Outputs' \
		--output table 2>/dev/null || echo "Stack not deployed"

# ヘルプ
help:
	@echo "Usage: make [target] [ENV=dev|staging|prod]"
	@echo ""
	@echo "Targets:"
	@echo "  build              - SAMアプリケーションをビルド"
	@echo "  validate           - テンプレートの検証"
	@echo "  deploy             - 指定環境にデプロイ"
	@echo "  local-api          - ローカルAPIサーバー起動"
	@echo "  invoke-*           - Lambda関数の個別実行"
	@echo "  logs-*             - CloudWatch Logsの確認"
	@echo "  sync-code          - ソースコードを同期"
	@echo "  clean              - ビルド成果物を削除"
	@echo "  info               - スタック情報を表示"
	@echo ""
	@echo "Examples:"
	@echo "  make build"
	@echo "  make deploy ENV=staging"
	@echo "  make local-api"
	@echo "  make invoke-api-handler"
#!/bin/bash

# FastAPI サーバー起動スクリプト
echo "Starting FastAPI server..."

# .envファイルを読み込む
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found"
fi

# 必要な環境変数をチェック
if [ -z "$OPENAI_API_KEY" ] && [ -z "$GEMINI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Warning: No LLM API keys found. Please set at least one of:"
    echo "  - OPENAI_API_KEY"
    echo "  - GEMINI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"
fi

if [ -z "$WXTECH_API_KEY" ]; then
    echo "Warning: WXTECH_API_KEY not found. Weather data will not be available."
fi

# 依存関係をチェック
echo "Checking Python dependencies..."
pip install -q fastapi uvicorn python-dotenv

echo "Starting FastAPI server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"

# FastAPIサーバーを起動
python api_server.py
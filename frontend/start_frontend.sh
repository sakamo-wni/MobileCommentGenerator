#!/bin/bash

# Nuxt.js フロントエンド起動スクリプト
echo "Starting Nuxt.js frontend..."

cd frontend

# パッケージがインストールされているかチェック
if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install
fi

# フロントエンドを起動
echo "Starting development server..."
npm run dev
# 📡 API設定と使用方法

## 📋 概要

MobileCommentGeneratorは、FastAPIを使用したRESTful APIサーバーを提供しています。このAPIは、天気予報データの取得、コメント生成、履歴管理などの機能を提供します。

## 🔑 API設定

### 必須環境変数

`.env`ファイルでLLMプロバイダーのAPIキーを設定:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 天気予報データ
WXTECH_API_KEY=your_wxtech_api_key_here

# AWS（オプション）
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

## 🚀 APIサーバー起動

### 開発環境
```bash
# uvを使用（推奨）
uv run ./start_api.sh

# または直接実行
uv run python api_server.py

# ポート指定
uv run python api_server.py --port 3001
```

### 本番環境
```bash
# Gunicornを使用
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:3001
```

## 📍 APIエンドポイント

### ヘルスチェック
```http
GET /health
```

**レスポンス例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 地点一覧取得
```http
GET /api/locations
```

**レスポンス例:**
```json
[
  {
    "id": "tokyo",
    "name": "東京",
    "prefecture": "東京都",
    "region": "関東",
    "latitude": 35.6762,
    "longitude": 139.6503
  },
  {
    "id": "osaka",
    "name": "大阪",
    "prefecture": "大阪府",
    "region": "関西",
    "latitude": 34.6937,
    "longitude": 135.5023
  }
]
```

### コメント生成
```http
POST /api/generate
```

**リクエストボディ:**
```json
{
  "location": {
    "id": "tokyo",
    "name": "東京",
    "prefecture": "東京都",
    "region": "関東"
  },
  "llmProvider": "openai",
  "temperature": 0.7,
  "targetDateTime": "2024-01-01T09:00:00+09:00"
}
```

**レスポンス例:**
```json
{
  "id": "gen_12345",
  "comment": "明日は晴れやか",
  "adviceComment": "おでかけ日和です",
  "weather": {
    "current": {
      "temperature": 15.5,
      "humidity": 60,
      "pressure": 1013,
      "windSpeed": 3.5,
      "windDirection": "北東",
      "description": "晴れ",
      "icon": "01d"
    },
    "forecast": [
      {
        "datetime": "2024-01-01T12:00:00+09:00",
        "temperature": {
          "min": 10,
          "max": 18
        },
        "humidity": 55,
        "precipitation": 0,
        "description": "晴れ",
        "icon": "01d"
      }
    ],
    "trend": {
      "trend": "stable",
      "confidence": 0.85,
      "description": "安定した晴天が続く見込み"
    }
  },
  "timestamp": "2024-01-01T08:00:00Z",
  "confidence": 0.92,
  "location": {
    "id": "tokyo",
    "name": "東京",
    "prefecture": "東京都",
    "region": "関東"
  },
  "settings": {
    "location": {...},
    "llmProvider": "openai",
    "temperature": 0.7,
    "targetDateTime": "2024-01-01T09:00:00+09:00"
  }
}
```

### 生成履歴取得
```http
GET /api/history?limit=10
```

**クエリパラメータ:**
- `limit`: 取得する履歴の件数（デフォルト: 10）

**レスポンス例:**
```json
[
  {
    "id": "gen_12345",
    "comment": "明日は晴れやか",
    "adviceComment": "おでかけ日和です",
    "weather": {...},
    "timestamp": "2024-01-01T08:00:00Z",
    "confidence": 0.92,
    "location": {...},
    "settings": {...}
  }
]
```

### 天気データ取得
```http
GET /api/weather/{location_id}
```

**パスパラメータ:**
- `location_id`: 地点ID（例: tokyo）

**レスポンス例:**
```json
{
  "current": {
    "temperature": 15.5,
    "humidity": 60,
    "pressure": 1013,
    "windSpeed": 3.5,
    "windDirection": "北東",
    "description": "晴れ",
    "icon": "01d"
  },
  "forecast": [...],
  "trend": {
    "trend": "stable",
    "confidence": 0.85,
    "description": "安定した晴天が続く見込み"
  }
}
```

## 💻 プログラマティック使用

### Python
```python
from src.workflows.comment_generation_workflow import run_comment_generation
from datetime import datetime

# 単一地点のコメント生成
result = run_comment_generation(
    location_name="東京",
    target_datetime=datetime.now(),
    llm_provider="openai"
)

print(f"生成コメント: {result['final_comment']}")
print(f"アドバイス: {result['advice_comment']}")
```

### JavaScript/TypeScript
```typescript
import { createApiClient } from '@mobile-comment-generator/shared/api';

const client = createApiClient('http://localhost:3001');

// コメント生成
const result = await client.generateComment({
  location: {
    id: 'tokyo',
    name: '東京',
    prefecture: '東京都',
    region: '関東'
  },
  llmProvider: 'openai',
  temperature: 0.7
});

console.log('生成コメント:', result.comment);
console.log('アドバイス:', result.adviceComment);
```

### cURL
```bash
# 地点一覧取得
curl http://localhost:3001/api/locations

# コメント生成
curl -X POST http://localhost:3001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "location": {
      "id": "tokyo",
      "name": "東京",
      "prefecture": "東京都",
      "region": "関東"
    },
    "llmProvider": "openai"
  }'
```

## 🔒 認証・認可

現在のバージョンでは認証機能は実装されていませんが、本番環境では以下の実装を推奨します：

### 推奨セキュリティ対策
1. **APIキー認証**: ヘッダーベースのAPIキー認証
2. **レート制限**: IP/APIキーごとのリクエスト制限
3. **CORS設定**: 許可されたオリジンのみアクセス可能
4. **HTTPS**: SSL/TLS証明書によるセキュア通信

### CORS設定例
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 エラーハンドリング

### エラーレスポンス形式
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "必須パラメータが不足しています",
    "details": {
      "missing_fields": ["location", "llmProvider"]
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### HTTPステータスコード
- `200 OK`: 正常終了
- `400 Bad Request`: 不正なリクエスト
- `404 Not Found`: リソースが存在しない
- `429 Too Many Requests`: レート制限超過
- `500 Internal Server Error`: サーバーエラー

## 🕑 天気予報時刻の仕様

システムは**翌朝9:00-18:00（JST）の時間帯**から天気に基づいてコメントを生成します。

### 天気の優先順位ルール

1. **特別に慎重な最優先項目**: 雨、雪、雷の3つ
2. **本日天気の最優先対策**: 重い雨（10mm/h以上）
3. **最高気温35℃以上**: 熱中症警戒
4. **その他**: 最高気温データと湿度

## 🛠️ トラブルシューティング

### よくある問題

1. **APIキーエラー**
   - `.env`ファイルが正しく設定されているか確認
   - 環境変数が読み込まれているか確認

2. **接続エラー**
   - APIサーバーが起動しているか確認
   - ファイアウォール設定を確認

3. **タイムアウトエラー**
   - LLMプロバイダーのレスポンスが遅い場合があります
   - タイムアウト設定を調整してください

## 📚 関連ドキュメント

- [README](../README.md) - プロジェクト概要
- [アーキテクチャ](./architecture.md) - システム構成
- [デプロイメント](./deployment.md) - AWSデプロイメントガイド
- [フロントエンド](./frontend-guide.md) - Nuxt.js/React実装ガイド
- [開発](./development.md) - 開発ツールとテスト
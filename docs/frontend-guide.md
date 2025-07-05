# 🎨 フロントエンド実装ガイド

## 📋 概要

MobileCommentGeneratorは、Nuxt.js 3（Vue版）とReact版の2つのフロントエンド実装を提供しています。両者は共通のAPIとロジックを共有しながら、異なるUIライブラリで実装されています。

## 🏗️ ディレクトリ構成

### モノレポ構成
```
MobileCommentGenerator/
├── frontend/                    # Nuxt.js 3版
├── react-version/              # React版
├── shared/                     # 共通ロジック・型定義
│   ├── types/                  # 共通型定義
│   ├── api/                    # APIクライアント
│   ├── composables/            # 共通ロジック
│   └── utils/                  # 共通ユーティリティ
└── pnpm-workspace.yaml         # pnpmワークスペース設定
```

## 🔧 セットアップ

### 環境構築
```bash
# pnpmのインストール
npm install -g pnpm

# 依存関係のインストール
pnpm install

# 共通パッケージのビルド
pnpm --filter @mobile-comment-generator/shared build
```

### 環境変数設定

**.env.shared**（ルートディレクトリ）:
```bash
# API設定
VITE_API_URL=http://localhost:3001
NUXT_PUBLIC_API_URL=http://localhost:3001

# LLMプロバイダー
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 天気予報API
WXTECH_API_KEY=your_wxtech_api_key_here
```

## 📱 Nuxt.js 3版（Vue）

### ファイル構成

| ファイル | 役割 | 主要機能 |
|---------|------|---------|
| **pages/index.vue** | メインページ | 全体レイアウト・状態管理・API連携機能 |
| **app.vue** | アプリケーション全体のレイアウト | グローバルスタイル・共通レイアウト |
| **components/LocationSelection.vue** | 地点選択コンポーネント | 地域リスト・検索機能・フィルタリング機能 |
| **components/GenerateSettings.vue** | 設定コンポーネント | LLMプロバイダー選択・生成オプション設定 |
| **components/GeneratedComment.vue** | 結果表示コンポーネント | 生成コメント・履歴・コピー機能 |
| **components/WeatherData.vue** | 天気データコンポーネント | 現在・予報天気データ・詳細情報表示 |
| **composables/useApi.ts** | API層 | REST通信・エラーハンドリング・ローディング状態管理 |
| **constants/locations.ts** | 地点データ | 全国地点リスト |
| **constants/regions.ts** | 地域データ | 地域分類・表示項目・カテゴリ分類 |
| **types/index.ts** | 型定義 | API・UI内の型定義 |

### 状態管理
```typescript
// pages/index.vueでの主要状態管理
const selectedLocation = ref<Location | null>(null)
const generatedComment = ref<GeneratedComment | null>(null)
const isGenerating = ref(false)
const error = ref<string | null>(null)
```

### 実行方法
```bash
# 開発サーバー起動（ポート3000）
pnpm dev

# ビルド
pnpm build

# プレビュー
pnpm preview
```

## ⚛️ React版

### プロジェクト構成
```
react-version/
├── src/
│   ├── components/          # UIコンポーネント
│   ├── hooks/              # カスタムフック
│   ├── pages/              # ページコンポーネント
│   ├── styles/             # スタイル定義
│   └── App.tsx             # ルートコンポーネント
└── vite.config.ts          # Vite設定
```

### コンポーネント例

**LocationSelection.tsx**:
```tsx
import React, { useState, useEffect } from 'react';
import { Search, MapPin, Loader2 } from 'lucide-react';
import type { Location } from '@mobile-comment-generator/shared';
import { createWeatherCommentComposable } from '@mobile-comment-generator/shared/composables';

interface LocationSelectionProps {
  selectedLocation: Location | null;
  onLocationChange: (location: Location) => void;
  className?: string;
}

export const LocationSelection: React.FC<LocationSelectionProps> = ({
  selectedLocation,
  onLocationChange,
  className = '',
}) => {
  const [locations, setLocations] = useState<Location[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { getLocations } = createWeatherCommentComposable();

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getLocations();
        setLocations(data);
      } catch (err) {
        setError('地点データの取得に失敗しました');
        console.error('Failed to fetch locations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchLocations();
  }, []);

  // コンポーネントロジック続き...
};
```

### カスタムフック例

**useApi.ts**:
```tsx
import { useState, useCallback } from 'react';
import type { GenerateSettings, GeneratedComment, Location } from '@mobile-comment-generator/shared';
import { createWeatherCommentComposable } from '@mobile-comment-generator/shared/composables';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const composable = createWeatherCommentComposable();

  const generateComment = useCallback(async (
    location: Location,
    settings: Omit<GenerateSettings, 'location'>
  ): Promise<GeneratedComment> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await composable.generateComment(location, settings);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'コメント生成に失敗しました';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [composable]);

  return {
    loading,
    error,
    generateComment,
    clearError: () => setError(null),
  };
};
```

### 実行方法
```bash
# 開発サーバー起動（ポート5173）
pnpm dev:react

# ビルド
pnpm build:react

# プレビュー
pnpm preview:react
```

## 🌐 共通API

### APIクライアント

**shared/src/api/client.ts**:
```typescript
import axios, { AxiosInstance } from 'axios';
import type { Location, GenerateSettings, GeneratedComment, WeatherData } from '../types';

export class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL?: string) {
    const apiUrl = baseURL || process.env.NUXT_PUBLIC_API_URL || process.env.VITE_API_URL || 'http://localhost:3001';
    
    this.client = axios.create({
      baseURL: apiUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async getLocations(): Promise<Location[]> {
    const response = await this.client.get('/api/locations');
    return response.data;
  }

  async generateComment(settings: GenerateSettings): Promise<GeneratedComment> {
    const response = await this.client.post('/api/generate', settings);
    return response.data;
  }

  async getHistory(limit: number = 10): Promise<GeneratedComment[]> {
    const response = await this.client.get('/api/history', {
      params: { limit },
    });
    return response.data;
  }

  async getWeatherData(locationId: string): Promise<WeatherData> {
    const response = await this.client.get(`/api/weather/${locationId}`);
    return response.data;
  }
}
```

### 共通型定義

**shared/src/types/index.ts**:
```typescript
export interface Location {
  id: string;
  name: string;
  prefecture: string;
  region: string;
  latitude?: number;
  longitude?: number;
}

export interface GenerateSettings {
  location: Location;
  llmProvider: 'openai' | 'gemini' | 'anthropic';
  temperature?: number;
  targetDateTime?: string;
}

export interface GeneratedComment {
  id: string;
  comment: string;
  adviceComment?: string;
  weather: WeatherData;
  timestamp: string;
  confidence: number;
  location: Location;
  settings: GenerateSettings;
}

export interface WeatherData {
  current: CurrentWeather;
  forecast: ForecastWeather[];
  trend?: WeatherTrend;
}
```

## 🚀 同時実行

### 開発サーバー同時起動
```bash
# Nuxt.js版とReact版を同時起動
pnpm dev:all

# APIサーバーも含めて全部起動
pnpm dev:all && uv run ./start_api.sh
```

### ポート配置
- **3000番**: Nuxt.js 3フロントエンド
- **5173番**: React版フロントエンド
- **3001番**: FastAPI バックエンド
- **8501番**: Streamlit開発UI

## 🎨 スタイリング

### Nuxt.js版
- Tailwind CSS を使用
- `nuxt.config.ts` で設定

### React版
- Tailwind CSS を使用
- カスタムCSS変数でテーマカラー定義
- ダークモード対応

## 📊 開発ガイドライン

### コンポーネント設計原則

1. **関数コンポーネント + Hooks**
```tsx
// ✅ 推奨
const MyComponent: React.FC<Props> = ({ prop1, prop2 }) => {
  const [state, setState] = useState(initialValue);
  return <div>...</div>;
};
```

2. **TypeScript必須**
```tsx
// ✅ 推奨: 明確な型定義
interface ComponentProps {
  title: string;
  count: number;
  onUpdate: (value: number) => void;
}
```

3. **共通ロジックの活用**
```tsx
// ✅ 推奨: 共通コンポジタブルの使用
import { createWeatherCommentComposable } from '@mobile-comment-generator/shared/composables';
```

### 依存関係管理
```bash
# 新しい依存関係を追加
pnpm --filter frontend add package-name
pnpm --filter @mobile-comment-generator/react-version add package-name

# 共通パッケージを更新
pnpm --filter @mobile-comment-generator/shared build
```

## 🌙 ダークモード

React版は起動時にシステムのテーマを検出し、右上のボタンでライト/ダークを切り替えられます。
色の調整は `react-version/src/index.css` 内の `--app-color-*` 変数を変更してください。

## 📚 関連ドキュメント

- [README](../README.md) - プロジェクト概要
- [アーキテクチャ](./architecture.md) - システム構成
- [デプロイメント](./deployment.md) - AWSデプロイメントガイド
- [API](./api-guide.md) - API設定と使用方法
- [開発](./development.md) - 開発ツールとテスト
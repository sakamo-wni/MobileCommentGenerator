# 🌦️ MobileCommentGenerator

天気予報に基づいて適応的なコメントを生成するAIシステム。LangGraphフレームワークを使用して構築され、過去のコメントデータを活用してコンテキストに応じたコメントを生成します。

## 📁 プロジェクト構成

```
MobileCommentGenerator/
├── src/                                    # バックエンドソースコード
│   ├── workflows/                          # LangGraphワークフロー実装
│   ├── nodes/                              # 各処理ノードの実装
│   ├── llm/                                # LLMプロバイダー統合
│   ├── data/                               # データモデル・管理
│   ├── apis/                               # 外部API統合
│   └── utils/                              # ユーティリティ関数
├── frontend/                               # Nuxt.js 3 フロントエンド（Vue版）
│   ├── pages/                              # ページコンポーネント
│   ├── components/                         # UIコンポーネント
│   ├── composables/                        # Composition API
│   └── nuxt.config.ts                      # Nuxt設定
├── react-version/                          # React版フロントエンド（新規）
│   ├── src/                                # Reactソースコード
│   ├── public/                             # 静的ファイル
│   └── vite.config.ts                      # Vite設定
├── shared/                                 # 共通ロジック・型定義
│   ├── types/                              # 共通型定義
│   ├── api/                                # APIクライアント
│   ├── composables/                        # 共通ロジック
│   └── utils/                              # 共通ユーティリティ
├── tests/                                  # テストスイート
├── docs/                                   # ドキュメント
├── examples/                               # 使用例
├── config/                                 # 設定ファイル
├── app.py                                  # Streamlit UI
├── api_server.py                           # FastAPI サーバー
├── output/                                 # CSVファイル出力ディレクトリ
├── .github/                                # GitHub Actions CI/CD
│   └── workflows/                          # ワークフロー定義
├── pnpm-workspace.yaml                     # pnpmモノレポ設定
├── uv.lock                                 # uvロックファイル
├── requirements.txt                        # 従来の依存関係ファイル
├── pytest.ini                              # pytest設定
├── mypy.ini                                # mypy設定
├── Makefile                                # ビルド・実行スクリプト
├── setup.sh                                # セットアップスクリプト
└── README.md                               # このファイル
```

## 🌟 主要特徴

- **LangGraphワークフロー**: 状態管理とエラーハンドリングロジックを体系的に実装
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic対応  
- **適応性ベース選抜**: ローカルCSVから最適なペアを適応性に基づいてLLM選抜
- **表現ルール遵守**: NG表現禁止・値域制限・文字数規制の自動チェック
- **12時間周期天気予報**: デフォルトで12時間周期のデータを使用
- **デュアルUI実装**: Streamlit（開発用）+ Nuxt.js 3（Vue版） + React（新規）
- **FastAPI統合**: RESTful APIでフロントエンドとバックエンドを分離
- **天気予報キャッシュ**: 効率的な天気データ管理とキャッシュ機能
- **モノレポ構成**: pnpmワークスペースによる効率的な依存管理

## 🔄 LangGraphワークフロー

以下はMobileCommentGeneratorの正確なワークフロー構造です：

```mermaid
graph TB
    Start([開始]) --> input[InputNode<br/>入力検証・初期化]
    
    input --> fetch_forecast[FetchForecastNode<br/>天気予報取得]
    
    fetch_forecast --> retrieve_comments[RetrieveCommentsNode<br/>過去コメント取得]
    
    retrieve_comments --> select_pair[SelectCommentPairNode<br/>LLMによる適応的ペア選択]
    
    select_pair --> should_evaluate{評価すべきか？<br/>should_evaluate}
    
    should_evaluate -->|evaluate| evaluate_candidate[EvaluateCandidateNode<br/>候補評価]
    should_evaluate -->|generate| generate_comment[GenerateCommentNode<br/>コメント生成]
    
    evaluate_candidate --> should_retry{リトライ必要？<br/>should_retry}
    
    should_retry -->|retry<br/>最大5回| select_pair
    should_retry -->|continue| generate_comment
    
    generate_comment --> output[OutputNode<br/>出力整形]
    
    output --> End([終了])
    
    style input fill:#e1f5fe
    style fetch_forecast fill:#f3e5f5
    style retrieve_comments fill:#e8f5e9
    style select_pair fill:#fff3e0
    style evaluate_candidate fill:#fce4ec
    style generate_comment fill:#fff8e1
    style output fill:#e0f2f1
    
    style should_evaluate fill:#ffebee
    style should_retry fill:#ffebee
```

### ワークフローの詳細説明

1. **InputNode**: 入力パラメータの検証と初期状態の設定
2. **FetchForecastNode**: WxTech APIから天気予報データを取得（12時間周期）
3. **RetrieveCommentsNode**: ローカルCSVファイルから過去のコメントデータを取得
4. **SelectCommentPairNode**: LLMが天気に基づいて最適なコメントペアを選択
5. **EvaluateCandidateNode**: 選択されたペアの評価（評価基準に基づく検証）
6. **GenerateCommentNode**: 最終的なコメント生成
7. **OutputNode**: 生成結果の整形と出力

### 条件分岐

- **should_evaluate**: LLMプロバイダーが設定されていない場合は評価をスキップ
- **should_retry**: 評価が失敗した場合、最大5回までリトライ

## 📈 現在の進捗状況

### ✅ Phase 1: 基盤システム（100%完了）
- [x] **地点データ管理システム**: CSV読み込み・検索・条件取得機能
- [x] **天気予報API機能**: WxTech API統合（12時間周期データ対応）
- [x] **過去コメント取得**: ローカルCSVベースのデータ解析・類似度選抜検証
- [x] **LLM統合**: マルチプロバイダー対応（OpenAI/Gemini/Anthropic）

### ✅ Phase 2: LangGraph ワークフロー（100%完了）
- [x] **SelectCommentPairNode**: コメント類似度選抜ベースによる適応選抜
- [x] **EvaluateCandidateNode**: 複数の評価基準による検証
- [x] **基盤ワークフロー**: 実装済みノードでの順健実装
- [x] **InputNode/OutputNode**: 本実装完了
- [x] **GenerateCommentNode**: LLM統合実装
- [x] **統合テスト**: エンドtoエンドテスト状態管理

### ✅ Phase 3: Streamlit UI（100%完了）
- [x] **基礎UI実装**: 地点選択・LLMプロバイダー選択・コメント生成
- [x] **詳細情報表示**: 現在・予報天気データ・詳細情報表示
- [x] **バッチ出力**: 複数地点一括出力機能
- [x] **CSV出力**: 生成結果のエクスポート機能
- [x] **エラーハンドリング**: ユーザーフレンドリーなエラー表示

### ✅ Phase 4: フロントエンド分離（100%完了）
- [x] **フロントエンド分離**: Nuxt.js 3を独立プロジェクトに移行
- [x] **プロジェクト進捗の明確化**: frontend/とsrc/の責任分担明確化
- [x] **API実装**: FastAPI RESTful APIエンドポイント完成
- [x] **統合ドキュメント**: フロントエンド・バックエンド連携ガイド
- [x] **UIコンポーネント**: 地点選択・設定・結果表示の完全実装

### 🚧 Phase 5: デプロイメント（0%完了）
- [ ] **AWSデプロイメント**: Lambda/ECS・CloudWatch統合

## 🚀 AWSデプロイメントロードマップ

以下は AWS 上に本システムを展開するための代表的な手順です。ECS(Fargate) を軸に
しつつ、EC2 での代替運用も視野に入れたロードマップをまとめました。

1. **初期準備**
   - AWS アカウントを作成し、必要な IAM ユーザー／ロールを整備
   - AWS CLI をインストールして `aws configure` で認証情報を設定
   - ネットワークは VPC 内にパブリック／プライベートサブネットを作成し、
     セキュリティグループで HTTP/HTTPS ポートを開放
2. **Docker イメージ管理(ECR)**
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

3. **ECS(Fargate) クラスタ構築**
   - クラスタを作成し、タスク定義で上記イメージを指定
   - サービスを作成して Application Load Balancer と接続
   - CloudWatch Logs へログを送信し、Auto Scaling を有効化

4. **GitHub Actions での CI/CD**
   - PR では `lint` と `test` を実行
   - `main` マージ時に Docker ビルド → ECR push → ECS サービス更新を自動化
   - 例: `aws ecs update-service --cluster <cluster> --service <service> --force-new-deployment`

5. **EC2 デプロイ (代替案)**
   - Auto Scaling Group + Launch Template を用意し、起動時スクリプトで ECR からイメージ
     を pull して `docker run` で起動
   - ALB で複数インスタンスにトラフィックを分散し、CloudWatch Agent でメトリクス／
     ログを収集

6. **運用と周辺サービス**
   - CloudWatch Alarms で CPU や応答コードを監視し、必要に応じて通知
   - データ永続化が必要な場合は RDS や DynamoDB をプライベートサブネットに配置
   - S3 へのファイル保存や Secrets Manager での機密情報管理も検討する

上記を基に環境を整備すれば、可用性とスケーラビリティを両立した AWS 運用が可能に
なります。

## 🔥 React版追加実装ガイド

既存のNuxt.js 3版に影響を与えずにReact版を追加する詳細な手順を以下に示します。

### 📋 設計思想

React版の追加により、より広範囲の開発者コミュニティがこのプロジェクトを活用できるようになります。Nuxt.js版とReact版は並列で存在し、共通のAPIとロジックを共有しながら異なるUIライブラリで実装されます。

### 🏗️ ディレクトリ構成（追加後の全体像）

React版追加後の推奨構成では、既存のNuxt.js版は完全にそのまま保持し、新しく`react-version/`と`shared/`ディレクトリを追加します。

### 📝 実装手順

#### Step 1: モノレポ環境の構築

既存プロジェクトをモノレポ構成に変更し、効率的な開発環境を構築します。

```bash
# pnpmのインストール（推奨）
npm install -g pnpm

# ルートディレクトリでpnpmワークスペースを初期化
pnpm init
```

**pnpm-workspace.yaml**:
```yaml
packages:
  - 'frontend'
  - 'react-version'
  - 'shared'
```

**ルートpackage.json**:
```json
{
  "name": "mobile-comment-generator",
  "version": "1.0.0",
  "private": true,
  "workspaces": [
    "frontend",
    "react-version",
    "shared"
  ],
  "scripts": {
    "dev": "pnpm --filter frontend dev",
    "build": "pnpm --filter frontend build",
    "dev:react": "pnpm --filter react-version dev",
    "build:react": "pnpm --filter react-version build",
    "dev:all": "pnpm --parallel --filter frontend --filter react-version dev",
    "install:all": "pnpm install",
    "test": "pnpm --recursive test",
    "test:vue": "pnpm --filter frontend test",
    "test:react": "pnpm --filter react-version test",
    "lint": "pnpm --recursive lint",
    "lint:vue": "pnpm --filter frontend lint",
    "lint:react": "pnpm --filter react-version lint",
    "typecheck": "pnpm --recursive typecheck",
    "ci:test": "pnpm --recursive test:ci",
    "ci:build": "pnpm --recursive build"
  },
  "devDependencies": {
    "@changesets/cli": "^2.27.1",
    "turbo": "^1.13.0"
  }
}
```

#### Step 2: 共通ロジックディレクトリの作成

**shared/package.json**:
```json
{
  "name": "@mobile-comment-generator/shared",
  "version": "1.0.0",
  "main": "./dist/index.js",
  "module": "./dist/index.mjs",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.js",
      "types": "./dist/index.d.ts"
    },
    "./api": {
      "import": "./dist/api/index.mjs",
      "require": "./dist/api/index.js",
      "types": "./dist/api/index.d.ts"
    },
    "./composables": {
      "import": "./dist/composables/index.mjs",
      "require": "./dist/composables/index.js",
      "types": "./dist/composables/index.d.ts"
    }
  },
  "scripts": {
    "build": "tsup",
    "dev": "tsup --watch",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "tsup": "^8.0.0",
    "typescript": "^5.3.0"
  }
}
```

**shared/tsup.config.ts**:
```typescript
import { defineConfig } from 'tsup';

export default defineConfig({
  entry: {
    index: 'src/index.ts',
    'api/index': 'src/api/index.ts',
    'composables/index': 'src/composables/index.ts',
  },
  format: ['cjs', 'esm'],
  dts: true,
  clean: true,
  external: ['axios'],
});
```

**shared/src/types/index.ts**:
```typescript
// 既存のNuxt.js版と共通の型定義
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

export interface CurrentWeather {
  temperature: number;
  humidity: number;
  pressure: number;
  windSpeed: number;
  windDirection: string;
  description: string;
  icon: string;
}

export interface ForecastWeather {
  datetime: string;
  temperature: {
    min: number;
    max: number;
  };
  humidity: number;
  precipitation: number;
  description: string;
  icon: string;
}

export interface WeatherTrend {
  trend: 'improving' | 'worsening' | 'stable';
  confidence: number;
  description: string;
}
```

**shared/src/api/client.ts**:
```typescript
import axios, { AxiosInstance } from 'axios';
import type { Location, GenerateSettings, GeneratedComment, WeatherData } from '../types';

export class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL?: string) {
    // Nuxt.jsが3000番ポートを使用するため、APIは3001番を使用
    const apiUrl = baseURL || process.env.NUXT_PUBLIC_API_URL || process.env.VITE_API_URL || 'http://localhost:3001';
    
    this.client = axios.create({
      baseURL: apiUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('[API Error]', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
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

export const createApiClient = (baseURL?: string) => new ApiClient(baseURL);
```

**shared/src/composables/useWeatherComment.ts**:
```typescript
import type { GenerateSettings, GeneratedComment, Location } from '../types';
import { createApiClient } from '../api/client';

export interface UseWeatherCommentOptions {
  apiUrl?: string;
}

export const createWeatherCommentComposable = (options: UseWeatherCommentOptions = {}) => {
  const client = createApiClient(options.apiUrl);
  
  const generateComment = async (
    location: Location,
    settings: Omit<GenerateSettings, 'location'>
  ): Promise<GeneratedComment> => {
    const fullSettings: GenerateSettings = {
      location,
      ...settings,
    };
    
    return client.generateComment(fullSettings);
  };

  const getHistory = async (limit?: number): Promise<GeneratedComment[]> => {
    return client.getHistory(limit);
  };

  const getLocations = async (): Promise<Location[]> => {
    return client.getLocations();
  };

  const getWeatherData = async (locationId: string) => {
    return client.getWeatherData(locationId);
  };

  return {
    generateComment,
    getHistory,
    getLocations,
    getWeatherData,
  };
};
```

#### Step 3: React版プロジェクトの作成

```bash
# React版ディレクトリの作成
mkdir react-version
cd react-version

# Vite + React + TypeScriptプロジェクトを作成
pnpm create vite@latest . --template react-ts

# 追加ライブラリのインストール
pnpm add @mobile-comment-generator/shared@workspace:*
pnpm add lucide-react clsx
pnpm add -D tailwindcss postcss autoprefixer @types/react @types/react-dom

# Tailwind CSSを初期化
pnpm dlx tailwindcss init -p
```

**react-version/package.json**:
```json
{
  "name": "@mobile-comment-generator/react-version",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --port 5173",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "test": "vitest",
    "test:ci": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@mobile-comment-generator/shared": "workspace:*",
    "clsx": "^2.1.0",
    "lucide-react": "^0.321.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.55",
    "@types/react-dom": "^18.2.19",
    "@typescript-eslint/eslint-plugin": "^6.21.0",
    "@typescript-eslint/parser": "^6.21.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.35",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.1.0",
    "vitest": "^1.2.0"
  }
}
```

**react-version/vite.config.ts**:
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
});
```

#### Step 4: 環境変数の統一管理

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

# AWS（オプション）
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

**frontend/.env**:
```bash
# 共通環境変数をインポート
source ../.env.shared

# Nuxt.js固有の設定
NUXT_PUBLIC_SITE_NAME="天気コメント生成システム"
```

**react-version/.env**:
```bash
# 共通環境変数をインポート
source ../.env.shared

# React固有の設定
VITE_APP_TITLE="天気コメント生成システム - React版"
```

#### Step 5: React版コンポーネントの実装

**react-version/src/components/LocationSelection.tsx**:
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

  const filteredLocations = locations.filter(location =>
    location.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    location.prefecture.toLowerCase().includes(searchTerm.toLowerCase()) ||
    location.region.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
          <span className="ml-2 text-gray-600">読み込み中...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div>
        <label htmlFor="location-search" className="block text-sm font-medium text-gray-700 mb-2">
          地点選択
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            id="location-search"
            type="text"
            placeholder="地点名または地域名で検索..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {selectedLocation && (
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-primary-600" />
            <div>
              <div className="font-medium text-primary-900">{selectedLocation.name}</div>
              <div className="text-sm text-primary-700">{selectedLocation.prefecture} - {selectedLocation.region}</div>
            </div>
          </div>
        </div>
      )}
      
      <div className="border border-gray-200 rounded-lg max-h-64 overflow-y-auto">
        {filteredLocations.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            検索条件に一致する地点が見つかりません
          </div>
        ) : (
          filteredLocations.map((location) => (
            <button
              key={location.id}
              className={`w-full text-left p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 flex items-center space-x-2 transition-colors ${
                selectedLocation?.id === location.id ? 'bg-primary-50' : ''
              }`}
              onClick={() => onLocationChange(location)}
            >
              <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900 truncate">{location.name}</div>
                <div className="text-sm text-gray-500 truncate">{location.prefecture} - {location.region}</div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
};
```

**react-version/src/hooks/useApi.ts**:
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

  const getHistory = useCallback(async (limit?: number): Promise<GeneratedComment[]> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await composable.getHistory(limit);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '履歴の取得に失敗しました';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [composable]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    loading,
    error,
    generateComment,
    getHistory,
    clearError,
  };
};
```

#### Step 6: CI/CD設定

**.github/workflows/ci.yml**:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-vue:
    name: Test Nuxt.js (Vue)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: pnpm/action-setup@v2
        with:
          version: 8
          
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
          
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
        
      - name: Build shared package
        run: pnpm --filter @mobile-comment-generator/shared build
        
      - name: Lint Vue
        run: pnpm --filter frontend lint
        
      - name: Type check Vue
        run: pnpm --filter frontend typecheck
        
      - name: Test Vue
        run: pnpm --filter frontend test:ci
        
      - name: Build Vue
        run: pnpm --filter frontend build

  test-react:
    name: Test React
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: pnpm/action-setup@v2
        with:
          version: 8
          
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
          
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
        
      - name: Build shared package
        run: pnpm --filter @mobile-comment-generator/shared build
        
      - name: Lint React
        run: pnpm --filter @mobile-comment-generator/react-version lint
        
      - name: Type check React
        run: pnpm --filter @mobile-comment-generator/react-version typecheck
        
      - name: Test React
        run: pnpm --filter @mobile-comment-generator/react-version test:ci
        
      - name: Build React
        run: pnpm --filter @mobile-comment-generator/react-version build

  test-backend:
    name: Test Backend
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
        
      - name: Install dependencies
        run: uv sync
        
      - name: Run tests
        run: uv run pytest tests/
        
      - name: Run type check
        run: uv run mypy src/
```

### 🚀 実行方法

#### Nuxt.js版（既存）
```bash
# Nuxt.js版開発サーバー起動（ポート3000）
pnpm dev

# Nuxt.js版ビルド
pnpm build
```

#### React版（新規）
```bash
# React版開発サーバー起動（ポート5173）
pnpm dev:react

# React版ビルド
pnpm build:react
```

#### 🌙 ダークモード切り替え
React版は起動時にシステムのテーマを検出し、右上のボタンでライト/ダークを切り替えられます。
色の調整は `react-version/src/index.css` 内の `--app-color-*` 変数を変更してください。

#### 両方同時起動
```bash
# Nuxt.js版とReact版を同時起動
pnpm dev:all
```

#### APIサーバー
```bash
# FastAPIサーバー起動（ポート3001）
uv run ./start_api.sh
```

### 🔧 開発ガイドライン

#### ポート配置
- **3000番**: Nuxt.js 3フロントエンド
- **5173番**: React版フロントエンド
- **3001番**: FastAPI バックエンド
- **8501番**: Streamlit開発UI

#### React版コンポーネント設計原則

**1. 関数コンポーネント + Hooks**
```tsx
// ✅ 推奨: 関数コンポーネント
const MyComponent: React.FC<Props> = ({ prop1, prop2 }) => {
  const [state, setState] = useState(initialValue);
  
  useEffect(() => {
    // 副作用処理
  }, [dependencies]);

  return <div>...</div>;
};

// ❌ 非推奨: クラスコンポーネント
class MyComponent extends React.Component {
  // 使用しない
}
```

**2. TypeScript必須**
```tsx
// ✅ 推奨: 明確な型定義
interface ComponentProps {
  title: string;
  count: number;
  onUpdate: (value: number) => void;
  optional?: boolean;
}

const Component: React.FC<ComponentProps> = ({ title, count, onUpdate, optional = false }) => {
  // 実装
};

// ❌ 非推奨: any型の使用
const Component = ({ title, count, onUpdate }: any) => {
  // 型安全性が失われる
};
```

**3. 共通ロジックの活用**
```tsx
// ✅ 推奨: 共通コンポジタブルの使用
import { createWeatherCommentComposable } from '@mobile-comment-generator/shared/composables';

const MyComponent = () => {
  const { generateComment, getHistory } = createWeatherCommentComposable();
  // 共通ロジックを活用
};

// ❌ 非推奨: 重複実装
const MyComponent = () => {
  // APIクライアントを直接実装
  const generateComment = async () => {
    // 重複コード
  };
};
```

#### 依存関係管理

```bash
# 新しい依存関係を追加
pnpm --filter @mobile-comment-generator/react-version add package-name

# 開発依存関係を追加
pnpm --filter @mobile-comment-generator/react-version add -D package-name

# 共通パッケージを更新
pnpm --filter @mobile-comment-generator/shared build
```

この詳細な実装ガイドにより、既存のNuxt.js版に全く影響を与えることなく、本格的なReact版を追加できます。モノレポ構成と共通ロジックの活用により、コード重複を最小限に抑えながら、両フレームワークの特性を活かした実装が可能になります。

## 📊 現在のアップデート内容 (v1.1.5)

**コメント選抜ロジックの大幅改善:**

- `comment_selector.py`: LLMによる適応的コメント選抜とタイム全員対応実装
- プロンプト改善で確実な数値選抜を実装
- 最終出力: 「明日は晴やか」「おでかけ日和です」生成確認

**タイム全員対応の修正:**
- timezone-aware/naive datetime系統エラーを解消
- 時系列データ取得の安全性向上
- 予報データ間隔: 3-6時間間隔での効率的な天気変化追跡

**システム改善:**
- エラーハンドリング強化
- 予報データの精度向上
- プロンプト最適化でLLMレスポンス精度向上

**動作確認済み:**
- 単一地点のコメント生成: LLMによる適応選抜成功
- アドバイスコメント: 3種「おでかけ日和」選抜成功
- 最終出力: 「明日は晴やか」「おでかけ日和です」生成確認

生成されたコメントが地点・天気情報に忠実に適応し変化することを確認

## 📈 天気コメント改善内容 (v1.1.1)

システムは**翌朝9:00-18:00（JST）の時間帯**から天気に基づいてコメントを生成します。設定された時刻は日本標準時間（JST）です。

### 重複コメント防止機能

**重複パターンの検出:**
- 完全同一の重複検出
- 重複キーワード並び（「にわか雨がちらつく」「にわか雨に注意」等）
- 類似表現パターンマッチング（「雨が心配」↔「雨にご注意」「雨に気をつけて」等）
- 頻度観測における高頻出語彙検出（70%以上の文字共通性など）

**代替選抜機能:**
- 重複検出時の自動代替ペア選抜
- 最大10回の候補重複検測機能
- カテゴリベーション（複数パターンがある場合）
- フォールバック機能での効率的な代替利用

**改善例:**
- ❌ Before: 「にわか雨がちらつく」「にわか雨がちらつきます」
- ✅ After: 「にわか雨がちらつく」「水分補給を心がけて」
- ❌ Before: 「熱中症警戒」「熱中症に注意」  
- ✅ After: 「熱中症警戒」「水分補給をお忘れなく」

### 天気の優先順位ルール

1. **特別に慎重な最優先項目**: 雨、雪、雷の3つのうちなどの不適切な天気表現を除去
2. **本日天気の最優先対策**: 重い雨（10mm/h以上）「スッキリしない」表現を阻止  
3. **最高気温35℃以上**: 最高気温最優先で「おでかけ日和」選抜成功
4. **その他**: 最高気温データと湿度

### 予報の例

天気→LLMによる適応選抜成功
- 「雨3回」「晴れ1回」「おでかけ日和」選抜成功
- 「晴れ2回」「お天気予想1回」選抜成功  
- 「真夏日30℃」選抜成功

🚨 生成されたコメントが地点・天気情報に忠実に適応し変化することを確認

## 📝 フロントエンド構成

### フロントエンド機能詳細

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

### API通信

```typescript
// composables/useApi.ts
export const useApi = () => {
  // 地点一覧取得
  const getLocations = async (): Promise<Location[]>
  
  // コメント生成
  const generateComment = async (params: GenerateSettings): Promise<GeneratedComment>
  
  // 生成履歴取得
  const getHistory = async (): Promise<GeneratedComment[]>
}
```

### UI機能詳細

#### LocationSelection.vue
- **フィルタリング**: 北海道・東北・関東・中部・関西・中国・四国・九州など地域別検索機能・フィルタリング機能
- **検索機能**: よく使う地点の保存・手動入力検索機能
- **レスポンシブ**: モバイル・タブレット対応

#### GenerateSettings.vue
- **LLMプロバイダー選択**: OpenAI・Gemini・Anthropic
- **API設定表示**: 温度パラメータ・生成オプション設定
- **プロンプト設定**: カスタムプロンプトテンプレート

#### GeneratedComment.vue
- **コメント表示**: 天気コメント・アドバイスコメント一体表示・コピー機能
- **生成履歴**: 過去の生成コメント一覧・時刻情報・詳細情報表示
- **エクスポート**: CSV出力機能

#### WeatherData.vue
- **現在天気**: リアルタイム天気データ
- **12時間予報**: デフォルトで12時間後のデータを使用
- **気象パラメータ**: 湿度・気圧・風向風速・警戒情報
- **注意報**: 悪天候設定

## 📖 使用方法

### Nuxt.jsフロントエンド（推奨）

```bash
# APIサーバー起動（ポート3001）
uv run ./start_api.sh
```

1. ブラウザで http://localhost:3000 を開く
2. 左パネルから地点と天気設定
3. 「🌦️ コメント生成」ボタンをクリック
4. 生成されたコメントと天気情報を確認

### React版フロントエンド（新規）

```bash
# React版開発サーバー起動（ポート5173）
pnpm dev:react
```

1. ブラウザで http://localhost:5173 を開く
2. 地点選択から希望の地点を選択
3. 生成設定でLLMプロバイダーを選択
4. 「コメント生成」ボタンをクリック
5. 生成されたコメントと天気情報を確認

### Streamlit UI（開発・デバッグ用）

```bash
uv run streamlit run app.py
```

1. ブラウザで http://localhost:8501 を開く
2. 左パネルからLLMプロバイダーを選択
3. 「🌦️ コメント生成」ボタンをクリック
4. 生成されたコメントと天気情報を確認

### プログラマティック使用

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
```

## 🧪 テスト

```bash
# 全テスト実行
make test

# カバレッジ付きテスト
make test-cov

# 統合テスト
make test-integration

# フロントエンドテスト
pnpm test
```

## 📗 開発ツール

### コード品質
- **Black**: コードフォーマッター（100文字）
- **isort**: インポート整理
- **mypy**: 型チェック
- **ruff**: 高速リンター
- **pytest**: テストフレームワーク

### その他便利コマンド
```bash
# セットアップスクリプト使用
chmod +x setup.sh
./setup.sh dev

# メンテナンス
make clean               # 一時ファイル削除
uv sync                  # 依存更新

# ログ表示
tail -f logs/llm_generation.log   # LLMジェネレーションログ

# ヘルプ
make help
```

## 📗 API設定

### 必須設定
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

## 🕑 天気予報時刻の設定

システムは**翌朝9:00-18:00（JST）の時間帯**から天気に基づいてコメントを生成します。設定された時刻は日本標準時間（JST）です。

### 天気の優先順位ルール

1. **特別に慎重な最優先項目**: 雨、雪、雷の3つのうちなどの不適切な天気表現を除去
2. **本日天気の最優先対策**: 重い雨（10mm/h以上）「スッキリしない」表現を阻止
3. **最高気温35℃以上**: 最高気温最優先で「おでかけ日和」選抜成功
4. **その他**: 最高気温データと湿度

### 予報の例

天気→LLMによる適応選抜成功
- 「雨3回」「晴れ1回」「おでかけ日和」選抜成功
- 「晴れ2回」「お天気予想1回」選抜成功
- 「真夏日30℃」選抜成功

🚨 生成されたコメントが地点・天気情報に忠実に適応し変化することを確認

## 📔 コントリビューション

1. Issueを作成で問題報告・機能要望
2. Fork & Pull Requestでの貢献
3. [開発ガイドライン](docs/CONTRIBUTING.md)に従った開発

## 📘 サポート

問題が解決しない場合は、GitHub Issuesで報告してください。

---

**このセットアップガイドで問題が解決しない場合は、GitHub Issuesで報告してください。**

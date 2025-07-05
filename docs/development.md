# 🛠️ 開発ガイド

## 📋 開発環境セットアップ

### 必要なツール
- Python 3.11以上
- Node.js 20以上
- pnpm 8以上
- uv (Python パッケージマネージャー)

### 初期セットアップ
```bash
# セットアップスクリプト使用
chmod +x setup.sh
./setup.sh dev

# または手動セットアップ
# Python依存関係
uv sync

# JavaScript依存関係
pnpm install
```

## 🧪 テスト

### バックエンドテスト

```bash
# 全テスト実行
make test

# カバレッジ付きテスト
make test-cov

# 統合テスト
make test-integration

# 特定のテストファイルを実行
uv run pytest tests/test_specific.py

# 特定のテスト関数を実行
uv run pytest tests/test_specific.py::test_function_name
```

### フロントエンドテスト

```bash
# 全フロントエンドテスト
pnpm test

# Vue (Nuxt.js)テスト
pnpm test:vue

# Reactテスト
pnpm test:react

# ウォッチモード
pnpm test:watch
```

### E2Eテスト

```bash
# Playwright E2Eテスト
pnpm test:e2e

# ヘッドレスモード
pnpm test:e2e:headless
```

## 📗 コード品質ツール

### Python

#### Black (コードフォーマッター)
```bash
# フォーマットチェック
make format-check

# 自動フォーマット
make format

# 設定 (pyproject.toml)
[tool.black]
line-length = 100
target-version = ['py311']
```

#### isort (インポート整理)
```bash
# インポート整理
make isort

# チェックのみ
make isort-check
```

#### mypy (型チェック)
```bash
# 型チェック実行
make typecheck

# 設定 (mypy.ini)
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

#### ruff (高速リンター)
```bash
# リント実行
make lint

# 自動修正
make lint-fix
```

### JavaScript/TypeScript

#### ESLint
```bash
# リント実行
pnpm lint

# 自動修正
pnpm lint:fix

# Vue専用
pnpm lint:vue

# React専用
pnpm lint:react
```

#### TypeScript
```bash
# 型チェック
pnpm typecheck

# Vue専用
pnpm typecheck:vue

# React専用
pnpm typecheck:react
```

## 🔧 開発用コマンド

### Makefile コマンド一覧

```bash
# ヘルプ表示
make help

# 開発環境起動
make dev           # APIサーバー起動
make dev-ui        # Streamlit UI起動

# テスト
make test          # 全テスト実行
make test-cov      # カバレッジ付きテスト
make test-watch    # ウォッチモードでテスト

# コード品質
make format        # コードフォーマット
make lint          # リントチェック
make typecheck     # 型チェック
make quality       # 全品質チェック実行

# クリーンアップ
make clean         # 一時ファイル削除
make clean-all     # 全キャッシュ削除
```

### 便利なスクリプト

#### ログ確認
```bash
# LLM生成ログ
tail -f logs/llm_generation.log

# APIサーバーログ
tail -f logs/api_server.log

# エラーログのみ
grep ERROR logs/*.log
```

#### データベース管理
```bash
# CSVデータ確認
ls -la data/csv/

# 出力ファイル確認
ls -la output/
```

## 📊 パフォーマンス分析

### Python プロファイリング
```python
# コード内でプロファイリング
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 計測したいコード
result = run_comment_generation(...)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### メモリプロファイリング
```bash
# memory-profilerを使用
uv pip install memory-profiler

# デコレータを使用
@profile
def memory_intensive_function():
    # メモリ使用量を計測したい関数
    pass

# 実行
uv run python -m memory_profiler your_script.py
```

## 🐛 デバッグ

### VS Code設定

**.vscode/launch.json**:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: API Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/api_server.py",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: Streamlit",
      "type": "python",
      "request": "launch",
      "module": "streamlit",
      "args": ["run", "app.py"],
      "console": "integratedTerminal"
    }
  ]
}
```

### ログレベル設定
```python
# 環境変数で設定
export LOG_LEVEL=DEBUG

# コード内で設定
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 CI/CD

### GitHub Actions

**.github/workflows/ci.yml**:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
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

### pre-commit フック

**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort
  
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
```

セットアップ:
```bash
# pre-commitインストール
uv pip install pre-commit

# フック設定
pre-commit install
```

## 🔄 開発ワークフロー

### 1. 機能開発
```bash
# 新しいブランチ作成
git checkout -b feature/new-feature

# 開発サーバー起動
make dev

# コード変更後、品質チェック
make quality

# テスト実行
make test
```

### 2. コミット前
```bash
# フォーマット
make format

# リント
make lint

# テスト
make test

# コミット (pre-commitフックが自動実行)
git commit -m "feat: 新機能追加"
```

### 3. プルリクエスト
- GitHub ActionsでCIが自動実行
- コードレビュー後マージ

## 📔 トラブルシューティング

### よくある問題

1. **依存関係のインストールエラー**
   ```bash
   # キャッシュクリア
   uv cache clean
   
   # 再インストール
   uv sync --refresh
   ```

2. **ポート競合**
   ```bash
   # 使用中のポート確認
   lsof -i :3001
   
   # プロセス終了
   kill -9 <PID>
   ```

3. **テスト失敗**
   ```bash
   # 詳細ログ表示
   uv run pytest -vvs
   
   # 特定のテストのみ実行
   uv run pytest -k "test_name"
   ```

## 📚 その他のリソース

- [Python開発ベストプラクティス](https://docs.python-guide.org/)
- [TypeScript ハンドブック](https://www.typescriptlang.org/docs/)
- [Vue.js スタイルガイド](https://vuejs.org/style-guide/)
- [React ベストプラクティス](https://react.dev/learn)
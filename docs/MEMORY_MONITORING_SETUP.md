# メモリ監視機能のセットアップガイド

このドキュメントでは、MobileCommentGeneratorのメモリ監視機能を有効にする方法について説明します。

## 概要

メモリ監視機能は、システムのメモリ使用状況をリアルタイムで監視し、メモリ不足による問題を未然に防ぐための機能です。この機能を使用するには、`psutil`パッケージのインストールが必要です。

## psutilについて

`psutil`（Python System and Process Utilities）は、実行中のプロセスとシステム使用率（CPU、メモリ、ディスク、ネットワーク、センサー）の情報を取得するためのクロスプラットフォームライブラリです。

### 対応プラットフォーム
- Linux
- Windows
- macOS
- FreeBSD、OpenBSD、NetBSD
- Sun Solaris
- AIX

## インストール方法

### 1. 開発環境でのインストール（推奨）

開発環境では、開発依存関係として`psutil`が含まれています：

```bash
# uvを使用する場合
uv pip install -e ".[dev]"

# または通常のpipを使用する場合
pip install -e ".[dev]"
```

### 2. 本番環境でのインストール

本番環境でメモリ監視を有効にする場合：

```bash
# 個別にインストール
pip install psutil>=5.9.0

# またはrequirements.txtに追加
echo "psutil>=5.9.0" >> requirements.txt
pip install -r requirements.txt
```

### 3. Dockerコンテナでのインストール

Dockerfileに以下を追加：

```dockerfile
# psutilのインストール（オプション）
RUN pip install psutil>=5.9.0
```

### 4. 条件付きインストール

環境変数でインストールを制御する例：

```bash
# 環境変数でメモリ監視を有効化
if [ "$ENABLE_MEMORY_MONITORING" = "true" ]; then
    pip install psutil>=5.9.0
fi
```

## インストールの確認

インストールが成功したか確認：

```python
python -c "import psutil; print(f'psutil {psutil.__version__} installed successfully')"
```

## メモリ監視なしでの動作

`psutil`がインストールされていない場合でも、アプリケーションは正常に動作します：

- メモリ監視機能は自動的に無効化されます
- ログに警告メッセージが出力されます
- その他の機能には影響しません

## 設定

メモリ監視の閾値は環境変数で設定できます：

```bash
# .envファイルまたは環境変数
MEMORY_WARNING_THRESHOLD=80   # 警告閾値（デフォルト: 80%）
MEMORY_CRITICAL_THRESHOLD=90  # 危険閾値（デフォルト: 90%）
```

## 使用例

### 基本的な使用

```python
from src.utils.memory_monitor import MemoryMonitor

# メモリモニターの初期化
monitor = MemoryMonitor()

# メモリ情報の取得
info = monitor.get_memory_info()
print(f"プロセスメモリ: {info['process']['rss_mb']:.1f}MB")
print(f"システムメモリ使用率: {info['system']['percent']:.1f}%")

# メモリ使用量のチェック
warning_needed, msg = monitor.check_memory_usage()
if warning_needed:
    logger.warning(msg)
```

### キャッシュメモリの推定

```python
# キャッシュサイズの取得
cache_sizes = {
    "memory_cache": 500,
    "spatial_cache": 200
}

# メモリ使用量の推定
estimates = monitor.get_cache_memory_estimate(cache_sizes)
print(f"推定キャッシュメモリ: {estimates['total']:.1f}MB")
```

## トラブルシューティング

### インストールエラーが発生する場合

1. **権限エラー**
   ```bash
   # ユーザーディレクトリにインストール
   pip install --user psutil
   ```

2. **コンパイラエラー（Windowsの場合）**
   - Visual Studio Build Toolsをインストール
   - またはプリコンパイル済みのwheelファイルを使用

3. **古いpipバージョン**
   ```bash
   # pipをアップグレード
   pip install --upgrade pip
   ```

### メモリ監視が動作しない場合

1. **インポートエラーの確認**
   ```python
   import sys
   print("psutil" in sys.modules)
   ```

2. **ログの確認**
   ```
   psutil is not available. Memory monitoring will be disabled.
   ```

3. **権限の確認**
   - 一部のシステムでは、プロセス情報へのアクセスに特権が必要な場合があります

## セキュリティ考慮事項

- `psutil`はシステム情報にアクセスするため、セキュリティポリシーによっては使用が制限される場合があります
- 本番環境では、必要最小限の権限で実行することを推奨します
- メモリ情報のログ出力には機密情報が含まれないよう注意してください

## まとめ

メモリ監視機能は、システムの安定性を向上させる重要な機能ですが、オプショナルな機能として設計されています。環境や要件に応じて、適切にセットアップしてください。

不明な点がある場合は、[GitHub Issues](https://github.com/sakamo-wni/MobileCommentGenerator/issues)でお問い合わせください。
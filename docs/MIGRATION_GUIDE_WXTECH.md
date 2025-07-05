# WxTech APIクライアント移行ガイド

## 概要

`wxtech_client.py` モジュールは、保守性とコードの組織化を改善するため、複数の小さなモジュールに分割されました。この文書では、新しい構造への移行方法を説明します。

## モジュール構造の変更

### 旧構造
```
src/apis/
└── wxtech_client.py  # 1300行の単一ファイル
```

### 新構造
```
src/apis/
├── wxtech_client.py  # 後方互換性のためのラッパー（非推奨）
└── wxtech/
    ├── __init__.py     # パッケージエクスポート
    ├── api.py          # HTTPリクエスト処理
    ├── client.py       # 高レベルクライアント
    ├── errors.py       # エラー定義
    ├── mappings.py     # データマッピング
    └── parser.py       # レスポンスパーサー
```

## コードの移行

### 基本的なインポートの変更

#### 旧コード
```python
from src.apis.wxtech_client import WxTechAPIClient, WxTechAPIError
```

#### 新コード
```python
from src.apis.wxtech import WxTechAPIClient, WxTechAPIError
```

### 互換性のあるインポート（一時的な使用のみ）
```python
# 警告が表示されますが、動作します
from src.apis.wxtech_client import WxTechAPIClient
```

## API の使用方法

### クライアントの初期化
```python
from src.apis.wxtech import WxTechAPIClient

# 基本的な初期化
client = WxTechAPIClient(api_key="your_api_key")

# カスタムタイムアウトの設定
client = WxTechAPIClient(api_key="your_api_key", timeout=60)
```

### 天気予報の取得
```python
# 座標による取得
forecast = client.get_forecast(lat=35.6762, lon=139.6503)

# Locationオブジェクトによる取得
from src.data.location_manager import Location
location = Location(name="東京", latitude=35.6762, longitude=139.6503)
forecast = client.get_forecast_by_location(location)
```

### エラーハンドリング
```python
from src.apis.wxtech import WxTechAPIError

try:
    forecast = client.get_forecast(lat, lon)
except WxTechAPIError as e:
    if e.error_type == "rate_limit":
        print("レート制限に達しました")
    elif e.error_type == "api_key_invalid":
        print("APIキーが無効です")
    else:
        print(f"APIエラー: {e}")
```

## 非同期処理
```python
import asyncio
from src.apis.wxtech import WxTechAPIClient

async def get_weather_async():
    client = WxTechAPIClient(api_key="your_api_key")
    forecast = await client.get_forecast_async(lat=35.6762, lon=139.6503)
    return forecast

# 実行
forecast = asyncio.run(get_weather_async())
```

## 後方互換性関数
```python
from src.apis.wxtech import get_japan_1km_mesh_weather_forecast

# 既存のコードがこの関数を使用している場合、変更は不要
result = await get_japan_1km_mesh_weather_forecast(lat, lon, api_key)
```

## 移行チェックリスト

- [ ] すべての `from src.apis.wxtech_client import` を `from src.apis.wxtech import` に変更
- [ ] エラーハンドリングが適切に機能することを確認
- [ ] テストが正常に実行されることを確認
- [ ] 非推奨警告が表示されないことを確認

## よくある質問

### Q: 機能に変更はありますか？
A: いいえ、機能は完全に同一です。コードの組織化のみが改善されました。

### Q: 旧コードはいつまで動作しますか？
A: 当面は後方互換性が維持されますが、新しいコードでは新しいインポートパスを使用することを推奨します。

### Q: パフォーマンスへの影響はありますか？
A: 実質的な影響はありません。モジュールの分割により、必要な部分のみをインポートできるようになりました。

## トラブルシューティング

### ImportError が発生する場合
```python
# パスが正しいことを確認
import sys
print(sys.path)

# モジュールが存在することを確認
from pathlib import Path
wxtech_path = Path("src/apis/wxtech")
print(f"wxtech exists: {wxtech_path.exists()}")
```

### 非推奨警告を一時的に無効化する
```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="src.apis.wxtech_client")
```

## さらなる情報

詳細な実装については、各モジュールのドキュメントストリングを参照してください：
- `src/apis/wxtech/api.py` - HTTPリクエストの詳細
- `src/apis/wxtech/client.py` - クライアントAPI
- `src/apis/wxtech/errors.py` - エラータイプ
- `src/apis/wxtech/mappings.py` - データ変換
- `src/apis/wxtech/parser.py` - レスポンス解析
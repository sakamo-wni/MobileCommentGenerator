# 設定ファイル統一移行計画

## 現状分析

### 既存の設定ファイル構造
1. **新統一設定** (`config.py`) - 準備完了だが未使用
2. **旧統一設定** (`unified_config.py`) - 現在使用中
3. **個別設定ファイル** - 各機能ごとに分散

### 依存関係の概要
```
app_config.py (8 files) → unified_config.py → [計画] → config.py
    ↓
weather_config.py (9 files) → weather_settings.py (5 files) → constants.py (2 files)
                            → langgraph_settings.py (2 files)
                            → app_settings.py (3 files)

severe_weather_config.py (4 files)
comment_config.py (3 files)
weather_constants.py (10 files) - 独立
```

## 移行フェーズ

### フェーズ1: 定数ファイルの統合
**対象**: `constants.py`, `weather_constants.py`
**理由**: 依存関係がない（リーフノード）
**影響**: 12ファイル

1. 新しい`config.py`に定数セクションを追加
2. インポートを更新
3. テスト実行

### フェーズ2: 単純な設定の移行
**対象**: `langgraph_settings.py`, `severe_weather_config.py`, `comment_config.py`
**理由**: 依存関係が少ない
**影響**: 9ファイル

### フェーズ3: 中核設定の移行
**対象**: `weather_settings.py`, `app_settings.py`
**理由**: 中程度の依存関係
**影響**: 8ファイル

### フェーズ4: ラッパーの更新
**対象**: `weather_config.py`
**理由**: 単なるラッパーなので、依存先が移行済みなら簡単
**影響**: 9ファイル

### フェーズ5: メイン設定の移行
**対象**: `app_config.py`, `unified_config.py`
**理由**: 最も広く使用されている
**影響**: 11ファイル

### フェーズ6: クリーンアップ
- 古い設定ファイルの削除
- `compatibility.py`の削除
- ドキュメントの更新

## 各フェーズでの作業手順

1. 新しい設定構造を`config.py`に追加
2. 互換性レイヤーを作成（必要に応じて）
3. 1ファイルずつインポートを更新
4. 各更新後にテストを実行
5. コミット＆プッシュ

## リスク管理

- 各フェーズ後に完全なテストスイートを実行
- 問題が発生した場合は即座にロールバック
- 本番環境への影響を最小化するため、段階的にデプロイ
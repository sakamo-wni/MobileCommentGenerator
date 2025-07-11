# 非推奨機能の削除計画

## 概要

このドキュメントは、MobileCommentGeneratorプロジェクトにおける非推奨機能の削除計画を記載しています。

## 1. 互換性レイヤー

### 対象ファイル

- `src/config/unified_config.py` - 旧設定システムとの互換性レイヤー
- `src/config/unified_config_shim.py` - 互換性のためのシムクラス
- `src/config/compatibility.py` - 独立した互換性ユーティリティ

### 削除計画

#### Phase 1 (現在)
- 新しい設定システム（`src/config/config.py`）への移行完了
- 互換性レイヤーに非推奨警告を追加済み
- すべての内部コードで新しい設定システムを使用

#### Phase 2 (2025年Q2)
- 外部連携システムへの移行期間
- 移行ガイドの提供
- 非推奨警告をより目立つように更新

#### Phase 3 (2025年Q3)
- 互換性レイヤーの削除
- 最終的なクリーンアップ

### 移行方法

```python
# 旧コード（非推奨）
from src.config.unified_config import get_api_config
config = get_api_config()

# 新コード（推奨）
from src.config.config import get_config
config = get_config().api
```

## 2. AWS/S3設定

### 現状

- AWS設定は現在使用されていない（`src/config/compatibility.py`のコメント参照）
- UIには設定項目が残存
- 将来的にAWS Bedrockサポートの可能性あり

### 削除計画

#### 即座に実施可能
- `src/config/settings/api_settings.py`からAWS設定フィールドを削除
- `src/config/app_config.py`のAPIKeysクラスからAWS関連フィールドを削除

#### UI更新（慎重に実施）
- `src/ui/components/settings_panel.py`からAWS設定セクションを削除
- ただし、AWS Bedrockサポートの計画がある場合は保留

### 影響範囲

以下のファイルに影響：
- `src/config/settings/api_settings.py`
- `src/config/app_config.py`
- `src/ui/components/settings_panel.py`
- `src/ui/utils/config_utils.py`

## 3. その他の非推奨機能

### S3コメント取得機能
- コード内にS3参照が残存するが、実装は存在しない
- 将来的な実装予定がなければコメントも削除推奨

## 推奨アクション

1. **短期（1ヶ月以内）**
   - [ ] AWS設定の使用状況を最終確認
   - [ ] 不要なAWS設定フィールドを削除
   - [ ] 削除による影響をテスト

2. **中期（3ヶ月以内）**
   - [ ] 外部システムへの移行ガイド作成
   - [ ] 非推奨警告の強化

3. **長期（6ヶ月以内）**
   - [ ] 互換性レイヤーの完全削除
   - [ ] 最終的なコードクリーンアップ

## メンテナンス

このドキュメントは定期的に更新し、削除計画の進捗を記録してください。

最終更新: 2025年7月11日
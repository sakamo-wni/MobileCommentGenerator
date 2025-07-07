# 天気コメントバリデータモジュール

このディレクトリには、天気コメントの検証を行うバリデータモジュールが含まれています。

## モジュール構成

### 1. base_validator.py
- **責任範囲**: 全バリデータの基底クラス
- **主な機能**:
  - 共通の検証インターフェース定義
  - 禁止ワードのチェック機能
  - 季節判定機能
  - ログ記録機能

### 2. weather_validator.py
- **責任範囲**: 天気条件に基づくコメント検証
- **主な機能**:
  - 天気タイプ（晴れ/曇り/雨）の判定
  - 天気別の禁止ワードチェック
  - 雨天時の矛盾表現チェック
  - 必須キーワードのチェック
- **特記事項**:
  - `_is_stable_cloudy_weather`メソッドは将来の機能拡張用（現在未使用）

### 3. temperature_validator.py
- **責任範囲**: 温度条件に基づくコメント検証
- **主な機能**:
  - 温度範囲別の禁止ワードチェック
  - 熱中症警告の適切性検証（34°C以上）
  - 温度と症状の矛盾チェック

### 4. consistency_validator.py
- **責任範囲**: コメントペアの一貫性検証
- **主な機能**:
  - 天気コメントとアドバイスの矛盾チェック
  - 重複コンテンツの検出
  - トーン（態度）の一貫性チェック
  - 傘関連表現の重複チェック
- **パフォーマンス最適化**:
  - 正規表現パターンをプリコンパイル済み

### 5. regional_validator.py
- **責任範囲**: 地域特性に基づくコメント検証
- **主な機能**:
  - 沖縄地域での雪・極寒表現の除外
  - 北海道地域での猛暑表現の除外
  - 湿度条件のチェック

### 6. weather_comment_validator.py
- **責任範囲**: メインバリデータ（ファサード）
- **主な機能**:
  - 各バリデータの統合管理
  - コメントの総合的な検証
  - 優先度スコアリング
  - フィルタリング機能

## 重要な仕様変更

### うすぐもり/薄曇りの扱い
- **変更前**: 晴天として扱われていた
- **変更後**: 曇りとして扱うように修正
- **理由**: 「うすぐもり」は曇りの一種であり、晴天表現（「夏空が広がる」など）が不適切
- **影響**:
  - SUNNY_WEATHER_KEYWORDS から「薄曇」「うすぐもり」「薄ぐもり」を削除
  - 曇り判定に「うすぐもり」「薄曇」「薄ぐもり」を追加
  - 曇天時の禁止ワードに「夏空」「秋空」などを追加

## 型安全性

- `TypedDict`を使用して辞書構造を明確化
- `Optional`型を使用してNone許容パラメータを明示
- 型ヒントにより、IDEの補完機能とエラー検出が向上

## パフォーマンス改善

1. **モジュール分割**:
   - 51KBの巨大ファイルを機能別に分割
   - 必要なバリデータのみを読み込み可能

2. **正規表現のプリコンパイル**:
   - consistency_validator.pyで実装
   - 繰り返し使用される正規表現パターンを事前コンパイル

3. **遅延読み込み**:
   - 各バリデータは必要時のみインスタンス化

## 使用例

```python
from src.utils.validators import WeatherCommentValidator

validator = WeatherCommentValidator()

# 単一コメントの検証
is_valid, reason = validator.validate_comment(comment, weather_data)

# コメントペアの一貫性チェック
is_consistent, reason = validator.validate_comment_pair_consistency(
    weather_comment, advice_comment, weather_data
)

# コメントのフィルタリング
filtered_comments = validator.filter_comments(comments, weather_data)
```
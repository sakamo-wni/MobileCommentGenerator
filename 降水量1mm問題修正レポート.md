# 降水量1mm「強雨や雷に注意」問題 修正レポート

## 問題概要
降水量1mmの軽微な雨や雷で「強雨や雷に注意」などの過度な警戒コメントが生成される問題。

## 原因分析

### 1. 降水量の閾値設定問題
- **場所**: `/src/data/weather_data.py` の `is_severe_weather()` メソッド
- **問題**: 雷が無条件で悪天候として扱われ、降水量1mmでも強い警戒コメントが選択される
- **原因**: 天気説明の文字列マッチングと実際の降水量データが連携していない

### 2. コメント選択ロジックの問題
- **場所**: `/src/nodes/select_comment_pair_node.py` の除外判定関数群
- **問題**: 天気説明に「雨」「雷」が含まれると、実際の降水量を無視して強い表現を選択
- **原因**: 降水量の重要度が適切に考慮されていない

### 3. バリデーションシステムの問題
- **場所**: `/src/utils/weather_comment_validator.py`
- **問題**: 天気説明のみでコメント適切性を判定し、降水量を考慮していない

## 修正内容

### 1. WeatherForecast クラスの強化 (`src/data/weather_data.py`)

#### 新機能追加
```python
def get_precipitation_severity(self) -> str:
    """降水量の重要度を取得"""
    if self.precipitation <= 0.5:
        return "none"
    elif self.precipitation <= 2.0:
        return "light"  # 軽い雨（1-2mm）
    elif self.precipitation <= 10.0:
        return "moderate"  # 中程度の雨
    elif self.precipitation <= 30.0:
        return "heavy"  # 大雨
    else:
        return "very_heavy"  # 激しい雨
```

#### 悪天候判定の改善
```python
def is_severe_weather(self) -> bool:
    # 雷は降水量が5mm以上の場合のみ悪天候とする
    thunder_with_rain = (
        self.weather_condition == WeatherCondition.THUNDER and 
        self.precipitation >= 5.0
    )
    
    return (
        self.weather_condition in severe_conditions
        or thunder_with_rain  # 雷+降水量5mm以上
        or self.precipitation >= 10.0
        or self.wind_speed >= 15.0
    )
```

### 2. コメント選択ロジックの改善 (`src/nodes/select_comment_pair_node.py`)

#### 降水量を考慮した除外判定
- **軽い雨（1-2mm）**: 強い警戒表現（「激しい」「警戒」「危険」等）を除外
- **中程度の雨（2-10mm）**: 快適系表現のみ除外
- **大雨（10mm以上）**: 従来通り厳格な除外

#### 雷の特別処理
- **軽微な雷（降水量5mm未満）**: 強い警戒表現を除外、軽い注意表現のみ許可
- **強い雷（降水量5mm以上）**: 従来通り強い警戒表現を許可

### 3. バリデーションシステムの強化 (`src/utils/weather_comment_validator.py`)

#### 降水量レベル別検証
```python
# 雷の特別チェック（降水量を考慮）
elif "雷" in weather_desc:
    if precipitation >= 5.0:
        # 強い雷（降水量5mm以上）
        forbidden_words = self.weather_forbidden_words["heavy_rain"][comment_type]
    else:
        # 軽微な雷（降水量5mm未満）では強い警戒表現を禁止
        strong_warning_words = ["激しい", "警戒", "危険", "大荒れ", "本格的", "強雨"]
```

## 修正効果の検証

### テスト結果

#### 降水量1mm の雨
- ❌ **修正前**: 「強雨や雷に注意」「本格的な雨に注意」が選択される
- ✅ **修正後**: 「雨雲が広がる空」「にわか雨が心配」など適切な表現が選択される

#### 降水量1mm の雷
- ❌ **修正前**: 「雷に警戒してください」「屋内に避難を」が選択される
- ✅ **修正後**: 「雷の音が聞こえる空」「雷に注意を」など軽い注意表現が選択される

#### 降水量15mm の大雨（比較用）
- ✅ **修正前後**: 「強雨や雷に注意」が適切に選択される（変更なし）

## 修正による改善点

### 1. 降水量の重要度を適切に反映
- 軽微な降水（1-2mm）では過度な警戒表現を回避
- 実際の気象状況に見合ったコメント選択

### 2. 雷の分類の細分化
- 降水を伴わない軽微な雷: 軽い注意表現
- 降水を伴う強い雷: 強い警戒表現

### 3. ユーザー体験の向上
- 軽微な天候で不安を煽らない適切な表現
- 実際の危険度に応じた段階的な警告レベル

## 技術的な特徴

### 1. 後方互換性の保持
- 既存の悪天候判定システムは維持
- 大雨・嵐などの重要な気象条件の警告は従来通り

### 2. 段階的な警告システム
- 降水量レベル: none → light → moderate → heavy → very_heavy
- 各レベルに応じた適切なコメント選択

### 3. 詳細なログ出力
- 除外理由の明確化（「軽い雨（1.0mm）で過度な警戒表現」等）
- デバッグとメンテナンスの向上

## まとめ

この修正により、降水量1mmの軽微な雨や雷で「強雨や雷に注意」などの過度な警戒コメントが生成される問題が解決されました。実際の降水量に基づいた適切なレベルの表現が選択されるようになり、ユーザーに対してより正確で適切な気象情報を提供できるようになりました。
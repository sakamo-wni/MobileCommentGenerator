# リファクタリングガイド

## モジュール構造

### 分割されたモジュール

#### 1. unified_comment_generation/
統合コメント生成機能を責務ごとに分割：
- `weather_formatter.py` - 天気情報のフォーマット処理
- `prompt_builder.py` - LLMプロンプトの構築
- `response_parser.py` - LLMレスポンスの解析
- `comment_filters.py` - コメントのフィルタリング処理

#### 2. weather_forecast/services/
天気予報取得機能をサービスクラスに分割：
- `location_service.py` - 地点情報の取得と検証
- `weather_api_service.py` - 天気予報API通信
- `forecast_processing_service.py` - 予報データの加工処理
- `temperature_analysis_service.py` - 気温分析処理

#### 3. comment_selector/strategies/
コメント選択戦略をStrategy パターンで実装：
- `rain_strategy.py` - 雨天時のコメント選択戦略
- `minimal_validation_strategy.py` - 最小限バリデーション戦略
- `alternative_selection_strategy.py` - 代替選択戦略（重複回避）

## 戦略パターンの使用ガイド

### 新しい戦略の追加方法

1. `src/nodes/comment_selector/strategies/`に新しいファイルを作成
2. 基本的なインターフェースに従って実装：

```python
class YourNewStrategy:
    """新しい戦略の説明"""
    
    def your_method(self, 
                   weather_comments: list[PastComment],
                   advice_comments: list[PastComment],
                   weather_data: WeatherForecast,
                   **kwargs) -> Any:
        """メソッドの説明
        
        Args:
            weather_comments: 天気コメントリスト
            advice_comments: アドバイスコメントリスト
            weather_data: 天気データ
            
        Returns:
            処理結果
            
        Raises:
            ValueError: エラーの説明
        """
        # 実装
        pass
```

3. `__init__.py`にエクスポートを追加
4. 必要に応じて`base_selector.py`で使用

### 設計原則

- **単一責任の原則**: 各戦略は特定の選択ロジックのみを担当
- **開放閉鎖の原則**: 新しい戦略の追加は既存コードの変更を最小限に
- **依存性逆転の原則**: 具体的な実装ではなく抽象に依存

## エラーハンドリング

### 例外の種類と対処

各サービスクラスで発生しうる例外：

1. **WeatherAPIService**
   - `WxTechAPIError`: ネットワークエラー、タイムアウト、サーバーエラー
   - `ValueError`: 空のデータ、無効な地点名

2. **LocationService**
   - `ValueError`: 地点が見つからない（座標も提供されていない）

3. **TemperatureAnalysisService**
   - 例外をキャッチして空の辞書を返す（非致命的エラー）

## テスト方針

各モジュールに対応する単体テストを配置：
- `tests/nodes/unified_comment_generation/`
- `tests/nodes/weather_forecast/services/`
- `tests/nodes/comment_selector/strategies/`

### テストの書き方

1. 正常系・異常系の両方をカバー
2. モックを使用して外部依存を排除
3. エッジケースを考慮
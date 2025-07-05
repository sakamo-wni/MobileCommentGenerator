# 設定永続化機能設計書

## 概要

現在の環境変数ベースの設定管理に加えて、JSON/YAMLファイルからの設定読み込み機能を追加する設計案です。

## 実装案

### 1. ConfigLoader クラス

```python
from pathlib import Path
import json
import yaml
from typing import Dict, Any, Optional

class ConfigLoader:
    """設定ファイルの読み込みを管理"""
    
    @staticmethod
    def load_from_file(filepath: Path) -> Dict[str, Any]:
        """ファイルから設定を読み込む"""
        if not filepath.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {filepath}")
        
        if filepath.suffix == '.json':
            return ConfigLoader._load_json(filepath)
        elif filepath.suffix in ['.yml', '.yaml']:
            return ConfigLoader._load_yaml(filepath)
        else:
            raise ValueError(f"サポートされていないファイル形式: {filepath.suffix}")
    
    @staticmethod
    def _load_json(filepath: Path) -> Dict[str, Any]:
        """JSONファイルから読み込む"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def _load_yaml(filepath: Path) -> Dict[str, Any]:
        """YAMLファイルから読み込む"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
```

### 2. 設定の優先順位

1. 環境変数（最優先）
2. 設定ファイル
3. デフォルト値

### 3. AppConfig の拡張

```python
@dataclass
class AppConfig:
    """アプリケーション全体の設定クラス"""
    
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    langgraph: LangGraphConfig = field(default_factory=LangGraphConfig)
    debug_mode: bool = field(default=False)
    log_level: str = field(default="INFO")
    
    @classmethod
    def from_file(cls, filepath: Path) -> 'AppConfig':
        """ファイルから設定を読み込んでインスタンスを作成"""
        config_data = ConfigLoader.load_from_file(filepath)
        return cls._from_dict(config_data)
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """辞書から設定を構築"""
        weather_data = data.get('weather', {})
        langgraph_data = data.get('langgraph', {})
        
        # WeatherConfigの構築
        weather_config = WeatherConfig(**weather_data)
        
        # LangGraphConfigの構築
        langgraph_config = LangGraphConfig(**langgraph_data)
        
        return cls(
            weather=weather_config,
            langgraph=langgraph_config,
            debug_mode=data.get('debug_mode', False),
            log_level=data.get('log_level', 'INFO')
        )
```

### 4. 設定ファイルの例

#### config.json
```json
{
  "weather": {
    "default_location": "東京",
    "forecast_hours": 24,
    "api_timeout": 30
  },
  "langgraph": {
    "enable_weather_integration": true,
    "min_confidence_threshold": 0.8
  },
  "debug_mode": false,
  "log_level": "INFO"
}
```

#### config.yaml
```yaml
weather:
  default_location: 東京
  forecast_hours: 24
  api_timeout: 30

langgraph:
  enable_weather_integration: true
  min_confidence_threshold: 0.8

debug_mode: false
log_level: INFO
```

### 5. get_config() 関数の拡張

```python
def get_config(config_file: Optional[Path] = None) -> AppConfig:
    """グローバル設定インスタンスを取得
    
    Args:
        config_file: 設定ファイルのパス（オプション）
    
    Returns:
        アプリケーション設定
    """
    global _config, _env_loaded
    
    try:
        if not _env_loaded:
            load_dotenv()
            _env_loaded = True
        
        if _config is None:
            if config_file and config_file.exists():
                # ファイルから読み込み
                _config = AppConfig.from_file(config_file)
            else:
                # デフォルトの初期化
                _config = AppConfig()
        
        return _config
    except Exception as e:
        raise RuntimeError(f"設定の読み込みに失敗しました: {str(e)}")
```

## メリット

1. **柔軟性**: 環境に応じて設定方法を選択可能
2. **可視性**: 設定内容が一覧で確認しやすい
3. **バージョン管理**: 設定ファイルをGit管理可能
4. **テスト容易性**: テスト用の設定ファイルを用意しやすい

## 注意点

1. **セキュリティ**: APIキーなどの機密情報は引き続き環境変数で管理
2. **後方互換性**: 既存の環境変数ベースの設定も継続サポート
3. **検証**: ファイルから読み込んだ設定も同様に検証が必要
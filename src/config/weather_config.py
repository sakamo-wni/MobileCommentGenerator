"""
天気予報統合機能の設定管理

後方互換性のためのラッパーモジュール
新しいコードでは以下から直接インポートすることを推奨:
- src.config.weather_settings
- src.config.langgraph_settings
- src.config.app_settings
"""

# 後方互換性のために全てのクラスと関数を再エクスポート
from .config import get_weather_config, get_langgraph_config
from .app_settings import (
    AppConfig,
    get_config,
    reload_config,
    validate_config,
    setup_environment_defaults,
)

# 互換性のためのWeatherConfigとLangGraphConfigのエイリアス
class WeatherConfig:
    """非推奨: get_weather_config()を使用してください"""
    def __new__(cls):
        return get_weather_config()

class LangGraphConfig:
    """非推奨: get_langgraph_config()を使用してください"""
    def __new__(cls):
        return get_langgraph_config()

__all__ = [
    "WeatherConfig",
    "LangGraphConfig",
    "AppConfig",
    "get_config",
    "reload_config",
    "validate_config",
    "setup_environment_defaults",
]


if __name__ == "__main__":
    # 設定テスト
    try:
        setup_environment_defaults()
        config = get_config()
        print("設定読み込み成功:")
        print(config.to_dict())

        # 設定検証
        validation_errors = validate_config(config)
        if validation_errors:
            print("\n設定検証エラー:")
            for category, errors in validation_errors.items():
                print(f"{category}:")
                for error in errors:
                    print(f"  - {error}")
        else:
            print("\n設定検証: 問題なし")

    except Exception as e:
        print(f"エラー: {str(e)}")
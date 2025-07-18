"""
天気予報統合機能の設定管理

後方互換性のためのラッパーモジュール
新しいコードでは以下から直接インポートすることを推奨:
- src.config.weather_settings
- src.config.langgraph_settings
- src.config.app_settings
"""

# 後方互換性のために全てのクラスと関数を再エクスポート

from __future__ import annotations
import logging
from .config import get_weather_config, get_langgraph_config
from .app_settings import (
    AppConfig,
    get_config,
    reload_config,
    validate_config,
    setup_environment_defaults,
)

logger = logging.getLogger(__name__)

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
    logging.basicConfig(level=logging.INFO)
    try:
        setup_environment_defaults()
        config = get_config()
        logger.info("設定読み込み成功:")
        logger.info(config.to_dict())

        # 設定検証
        validation_errors = validate_config(config)
        if validation_errors:
            logger.error("\n設定検証エラー:")
            for category, errors in validation_errors.items():
                logger.error(f"{category}:")
                for error in errors:
                    logger.error(f"  - {error}")
        else:
            logger.info("\n設定検証: 問題なし")

    except Exception as e:
        logger.error(f"エラー: {str(e)}")
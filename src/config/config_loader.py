"""設定ファイルの読み込みユーティリティ"""

import yaml
import os
from typing import Dict, Any, Optional
import jsonschema
import logging

logger = logging.getLogger(__name__)
_config_cache = {}

# 基本的な設定スキーマ
CONFIG_SCHEMAS = {
    'weather_thresholds': {
        'type': 'object',
        'properties': {
            'temperature': {'type': 'object'},
            'precipitation': {'type': 'object'},
            'wind_speed': {'type': 'object'}
        },
        'required': ['temperature', 'precipitation', 'wind_speed']
    }
}


def load_config(config_name: str, validate: bool = True) -> Dict[str, Any]:
    """YAMLファイルから設定を読み込む
    
    Args:
        config_name: 設定ファイル名（拡張子なし）
        validate: スキーマ検証を行うかどうか
        
    Returns:
        設定の辞書
        
    Raises:
        FileNotFoundError: 設定ファイルが見つからない場合
        yaml.YAMLError: YAML解析エラーの場合
        jsonschema.ValidationError: スキーマ検証エラーの場合
    """
    if config_name in _config_cache:
        return _config_cache[config_name]
    
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
    config_path = os.path.join(config_dir, f"{config_name}.yaml")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {config_path}: {e}")
        raise
    
    # スキーマ検証
    if validate and config_name in CONFIG_SCHEMAS:
        try:
            jsonschema.validate(config, CONFIG_SCHEMAS[config_name])
            logger.debug(f"Config validation successful for {config_name}")
        except jsonschema.ValidationError as e:
            logger.error(f"Config validation failed for {config_name}: {e.message}")
            raise
    
    _config_cache[config_name] = config
    return config


def validate_config(config_name: str, config_data: Dict[str, Any]) -> bool:
    """設定データの検証
    
    Args:
        config_name: 設定名
        config_data: 検証する設定データ
        
    Returns:
        検証結果（True: 成功, False: 失敗）
    """
    if config_name not in CONFIG_SCHEMAS:
        logger.warning(f"No schema defined for config: {config_name}")
        return True
    
    try:
        jsonschema.validate(config_data, CONFIG_SCHEMAS[config_name])
        return True
    except jsonschema.ValidationError as e:
        logger.error(f"Config validation failed: {e.message}")
        return False


def get_weather_thresholds() -> Dict[str, Any]:
    """天気関連の閾値設定を取得"""
    return load_config('weather_thresholds')
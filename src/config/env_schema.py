"""
環境変数スキーマの定義と検証

環境変数の一覧、型、デフォルト値を管理
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import os
import logging

logger = logging.getLogger(__name__)


class EnvVarType(Enum):
    """環境変数の型"""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    LIST = "list"  # カンマ区切りのリスト


@dataclass
class EnvVarSchema:
    """環境変数のスキーマ定義"""
    name: str
    type: EnvVarType
    default: Any
    description: str
    required: bool = False
    choices: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None


# 環境変数スキーマの定義
ENV_SCHEMA: List[EnvVarSchema] = [
    # API Keys
    EnvVarSchema("WXTECH_API_KEY", EnvVarType.STRING, "", "WxTech API key for weather data"),
    EnvVarSchema("OPENAI_API_KEY", EnvVarType.STRING, "", "OpenAI API key"),
    EnvVarSchema("ANTHROPIC_API_KEY", EnvVarType.STRING, "", "Anthropic API key"),
    EnvVarSchema("GEMINI_API_KEY", EnvVarType.STRING, "", "Google Gemini API key"),
    
    # API Settings
    EnvVarSchema("GEMINI_MODEL", EnvVarType.STRING, "gemini-1.5-flash", "Gemini model name"),
    EnvVarSchema("OPENAI_MODEL", EnvVarType.STRING, "gpt-4o-mini", "OpenAI model name"),
    EnvVarSchema("ANTHROPIC_MODEL", EnvVarType.STRING, "claude-3-haiku-20240307", "Anthropic model name"),
    EnvVarSchema("API_TIMEOUT", EnvVarType.INT, 30, "API timeout in seconds", min_value=1, max_value=300),
    
    # Weather Settings
    EnvVarSchema("WEATHER_FORECAST_HOURS_AHEAD", EnvVarType.INT, 12, "Hours ahead for weather forecast", min_value=1, max_value=72),
    EnvVarSchema("WEATHER_FORECAST_DAYS", EnvVarType.INT, 3, "Days of weather forecast", min_value=1, max_value=7),
    EnvVarSchema("WEATHER_CACHE_TTL", EnvVarType.INT, 3600, "Weather cache TTL in seconds", min_value=60),
    EnvVarSchema("WEATHER_CACHE_DIR", EnvVarType.STRING, "data/forecast_cache", "Weather cache directory"),
    
    # App Settings
    EnvVarSchema("APP_ENV", EnvVarType.STRING, "development", "Application environment", choices=["development", "staging", "production"]),
    EnvVarSchema("DEBUG", EnvVarType.BOOL, False, "Debug mode"),
    EnvVarSchema("LOG_LEVEL", EnvVarType.STRING, "INFO", "Log level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    EnvVarSchema("DATA_DIR", EnvVarType.STRING, "output", "Data output directory"),
    EnvVarSchema("CSV_DIR", EnvVarType.STRING, "output", "CSV output directory"),
    
    # Server Settings
    EnvVarSchema("API_HOST", EnvVarType.STRING, "0.0.0.0", "API server host"),
    EnvVarSchema("API_PORT", EnvVarType.INT, 8000, "API server port", min_value=1024, max_value=65535),
    EnvVarSchema("FRONTEND_PORT", EnvVarType.INT, 3000, "Frontend server port", min_value=1024, max_value=65535),
    EnvVarSchema("CORS_ORIGINS", EnvVarType.LIST, "", "Allowed CORS origins (comma-separated)"),
    
    # LLM Settings
    EnvVarSchema("DEFAULT_LLM_PROVIDER", EnvVarType.STRING, "gemini", "Default LLM provider", choices=["openai", "anthropic", "gemini"]),
    EnvVarSchema("LLM_TEMPERATURE", EnvVarType.FLOAT, 0.7, "LLM temperature", min_value=0.0, max_value=2.0),
    EnvVarSchema("LLM_MAX_TOKENS", EnvVarType.INT, 1000, "LLM max tokens", min_value=100, max_value=4000),
]


def parse_env_value(value: str, var_type: EnvVarType) -> Any:
    """環境変数の値を適切な型に変換"""
    if not value:
        return None
    
    try:
        if var_type == EnvVarType.STRING:
            return value
        elif var_type == EnvVarType.INT:
            return int(value)
        elif var_type == EnvVarType.FLOAT:
            return float(value)
        elif var_type == EnvVarType.BOOL:
            return value.lower() in ("true", "yes", "1", "on")
        elif var_type == EnvVarType.LIST:
            return [item.strip() for item in value.split(",") if item.strip()]
    except ValueError as e:
        logger.error(f"Failed to parse environment variable: {e}")
        return None


def validate_env_value(schema: EnvVarSchema, value: Any) -> bool:
    """環境変数の値を検証"""
    if value is None:
        return not schema.required
    
    # 選択肢の検証
    if schema.choices and value not in schema.choices:
        logger.warning(f"{schema.name} value '{value}' not in choices: {schema.choices}")
        return False
    
    # 数値範囲の検証
    if schema.type in (EnvVarType.INT, EnvVarType.FLOAT):
        if schema.min_value is not None and value < schema.min_value:
            logger.warning(f"{schema.name} value {value} is below minimum {schema.min_value}")
            return False
        if schema.max_value is not None and value > schema.max_value:
            logger.warning(f"{schema.name} value {value} is above maximum {schema.max_value}")
            return False
    
    return True


def load_env_with_schema() -> Dict[str, Any]:
    """スキーマに基づいて環境変数を読み込み、検証する"""
    env_values = {}
    validation_errors = []
    
    for schema in ENV_SCHEMA:
        # 環境変数の値を取得
        raw_value = os.getenv(schema.name)
        
        if raw_value is None:
            # デフォルト値を使用
            value = schema.default
        else:
            # 型変換
            value = parse_env_value(raw_value, schema.type)
            if value is None and schema.default is not None:
                value = schema.default
        
        # 検証
        if not validate_env_value(schema, value):
            validation_errors.append(f"{schema.name}: {schema.description}")
        
        env_values[schema.name] = value
    
    # 検証エラーがある場合は警告
    if validation_errors:
        logger.warning(f"Environment variable validation errors: {validation_errors}")
    
    return env_values


def generate_env_template() -> str:
    """環境変数テンプレートを生成"""
    lines = ["# Environment Variables Template", "# Generated from env_schema.py", ""]
    
    # カテゴリごとにグループ化
    categories = {
        "API Keys": [],
        "API Settings": [],
        "Weather Settings": [],
        "App Settings": [],
        "Server Settings": [],
        "LLM Settings": [],
    }
    
    for schema in ENV_SCHEMA:
        if "API_KEY" in schema.name:
            category = "API Keys"
        elif schema.name.startswith("WEATHER_"):
            category = "Weather Settings"
        elif schema.name.startswith("API_") or schema.name.endswith("_MODEL"):
            category = "API Settings"
        elif schema.name.startswith("LLM_") or schema.name == "DEFAULT_LLM_PROVIDER":
            category = "LLM Settings"
        elif schema.name in ("API_HOST", "API_PORT", "FRONTEND_PORT", "CORS_ORIGINS"):
            category = "Server Settings"
        else:
            category = "App Settings"
        
        categories[category].append(schema)
    
    # 各カテゴリの環境変数を出力
    for category, schemas in categories.items():
        if not schemas:
            continue
        
        lines.append(f"# {category}")
        lines.append("#" + "=" * (len(category) + 2))
        
        for schema in schemas:
            # 説明
            lines.append(f"# {schema.description}")
            if schema.required:
                lines.append("# REQUIRED")
            if schema.choices:
                lines.append(f"# Choices: {', '.join(map(str, schema.choices))}")
            if schema.min_value is not None or schema.max_value is not None:
                range_str = []
                if schema.min_value is not None:
                    range_str.append(f"min: {schema.min_value}")
                if schema.max_value is not None:
                    range_str.append(f"max: {schema.max_value}")
                lines.append(f"# Range: {', '.join(range_str)}")
            
            # 環境変数とデフォルト値
            if schema.type == EnvVarType.STRING and schema.default:
                default_value = f'"{schema.default}"'
            else:
                default_value = str(schema.default) if schema.default else ""
            
            lines.append(f"{schema.name}={default_value}")
            lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 環境変数テンプレートを生成
    logger.info(generate_env_template())
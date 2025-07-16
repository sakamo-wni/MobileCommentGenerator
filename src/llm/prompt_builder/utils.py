"""
Prompt builder utilities

プロンプトビルダーのユーティリティ関数
"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


def create_simple_prompt(weather_description: str, temperature: str, location: str = "") -> str:
    """シンプルなプロンプトを生成（レガシー互換性用）
    
    Args:
        weather_description: 天気の説明
        temperature: 気温
        location: 地点名（オプション）
        
    Returns:
        生成されたプロンプト
    """
    location_part = f"{location}の" if location else ""
    return (
        f"{location_part}今の天気は{weather_description}、"
        f"気温は{temperature}°Cです。"
        f"この天気に合った短いコメントを20文字以内で生成してください。"
        f"絵文字は使わないでください。"
    )


def format_weather_info(weather_data: dict[str, str]) -> str:
    """天気情報を整形
    
    Args:
        weather_data: 天気データの辞書
        
    Returns:
        整形された天気情報文字列
    """
    lines = []
    
    # 基本情報
    if "temperature" in weather_data:
        lines.append(f"気温: {weather_data['temperature']}°C")
    if "weather" in weather_data:
        lines.append(f"天気: {weather_data['weather']}")
    if "humidity" in weather_data:
        lines.append(f"湿度: {weather_data['humidity']}%")
    if "precipitation" in weather_data:
        lines.append(f"降水量: {weather_data['precipitation']}mm")
    if "wind_speed" in weather_data:
        lines.append(f"風速: {weather_data['wind_speed']}m/s")
    
    return "\n".join(lines)


def get_time_of_day_category(hour: int) -> str:
    """時間帯カテゴリを取得
    
    Args:
        hour: 時間（0-23）
        
    Returns:
        時間帯カテゴリ（朝、昼、夕方、夜）
    """
    if 4 <= hour < 10:
        return "朝"
    elif 10 <= hour < 16:
        return "昼"
    elif 16 <= hour < 19:
        return "夕方"
    else:
        return "夜"


def get_season_category(month: int) -> str:
    """季節カテゴリを取得
    
    Args:
        month: 月（1-12）
        
    Returns:
        季節カテゴリ（春、夏、秋、冬）
    """
    if month in [3, 4, 5]:
        return "春"
    elif month in [6, 7, 8]:
        return "夏"
    elif month in [9, 10, 11]:
        return "秋"
    else:
        return "冬"


def truncate_examples(examples: list[str], max_count: int = 5, max_chars: int = 500) -> list[str]:
    """例文リストを制限内に収める
    
    Args:
        examples: 例文のリスト
        max_count: 最大例文数
        max_chars: 最大文字数
        
    Returns:
        制限内に収まった例文リスト
    """
    if not examples:
        return []
    
    # 件数制限
    truncated = examples[:max_count]
    
    # 文字数制限
    total_chars = 0
    result = []
    
    for example in truncated:
        if total_chars + len(example) > max_chars:
            break
        result.append(example)
        total_chars += len(example)
    
    return result
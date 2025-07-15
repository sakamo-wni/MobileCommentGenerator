"""気温差分析モジュール"""

from typing import Any
import logging
from src.config.weather_config import get_config

logger = logging.getLogger(__name__)


def analyze_temperature_differences(temperature_differences: dict[str, float | None], current_temp: float) -> dict[str, Any]:
    """気温差を分析して特徴を抽出
    
    温度差の閾値について：
    - 前日との差 5.0℃: 人体が明確に体感できる温度差として設定。気象学的に「顕著な変化」とされる基準
    - 12時間前との差 3.0℃: 半日での変化として、体調管理に影響する可能性がある基準値
    - 日較差 15.0℃（大）/10.0℃（中）: 健康影響の観点から、15℃以上は要注意、10℃以上は留意すべき差として設定
    
    Args:
        temperature_differences: 気温差の辞書
        current_temp: 現在の気温
        
    Returns:
        気温差の分析結果
    """
    # 設定から閾値を取得
    config = get_config()
    threshold_previous_day = config.weather.temp_diff_threshold_previous_day
    threshold_12hours = config.weather.temp_diff_threshold_12hours
    threshold_daily_large = config.weather.daily_temp_range_threshold_large
    threshold_daily_medium = config.weather.daily_temp_range_threshold_medium
    
    analysis = {
        "has_significant_change": False,
        "change_type": None,
        "change_magnitude": None,
        "commentary": []
    }
    
    try:
        # 前日との比較
        prev_day_diff = temperature_differences.get("previous_day_diff")
        if prev_day_diff is not None:
            if abs(prev_day_diff) >= threshold_previous_day:
                analysis["has_significant_change"] = True
                if prev_day_diff > 0:
                    analysis["change_type"] = "warmer_than_yesterday"
                    analysis["commentary"].append(f"前日より{prev_day_diff:.1f}℃高い")
                else:
                    analysis["change_type"] = "cooler_than_yesterday"
                    analysis["commentary"].append(f"前日より{abs(prev_day_diff):.1f}℃低い")
                
                # 変化の程度を分類
                if abs(prev_day_diff) >= 10.0:
                    analysis["change_magnitude"] = "large"
                elif abs(prev_day_diff) >= 7.0:
                    analysis["change_magnitude"] = "moderate"
                else:
                    analysis["change_magnitude"] = "small"
        
        # 12時間前との比較
        twelve_hours_diff = temperature_differences.get("twelve_hours_ago_diff")
        if twelve_hours_diff is not None:
            if abs(twelve_hours_diff) >= threshold_12hours:
                if twelve_hours_diff > 0:
                    analysis["commentary"].append(f"12時間前より{twelve_hours_diff:.1f}℃上昇")
                else:
                    analysis["commentary"].append(f"12時間前より{abs(twelve_hours_diff):.1f}℃下降")
        
        # 日較差の分析
        daily_range = temperature_differences.get("daily_range")
        if daily_range is not None:
            if daily_range >= threshold_daily_large:
                analysis["commentary"].append(f"日較差が大きい（{daily_range:.1f}℃）")
            elif daily_range >= threshold_daily_medium:
                analysis["commentary"].append(f"やや日較差あり（{daily_range:.1f}℃）")
        
        # 設定から温度閾値を取得
        config = get_config()
        temp_hot = config.weather.temp_threshold_hot
        temp_warm = config.weather.temp_threshold_warm  
        temp_cool = config.weather.temp_threshold_cool
        temp_cold = config.weather.temp_threshold_cold
        
        # 現在の気温レベルに応じたコメント
        if current_temp >= temp_hot:
            analysis["commentary"].append("暑い気温")
        elif current_temp >= temp_warm:
            analysis["commentary"].append("暖かい気温")
        elif current_temp <= temp_cold:
            analysis["commentary"].append("寒い気温")
        elif current_temp <= temp_cool:
            analysis["commentary"].append("涼しい気温")
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"気温差分析中にエラー: {type(e).__name__}: {e}")
    except Exception as e:
        logger.error(f"気温差分析中に予期しないエラー: {type(e).__name__}: {e}", exc_info=True)
    
    return analysis
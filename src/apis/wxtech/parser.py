"""
WxTech API データパーサー

APIレスポンスをドメインモデルに変換する処理を管理
"""

from typing import Any
import warnings
from datetime import datetime

from src.data.weather_data import WeatherForecast, WeatherForecastCollection
from src.apis.wxtech.mappings import (
    convert_weather_code,
    get_weather_description,
    convert_wind_direction
)


def parse_forecast_response(
    raw_data: dict[str, Any], location_name: str
) -> WeatherForecastCollection:
    """API レスポンスを WeatherForecastCollection に変換
    
    Args:
        raw_data: API からの生データ
        location_name: 地点名
        
    Returns:
        天気予報コレクション
    """
    wxdata = raw_data["wxdata"][0]
    forecasts = []
    
    # 短期予報（時間別）の処理
    if "srf" in wxdata:
        for forecast_data in wxdata["srf"]:
            try:
                forecast = parse_single_forecast(
                    forecast_data, location_name, is_hourly=True
                )
                forecasts.append(forecast)
            except Exception as e:
                warnings.warn(f"時間別予報の解析に失敗: {str(e)}")
                continue
    
    # 中期予報（日別）の処理
    if "mrf" in wxdata:
        for forecast_data in wxdata["mrf"]:
            try:
                forecast = parse_single_forecast(
                    forecast_data, location_name, is_hourly=False
                )
                forecasts.append(forecast)
            except Exception as e:
                warnings.warn(f"日別予報の解析に失敗: {str(e)}")
                continue
    
    return WeatherForecastCollection(location=location_name, forecasts=forecasts)


def parse_single_forecast(
    data: dict[str, Any], location_name: str, is_hourly: bool = True
) -> WeatherForecast:
    """単一の予報データを WeatherForecast に変換
    
    Args:
        data: 予報データ
        location_name: 地点名
        is_hourly: 時間別予報かどうか
        
    Returns:
        天気予報オブジェクト
    """
    # 日時の解析
    date_str = data["date"]
    forecast_datetime = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    
    # 天気コードの変換
    weather_code = str(data["wx"])
    weather_condition = convert_weather_code(weather_code)
    weather_description = get_weather_description(weather_code)
    
    # 風向きの変換
    wind_dir_index = data.get("wnddir", 0)
    wind_direction, wind_degrees = convert_wind_direction(wind_dir_index)
    
    # 気温の取得（時間別と日別で異なるフィールド）
    if is_hourly:
        temperature = float(data["temp"])
    else:
        # 日別予報の場合は最高気温を使用
        temperature = float(data.get("maxtemp", data.get("temp", 0)))
    
    # 降水量の取得とデバッグ
    precipitation_value = data.get("prec", 0)
    import logging
    logger = logging.getLogger(__name__)
    
    # 常にログを出力（降水量0も含む）
    if forecast_datetime.hour in [9, 12, 15, 18]:
        logger.info(
            f"APIレスポンス解析: {forecast_datetime.strftime('%Y-%m-%d %H:%M')} - "
            f"降水量: {precipitation_value}mm, 天気: {weather_description}, "
            f"天気コード: {weather_code}"
        )
    
    return WeatherForecast(
        location=location_name,
        datetime=forecast_datetime,
        temperature=temperature,
        weather_code=weather_code,
        weather_condition=weather_condition,
        weather_description=weather_description,
        precipitation=float(precipitation_value),
        humidity=float(data.get("rhum", 0)),
        wind_speed=float(data.get("wndspd", 0)),
        wind_direction=wind_direction,
        wind_direction_degrees=wind_degrees,
        raw_data=data,
    )


def analyze_response_patterns(test_results: dict[str, Any]) -> dict[str, Any]:
    """レスポンスパターンを分析して特定時刻指定の効果を確認する"""
    
    analysis = {
        "unique_response_sizes": set(),
        "unique_srf_counts": set(),
        "unique_mrf_counts": set(),
        "minimum_data_response": None,
        "appears_time_specific": False
    }
    
    for name, result in test_results.items():
        if result.get("success"):
            analysis["unique_response_sizes"].add(result.get("response_size", 0))
            analysis["unique_srf_counts"].add(result.get("srf_count", 0))
            analysis["unique_mrf_counts"].add(result.get("mrf_count", 0))
            
            # 最小データレスポンスを特定
            if (analysis["minimum_data_response"] is None or 
                result.get("srf_count", 0) < analysis["minimum_data_response"]["srf_count"]):
                analysis["minimum_data_response"] = {
                    "name": name,
                    "srf_count": result.get("srf_count", 0),
                    "mrf_count": result.get("mrf_count", 0)
                }
    
    # 異なるデータサイズがあるかをチェック
    analysis["appears_time_specific"] = (
        len(analysis["unique_srf_counts"]) > 1 or 
        len(analysis["unique_response_sizes"]) > 1
    )
    
    # セットをリストに変換（JSONシリアライズ用）
    analysis["unique_response_sizes"] = sorted(list(analysis["unique_response_sizes"]))
    analysis["unique_srf_counts"] = sorted(list(analysis["unique_srf_counts"]))
    analysis["unique_mrf_counts"] = sorted(list(analysis["unique_mrf_counts"]))
    
    return analysis
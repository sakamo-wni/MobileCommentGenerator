#!/usr/bin/env python3
"""天気予報実装の詳細検証"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.apis.wxtech import WxTechAPIClient
from src.nodes.weather_forecast.data_validator import WeatherDataValidator
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection

# 環境変数をロード
load_dotenv()


def test_time_filtering():
    """時刻フィルタリングのテスト"""
    print("=== 時刻フィルタリングテスト ===\n")
    
    api_key = os.getenv("WXTECH_API_KEY")
    if not api_key:
        print("エラー: WXTECH_API_KEYが設定されていません")
        return
    
    client = WxTechAPIClient(api_key, enable_cache=True)
    
    # 東京の天気予報を取得
    lat, lon = 35.6762, 139.6503
    forecast_collection = client.get_forecast_for_next_day_hours_optimized(lat, lon)
    
    print(f"取得した予報数: {len(forecast_collection.forecasts)}")
    print("\n時刻別予報:")
    for f in forecast_collection.forecasts:
        print(f"  {f.datetime.strftime('%Y-%m-%d %H:%M')} - {f.weather_description}, "
              f"{f.temperature}°C, 降水量{f.precipitation}mm")


def test_priority_logic():
    """優先度ロジックのテスト"""
    print("\n=== 優先度ロジックテスト ===\n")
    
    # テスト用の天気予報データを作成
    test_forecasts = [
        WeatherForecast(
            location="テスト",
            datetime=datetime.now().replace(hour=9),
            temperature=25.0,
            weather_code="100",
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60,
            wind_speed=3.0,
            wind_direction=WindDirection.N,
            wind_direction_degrees=0
        ),
        WeatherForecast(
            location="テスト",
            datetime=datetime.now().replace(hour=12),
            temperature=30.0,
            weather_code="200",
            weather_condition=WeatherCondition.CLOUDY,
            weather_description="くもり",
            precipitation=0.0,
            humidity=65,
            wind_speed=4.0,
            wind_direction=WindDirection.N,
            wind_direction_degrees=0
        ),
        WeatherForecast(
            location="テスト",
            datetime=datetime.now().replace(hour=15),
            temperature=35.5,  # 猛暑
            weather_code="100",
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=55,
            wind_speed=2.0,
            wind_direction=WindDirection.S,
            wind_direction_degrees=180
        ),
        WeatherForecast(
            location="テスト",
            datetime=datetime.now().replace(hour=18),
            temperature=28.0,
            weather_code="300",
            weather_condition=WeatherCondition.RAIN,
            weather_description="雨",
            precipitation=5.0,  # 雨
            humidity=80,
            wind_speed=5.0,
            wind_direction=WindDirection.E,
            wind_direction_degrees=90
        )
    ]
    
    # 優先度選択をテスト
    validator = WeatherDataValidator()
    selected = validator.select_priority_forecast(test_forecasts)
    
    print("テストデータ:")
    for f in test_forecasts:
        print(f"  {f.datetime.strftime('%H:%M')} - {f.weather_description}, "
              f"{f.temperature}°C, 降水量{f.precipitation}mm")
    
    print(f"\n選択結果: {selected.datetime.strftime('%H:%M')} - {selected.weather_description}")
    print(f"理由: 降水量{selected.precipitation}mm（雨は最優先）")
    
    # 雨がない場合のテスト
    print("\n--- 雨がない場合のテスト ---")
    test_forecasts_no_rain = [f for f in test_forecasts if f.precipitation == 0]
    selected_no_rain = validator.select_priority_forecast(test_forecasts_no_rain)
    
    print("テストデータ（雨なし）:")
    for f in test_forecasts_no_rain:
        print(f"  {f.datetime.strftime('%H:%M')} - {f.weather_description}, "
              f"{f.temperature}°C")
    
    print(f"\n選択結果: {selected_no_rain.datetime.strftime('%H:%M')} - {selected_no_rain.weather_description}")
    print(f"理由: 気温{selected_no_rain.temperature}°C（35°C以上の猛暑）")


def test_actual_workflow():
    """実際のワークフローでの動作確認"""
    print("\n=== 実際のワークフローテスト ===\n")
    
    from src.workflows.comment_generation_workflow import run_comment_generation
    
    # 複数地点でテスト
    locations = ["東京", "大阪", "那覇"]
    
    for location in locations:
        print(f"\n{location}の結果:")
        result = run_comment_generation(
            location_name=location,
            target_datetime=datetime.now(),
            llm_provider="gemini"
        )
        
        if result["success"]:
            metadata = result.get("generation_metadata", {})
            weather_meta = metadata.get("weather_forecast_metadata", {})
            
            # 時刻フィルタリング結果
            if "selected_hours" in weather_meta:
                print(f"  選択された時刻: {weather_meta['selected_hours']}")
            
            # 優先度選択結果
            if "priority_reason" in weather_meta:
                print(f"  優先度選択理由: {weather_meta['priority_reason']}")
            
            print(f"  天気: {metadata.get('weather_condition', '不明')}")
            print(f"  気温: {metadata.get('temperature', '不明')}°C")
            print(f"  コメント: {result['final_comment']}")
        else:
            print(f"  エラー: {result.get('error', '不明')}")


if __name__ == "__main__":
    test_time_filtering()
    test_priority_logic()
    test_actual_workflow()
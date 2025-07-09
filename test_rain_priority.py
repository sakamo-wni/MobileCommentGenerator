#!/usr/bin/env python3
"""雨予報の優先順位テスト"""

import logging
from datetime import datetime, timedelta
import pytz

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 必要なモジュールをインポート
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.nodes.weather_forecast.data_validator import WeatherDataValidator

# テストデータを作成
def create_test_forecast(hour, temp, desc, condition, precipitation):
    """テスト用の予報データを作成"""
    jst = pytz.timezone('Asia/Tokyo')
    base_date = datetime.now(jst).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    return WeatherForecast(
        location="さいたま",
        datetime=base_date.replace(hour=hour),
        temperature=temp,
        weather_code="",
        weather_condition=condition,
        weather_description=desc,
        precipitation=precipitation,
        humidity=70,
        wind_speed=2.0,
        wind_direction="北",
        wind_direction_degrees=0,
        raw_data={}
    )

# さいたまの予報をシミュレート
saitama_forecasts = [
    create_test_forecast(9, 30.0, "晴れ", WeatherCondition.CLEAR, 0.0),
    create_test_forecast(12, 35.0, "晴れ", WeatherCondition.EXTREME_HEAT, 0.0),
    create_test_forecast(15, 34.0, "小雨", WeatherCondition.RAIN, 1.0),  # 15:00 雨1mm
    create_test_forecast(18, 32.0, "小雨", WeatherCondition.RAIN, 2.0),  # 18:00 雨2mm
]

# バリデータを作成
validator = WeatherDataValidator()

# 優先度選択を実行
print("=== さいたまの予報データ ===")
for f in saitama_forecasts:
    print(f"{f.datetime.strftime('%H:%M')}: {f.weather_description}, {f.temperature}°C, 降水量{f.precipitation}mm")

print("\n=== 優先度選択実行 ===")
selected = validator.select_priority_forecast(saitama_forecasts)

print(f"\n=== 選択結果 ===")
print(f"選択された時刻: {selected.datetime.strftime('%H:%M')}")
print(f"天気: {selected.weather_description}")
print(f"気温: {selected.temperature}°C")
print(f"降水量: {selected.precipitation}mm")
print(f"天気条件: {selected.weather_condition.value}")
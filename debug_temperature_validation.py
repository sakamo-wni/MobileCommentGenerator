#!/usr/bin/env python3
"""温度バリデーションのデバッグ"""

from datetime import datetime
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.data.past_comment import PastComment, CommentType
from src.utils.validators.temperature_validator import TemperatureValidator


def test_temperature_validation():
    """温度バリデーションをテスト"""
    print("=== 温度バリデーションテスト ===\n")
    
    # テスト用の天気データ
    weather_30c = WeatherForecast(
        location="那覇",
        datetime=datetime.now(),
        temperature=30.0,
        weather_code="200",
        weather_condition=WeatherCondition.CLOUDY,
        weather_description="くもり",
        precipitation=0.0,
        humidity=70,
        wind_speed=4.0,
        wind_direction=WindDirection.S,
        wind_direction_degrees=180
    )
    
    weather_26c = WeatherForecast(
        location="東京",
        datetime=datetime.now(),
        temperature=26.0,
        weather_code="200",
        weather_condition=WeatherCondition.CLOUDY,
        weather_description="くもり",
        precipitation=0.0,
        humidity=65,
        wind_speed=3.0,
        wind_direction=WindDirection.N,
        wind_direction_degrees=0
    )
    
    weather_35c = WeatherForecast(
        location="大阪",
        datetime=datetime.now(),
        temperature=35.0,
        weather_code="100",
        weather_condition=WeatherCondition.CLEAR,
        weather_description="晴れ",
        precipitation=0.0,
        humidity=55,
        wind_speed=2.0,
        wind_direction=WindDirection.S,
        wind_direction_degrees=180
    )
    
    # テスト用のコメント
    test_comments = [
        ("昼間でも肌寒い", "薄着注意"),
        ("朝はひんやり", "朝晩と昼間の体感差に注意"),
        ("朝は冷え込む", "朝昼の気温差に注意"),
        ("昼間は薄着でも快適", "水分補給を"),
        ("暑さ厳しい", "熱中症対策を"),
        ("雲が多め", "紫外線対策を忘れずに")
    ]
    
    validator = TemperatureValidator()
    
    # 各天気条件でテスト
    test_cases = [
        ("東京（26°C）", weather_26c),
        ("那覇（30°C）", weather_30c),
        ("大阪（35°C）", weather_35c)
    ]
    
    for location_name, weather in test_cases:
        print(f"\n{location_name}のテスト:")
        print(f"気温: {weather.temperature}°C")
        print("---")
        
        for weather_comment, advice in test_comments:
            # テスト用のPastCommentオブジェクトを作成
            comment = PastComment(
                location=location_name,
                datetime=datetime.now(),
                weather_condition="くもり",
                comment_text=weather_comment,
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=weather.temperature,
                raw_data={"advice": advice}
            )
            
            # バリデーション実行
            is_valid, reason = validator.validate(comment, weather)
            
            if not is_valid:
                print(f"  ❌ \"{weather_comment}\" - {reason}")
            else:
                print(f"  ✅ \"{weather_comment}\" - OK")


if __name__ == "__main__":
    test_temperature_validation()
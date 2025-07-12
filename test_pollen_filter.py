"""花粉フィルタリング機能のテスト"""

from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.validators.pollen_validator import PollenValidator
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.past_comment import PastComment, CommentType

def test_pollen_filtering():
    print("=== 花粉フィルタリングテスト ===\n")
    
    validator = PollenValidator()
    
    # テストケース1: 7月の花粉コメント（不適切）
    print("1. 7月の花粉コメント:")
    july_weather = WeatherForecast(
        location="東京",
        datetime=datetime(2024, 7, 15),
        temperature=25.0,
        weather_code="clear",
        weather_condition=WeatherCondition.CLEAR,
        weather_description="晴れ",
        precipitation=0.0,
        humidity=60,
        wind_speed=3.0,
        wind_direction="南",
        wind_direction_degrees=180,
        raw_data={}
    )
    
    pollen_comment = PastComment(
        comment_text="花粉が多く飛散しています。マスクで花粉対策を",
        location="東京",
        weather_condition="晴れ",
        temperature=25.0,
        comment_type=CommentType.WEATHER_COMMENT,
        usage_count=5,
        datetime=datetime(2024, 7, 15)
    )
    
    is_valid, reason = validator.validate(pollen_comment, july_weather)
    print(f"  コメント: {pollen_comment.comment_text}")
    print(f"  結果: {'有効' if is_valid else '無効'}")
    print(f"  理由: {reason}\n")
    
    # テストケース2: 3月の花粉コメント（適切）
    print("2. 3月の花粉コメント:")
    march_weather = WeatherForecast(
        location="東京",
        datetime=datetime(2024, 3, 15),
        temperature=15.0,
        weather_code="clear",
        weather_condition=WeatherCondition.CLEAR,
        weather_description="晴れ",
        precipitation=0.0,
        humidity=50,
        wind_speed=3.0,
        wind_direction="南",
        wind_direction_degrees=180,
        raw_data={}
    )
    
    is_valid, reason = validator.validate(pollen_comment, march_weather)
    print(f"  コメント: {pollen_comment.comment_text}")
    print(f"  結果: {'有効' if is_valid else '無効'}")
    print(f"  理由: {reason}\n")
    
    # テストケース3: 雨天時の花粉コメント（不適切）
    print("3. 雨天時の花粉コメント:")
    rain_weather = WeatherForecast(
        location="東京",
        datetime=datetime(2024, 3, 15),
        temperature=15.0,
        weather_code="rain",
        weather_condition=WeatherCondition.RAIN,
        weather_description="雨",
        precipitation=5.0,
        humidity=80,
        wind_speed=3.0,
        wind_direction="南",
        wind_direction_degrees=180,
        raw_data={}
    )
    
    is_valid, reason = validator.validate(pollen_comment, rain_weather)
    print(f"  コメント: {pollen_comment.comment_text}")
    print(f"  天気: {rain_weather.weather_description}")
    print(f"  降水量: {rain_weather.precipitation}mm")
    print(f"  結果: {'有効' if is_valid else '無効'}")
    print(f"  理由: {reason}\n")
    
    # テストケース4: 花粉を含まないコメント（常に有効）
    print("4. 花粉を含まないコメント:")
    normal_comment = PastComment(
        comment_text="今日は気持ちの良い晴天です",
        location="東京",
        weather_condition="晴れ",
        temperature=25.0,
        comment_type=CommentType.WEATHER_COMMENT,
        usage_count=5,
        datetime=datetime(2024, 7, 15)
    )
    
    is_valid, reason = validator.validate(normal_comment, july_weather)
    print(f"  コメント: {normal_comment.comment_text}")
    print(f"  結果: {'有効' if is_valid else '無効'}")
    print(f"  理由: {reason if reason else '検証OK'}\n")

if __name__ == "__main__":
    test_pollen_filtering()
#!/usr/bin/env python3
"""海岸地域バリデーションのテスト"""

from datetime import datetime
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.data.past_comment import PastComment, CommentType
from src.utils.validators.coastal_validator import CoastalValidator
from src.utils.validators.weather_transition_validator import WeatherTransitionValidator


def test_coastal_validation():
    """海岸地域バリデーションのテスト"""
    print("=== 海岸地域バリデーションテスト ===\n")
    
    validator = CoastalValidator()
    
    # テスト用の地域と天気データ
    test_cases = [
        ("東京", False),  # 内陸
        ("銚子", True),   # 海岸
        ("長野", False),  # 内陸
        ("横浜", True),   # 海岸
        ("京都", False),  # 内陸
    ]
    
    # 海岸関連のコメント
    coastal_comments = [
        "高波で海は危険",
        "引き続き沿岸は高波注意",
        "海は高波に注意",
        "海上はしける",
        "港は強風注意"
    ]
    
    for location, is_coastal in test_cases:
        print(f"\n{location}（{'海岸' if is_coastal else '内陸'}）のテスト:")
        
        weather = WeatherForecast(
            location=location,
            datetime=datetime.now(),
            temperature=25.0,
            weather_code="200",
            weather_condition=WeatherCondition.CLOUDY,
            weather_description="くもり",
            precipitation=0.0,
            humidity=65,
            wind_speed=5.0,
            wind_direction=WindDirection.N,
            wind_direction_degrees=0
        )
        
        for comment_text in coastal_comments:
            comment = PastComment(
                location=location,
                datetime=datetime.now(),
                weather_condition="くもり",
                comment_text=comment_text,
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=25.0,
                raw_data={"advice": ""}
            )
            
            is_valid, reason = validator.validate(comment, weather)
            
            if is_valid:
                print(f"  ✅ \"{comment_text}\" - OK")
            else:
                print(f"  ❌ \"{comment_text}\" - {reason}")


def test_weather_transition_validation():
    """天気推移バリデーションのテスト"""
    print("\n\n=== 天気推移バリデーションテスト ===\n")
    
    validator = WeatherTransitionValidator()
    
    # テスト用の天気データ（晴れ）
    weather_clear = WeatherForecast(
        location="東京",
        datetime=datetime.now(),
        temperature=25.0,
        weather_code="100",
        weather_condition=WeatherCondition.CLEAR,
        weather_description="晴れ",
        precipitation=0.0,
        humidity=50,
        wind_speed=3.0,
        wind_direction=WindDirection.N,
        wind_direction_degrees=0
    )
    
    # テスト用の天気データ（雨）
    weather_rain = WeatherForecast(
        location="東京",
        datetime=datetime.now(),
        temperature=20.0,
        weather_code="300",
        weather_condition=WeatherCondition.RAIN,
        weather_description="雨",
        precipitation=5.0,
        humidity=80,
        wind_speed=4.0,
        wind_direction=WindDirection.E,
        wind_direction_degrees=90
    )
    
    # 天気推移関連のコメント
    transition_comments = [
        ("天気回復へ", ""),
        ("段々と天気回復へ", ""),
        ("天気下り坂", ""),
        ("雨が降り出す", ""),
        ("晴れ間が広がる", "")
    ]
    
    print("晴れの場合:")
    for comment_text, advice in transition_comments:
        comment = PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="晴れ",
            comment_text=comment_text,
            comment_type=CommentType.WEATHER_COMMENT,
            temperature=25.0,
            raw_data={"advice": advice}
        )
        
        is_valid, reason = validator.validate(comment, weather_clear)
        
        if is_valid:
            print(f"  ✅ \"{comment_text}\" - OK")
        else:
            print(f"  ❌ \"{comment_text}\" - {reason}")
    
    print("\n雨の場合:")
    for comment_text, advice in transition_comments:
        comment = PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text=comment_text,
            comment_type=CommentType.WEATHER_COMMENT,
            temperature=20.0,
            raw_data={"advice": advice}
        )
        
        is_valid, reason = validator.validate(comment, weather_rain)
        
        if is_valid:
            print(f"  ✅ \"{comment_text}\" - OK")
        else:
            print(f"  ❌ \"{comment_text}\" - {reason}")


if __name__ == "__main__":
    test_coastal_validation()
    test_weather_transition_validation()
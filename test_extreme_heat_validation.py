"""猛暑時のコメント選択バリデーションテスト"""

import sys
import logging
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO)

# パスを追加
sys.path.append('.')

from src.data.location import Location
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment, CommentType
from src.utils.validators.temperature_validator import TemperatureValidator
from src.utils.validators.weather_comment_validator import WeatherCommentValidator

def test_temperature_validation():
    """温度バリデーションのテスト"""
    
    # バリデータの初期化
    temp_validator = TemperatureValidator()
    weather_validator = WeatherCommentValidator()
    
    # テスト用の天気データ（35°C）
    from src.data.location_manager import LocationManager
    location_manager = LocationManager()
    location = location_manager.get_location("京都")
    
    from src.data.weather_data import WindDirection, WeatherCondition
    
    weather_35c = WeatherForecast(
        location=location.name,
        weather_code="100",
        weather_condition=WeatherCondition.EXTREME_HEAT,
        weather_description="猛暑",
        temperature=35.0,
        humidity=56,
        wind_speed=4,
        wind_direction=WindDirection.N,
        wind_direction_degrees=0,
        precipitation=0.0,
        datetime=datetime.now()
    )
    
    weather_30c = WeatherForecast(
        location=location.name,
        weather_code="200",
        weather_condition=WeatherCondition.CLOUDY,
        weather_description="うすぐもり",
        temperature=30.0,
        humidity=60,
        wind_speed=3,
        wind_direction=WindDirection.N,
        wind_direction_degrees=0,
        precipitation=0.0,
        datetime=datetime.now()
    )
    
    # テストコメント
    test_comments = [
        ("朝は冷え込む　空の変化に注意", "30°Cで「冷え込む」"),
        ("天気回復へ　朝昼の気温差に注意", "35°Cで猛暑への言及なし"),
        ("猛暑日　熱中症に厳重警戒を", "35°Cで適切"),
        ("厳しい暑さ　こまめな水分補給を", "35°Cで適切"),
        ("雲優勢の空　朝晩と昼の気温差に注意", "特に問題なし"),
    ]
    
    print("=== 温度バリデーションテスト ===\n")
    
    # 30°Cでのテスト
    print("30°Cでのテスト:")
    for comment_text, description in test_comments:
        comment = PastComment(
            location="京都",
            datetime=datetime.now(),
            comment_type=CommentType.WEATHER_COMMENT,
            comment_text=comment_text,
            weather_condition="晴れ",
            usage_count=1,
            raw_data={}
        )
        
        is_valid, reason = temp_validator.validate(comment, weather_30c)
        print(f"  {'✅' if is_valid else '❌'} \"{comment_text}\" - {reason if not is_valid else 'OK'}")
    
    print("\n35°Cでのテスト:")
    for comment_text, description in test_comments:
        comment = PastComment(
            location="京都",
            datetime=datetime.now(),
            comment_type=CommentType.WEATHER_COMMENT,
            comment_text=comment_text,
            weather_condition="晴れ",
            usage_count=1,
            raw_data={}
        )
        
        # 温度バリデーション
        temp_valid, temp_reason = temp_validator.validate(comment, weather_35c)
        
        # 総合バリデーション
        weather_valid, weather_reason = weather_validator.validate_comment(comment, weather_35c)
        
        print(f"  {'✅' if weather_valid else '❌'} \"{comment_text}\" - {weather_reason if not weather_valid else 'OK'}")
        if not temp_valid:
            print(f"     └─ 温度: {temp_reason}")

    # 必須キーワードチェック
    print("\n=== 35°C時の必須キーワードチェック ===")
    print("※現在の実装では猛暑時の必須キーワードチェックは実装されていません")
    print("※温度バリデータは不適切な表現を除外するのみで、必須表現のチェックはしていません")

if __name__ == "__main__":
    test_temperature_validation()
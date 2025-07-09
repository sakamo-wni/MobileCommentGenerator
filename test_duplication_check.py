#!/usr/bin/env python3
"""
重複表現検証のテスト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pytz
from src.utils.validators.consistency_validator import ConsistencyValidator
from src.data.weather_data import WeatherForecast

def test_duplication_detection():
    """重複表現の検出テスト"""
    
    validator = ConsistencyValidator()
    jst = pytz.timezone("Asia/Tokyo")
    
    # ダミーの天気データ
    weather_data = WeatherForecast(
        location="テスト地点",
        datetime=datetime.now(jst),
        temperature=30.0,
        weather_code="200",
        weather_condition="cloudy",
        weather_description="くもり",
        precipitation=0.0,
        humidity=60.0,
        wind_speed=2.0,
        wind_direction="north",
        wind_direction_degrees=0
    )
    
    # テストケース
    test_cases = [
        {
            "weather": "朝昼の気温差大",
            "advice": "朝晩と昼間の気温差に注意",
            "expected": False,  # 重複として検出されるべき
            "description": "気温差の繰り返し"
        },
        {
            "weather": "雨が降りやすく",
            "advice": "急な雨に注意",
            "expected": False,  # 重複として検出されるべき
            "description": "雨注意の繰り返し"
        },
        {
            "weather": "暑さに注意",
            "advice": "熱中症対策を",
            "expected": False,  # 重複として検出されるべき
            "description": "暑さ注意の繰り返し"
        },
        {
            "weather": "過ごしやすい天気",
            "advice": "蒸し暑い一日",
            "expected": False,  # 矛盾として検出されるべき
            "description": "温度感覚の矛盾"
        },
        {
            "weather": "傘が必要",
            "advice": "傘を忘れずに",
            "expected": False,  # 重複として検出されるべき
            "description": "傘の重複"
        },
        {
            "weather": "晴れ間が広がる",
            "advice": "紫外線対策を忘れずに",
            "expected": True,  # 補完的な関係でOK
            "description": "補完的な関係"
        }
    ]
    
    print("重複表現検証テスト")
    print("=" * 60)
    
    for test in test_cases:
        is_consistent, reason = validator.validate_comment_pair_consistency(
            test["weather"],
            test["advice"],
            weather_data
        )
        
        passed = is_consistent == test["expected"]
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"\n{status} {test['description']}")
        print(f"  天気: {test['weather']}")
        print(f"  アドバイス: {test['advice']}")
        print(f"  期待値: {'一貫性あり' if test['expected'] else '重複/矛盾'}")
        print(f"  結果: {'一貫性あり' if is_consistent else '重複/矛盾'}")
        print(f"  理由: {reason}")

if __name__ == "__main__":
    test_duplication_detection()
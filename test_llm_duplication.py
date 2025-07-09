#!/usr/bin/env python3
"""
LLM重複検証のテスト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
import pytz
from src.utils.validators.llm_duplication_validator import LLMDuplicationValidator
from src.data.weather_data import WeatherForecast

async def test_llm_duplication():
    """LLM重複検証のテスト"""
    
    # API キーの確認
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY環境変数が設定されていません")
        return
    
    validator = LLMDuplicationValidator(api_key)
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
            "weather": "夏バテに注意",
            "advice": "夏バテ対策を",
            "expected": False,  # 重複として検出されるべき
            "description": "夏バテの繰り返し"
        },
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
            "weather": "快適な天気",
            "advice": "じめじめして不快",
            "expected": False,  # 矛盾として検出されるべき
            "description": "快適性の矛盾"
        },
        {
            "weather": "雲が広がる",
            "advice": "紫外線対策をしっかりと",
            "expected": True,  # 補完的でOK
            "description": "補完的な関係"
        },
        {
            "weather": "暑さ厳しく",
            "advice": "こまめな水分補給を",
            "expected": True,  # 補完的でOK
            "description": "暑さと水分補給"
        }
    ]
    
    print("LLM重複検証テスト")
    print("=" * 60)
    
    for test in test_cases:
        try:
            is_valid, reason = await validator.validate_comment_pair_with_llm(
                test["weather"],
                test["advice"],
                weather_data
            )
            
            passed = is_valid == test["expected"]
            status = "✅ PASS" if passed else "❌ FAIL"
            
            print(f"\n{status} {test['description']}")
            print(f"  天気: {test['weather']}")
            print(f"  アドバイス: {test['advice']}")
            print(f"  期待値: {'有効' if test['expected'] else '重複/矛盾'}")
            print(f"  結果: {'有効' if is_valid else '重複/矛盾'}")
            print(f"  理由: {reason}")
            
        except Exception as e:
            print(f"\n❌ ERROR {test['description']}")
            print(f"  エラー: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_duplication())
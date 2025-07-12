"""花粉バリデータの包括的なテスト"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from src.utils.validators.pollen_validator import PollenValidator
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.past_comment import PastComment, CommentType


class TestPollenValidator:
    """PollenValidatorのテストクラス"""
    
    @pytest.fixture
    def validator(self):
        """テスト用のバリデータインスタンス"""
        return PollenValidator()
    
    @pytest.fixture
    def pollen_comment(self):
        """花粉を含むテスト用コメント"""
        return PastComment(
            comment_text="花粉が多く飛散しています。マスクで花粉対策を",
            location="東京",
            weather_condition="晴れ",
            temperature=20.0,
            comment_type=CommentType.WEATHER_COMMENT,
            usage_count=5,
            datetime=datetime.now()
        )
    
    def create_weather(self, month, day, condition=WeatherCondition.CLEAR, 
                      precipitation=0.0, description="晴れ"):
        """テスト用の天気データを作成"""
        return WeatherForecast(
            location="東京",
            datetime=datetime(2024, month, day),
            temperature=20.0,
            weather_code=condition.value,
            weather_condition=condition,
            weather_description=description,
            precipitation=precipitation,
            humidity=60,
            wind_speed=3.0,
            wind_direction="南",
            wind_direction_degrees=180,
            raw_data={}
        )
    
    # 境界値テスト
    def test_boundary_february_end(self, validator, pollen_comment):
        """2月末（花粉シーズン開始）の境界値テスト"""
        # 2月28日 - 花粉OK
        weather = self.create_weather(2, 28)
        is_valid, _ = validator.validate(pollen_comment, weather)
        assert is_valid
    
    def test_boundary_march_start(self, validator, pollen_comment):
        """3月初め（花粉シーズン中）のテスト"""
        # 3月1日 - 花粉OK
        weather = self.create_weather(3, 1)
        is_valid, _ = validator.validate(pollen_comment, weather)
        assert is_valid
    
    def test_boundary_may_end(self, validator, pollen_comment):
        """5月末（花粉シーズン終了）の境界値テスト"""
        # 5月31日 - 花粉OK
        weather = self.create_weather(5, 31)
        is_valid, _ = validator.validate(pollen_comment, weather)
        assert is_valid
    
    def test_boundary_june_start(self, validator, pollen_comment):
        """6月初め（花粉シーズン外）の境界値テスト"""
        # 6月1日 - 花粉NG
        weather = self.create_weather(6, 1)
        is_valid, reason = validator.validate(pollen_comment, weather)
        assert not is_valid
        assert "6月は花粉飛散期間外" in reason
    
    # 複数の花粉表現パターンのテスト
    @pytest.mark.parametrize("comment_text,expected", [
        ("スギ花粉が大量に飛散", False),  # 7月
        ("ヒノキ花粉にご注意", False),
        ("花粉症の方はマスクを", False),
        ("くしゃみが止まらない花粉の季節", False),
        ("目のかゆみ、鼻水にお悩みの方へ", False),
        ("花粉予報は非常に多い", False),
        ("花粉量が多めです", False),
        ("今日は快晴です", True),  # 花粉を含まない
    ])
    def test_various_pollen_patterns_july(self, validator, comment_text, expected):
        """7月の様々な花粉表現パターンのテスト"""
        comment = PastComment(
            comment_text=comment_text,
            location="東京",
            weather_condition="晴れ",
            temperature=25.0,
            comment_type=CommentType.WEATHER_COMMENT,
            usage_count=5,
            datetime=datetime.now()
        )
        weather = self.create_weather(7, 15)
        is_valid, _ = validator.validate(comment, weather)
        assert is_valid == expected
    
    # エッジケース - 降水量
    @pytest.mark.parametrize("precipitation,expected", [
        (0.0, True),    # 降水なし - 花粉OK（3月）
        (0.1, False),   # わずかな降水 - 花粉NG
        (0.4, False),   # 少量の降水 - 花粉NG
        (0.5, False),   # 降水あり - 花粉NG
        (1.0, False),   # 明確な降水 - 花粉NG
        (10.0, False),  # 大雨 - 花粉NG
    ])
    def test_precipitation_edge_cases(self, validator, pollen_comment, precipitation, expected):
        """降水量のエッジケーステスト（3月）"""
        weather = self.create_weather(3, 15, precipitation=precipitation)
        is_valid, _ = validator.validate(pollen_comment, weather)
        assert is_valid == expected
    
    # 天気説明による判定
    @pytest.mark.parametrize("description,expected", [
        ("晴れ", True),
        ("快晴", True),
        ("曇り", True),
        ("小雨", False),
        ("雨", False),
        ("大雨", False),
        ("にわか雨", False),
        ("rain", False),
        ("light rain", False),
    ])
    def test_weather_description_patterns(self, validator, pollen_comment, description, expected):
        """天気説明による花粉判定テスト（3月）"""
        condition = WeatherCondition.RAIN if "雨" in description or "rain" in description else WeatherCondition.CLEAR
        weather = self.create_weather(3, 15, condition=condition, description=description)
        is_valid, _ = validator.validate(pollen_comment, weather)
        assert is_valid == expected
    
    # 月ごとの包括的テスト
    @pytest.mark.parametrize("month,expected", [
        (1, False),   # 1月 - NG
        (2, True),    # 2月 - OK
        (3, True),    # 3月 - OK
        (4, True),    # 4月 - OK
        (5, True),    # 5月 - OK
        (6, False),   # 6月 - NG
        (7, False),   # 7月 - NG
        (8, False),   # 8月 - NG
        (9, False),   # 9月 - NG
        (10, False),  # 10月 - NG
        (11, False),  # 11月 - NG
        (12, False),  # 12月 - NG
    ])
    def test_all_months(self, validator, pollen_comment, month, expected):
        """全月の花粉コメント妥当性テスト"""
        weather = self.create_weather(month, 15)
        is_valid, _ = validator.validate(pollen_comment, weather)
        assert is_valid == expected
    
    # is_inappropriate_pollen_comment メソッドのテスト
    def test_inappropriate_check_method(self, validator):
        """is_inappropriate_pollen_comment メソッドの直接テスト"""
        weather = self.create_weather(7, 15)
        
        # 花粉を含む - 7月は不適切
        assert validator.is_inappropriate_pollen_comment(
            "花粉が飛散中", weather, datetime(2024, 7, 15)
        )
        
        # 花粉を含まない - 常に適切
        assert not validator.is_inappropriate_pollen_comment(
            "今日は晴天", weather, datetime(2024, 7, 15)
        )
        
        # 花粉を含む - 3月は適切
        assert not validator.is_inappropriate_pollen_comment(
            "花粉が飛散中", weather, datetime(2024, 3, 15)
        )
        
        # 雨天時は不適切
        rain_weather = self.create_weather(3, 15, WeatherCondition.RAIN, 5.0, "雨")
        assert validator.is_inappropriate_pollen_comment(
            "花粉が飛散中", rain_weather, datetime(2024, 3, 15)
        )
"""花粉バリデータの包括的なテスト"""

import pytest
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
    
    def test_boundary_june_start(self, validator, pollen_comment):
        """6月初め（花粉シーズン外）の境界値テスト"""
        # 6月1日 - 花粉NG
        weather = self.create_weather(6, 1)
        is_valid, reason = validator.validate(pollen_comment, weather)
        assert not is_valid
        assert "6月は花粉飛散期間外" in reason
    
    # エッジケース - 降水量
    @pytest.mark.parametrize("precipitation,expected", [
        (0.0, True),    # 降水なし - 花粉OK（3月）
        (0.1, False),   # わずかな降水 - 花粉NG
        (0.4, False),   # 少量の降水 - 花粉NG
    ])
    def test_precipitation_edge_cases(self, validator, pollen_comment, precipitation, expected):
        """降水量のエッジケーステスト（3月）"""
        weather = self.create_weather(3, 15, precipitation=precipitation)
        is_valid, _ = validator.validate(pollen_comment, weather)
        assert is_valid == expected
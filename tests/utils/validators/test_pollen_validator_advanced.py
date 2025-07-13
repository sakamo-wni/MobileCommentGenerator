"""花粉バリデータの高度な機能テスト"""

import pytest
from datetime import datetime
from src.utils.validators.pollen_validator import PollenValidator
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.past_comment import PastComment, CommentType


class TestPollenValidatorAdvanced:
    """花粉バリデータの高度な機能のテスト"""
    
    @pytest.fixture
    def validator(self):
        return PollenValidator()
    
    def create_weather(self, month=3, day=15, location="東京", 
                      wind_speed=5.0, humidity=60, precipitation=0.0,
                      description="晴れ"):
        """テスト用天気データ作成"""
        return WeatherForecast(
            location=location,
            datetime=datetime(2024, month, day),
            temperature=20.0,
            weather_code="clear",
            weather_condition=WeatherCondition.CLEAR,
            weather_description=description,
            precipitation=precipitation,
            humidity=humidity,
            wind_speed=wind_speed,
            wind_direction="南",
            wind_direction_degrees=180,
            raw_data={}
        )
    
    def create_comment(self, text, location="東京"):
        """テスト用コメント作成"""
        return PastComment(
            comment_text=text,
            location=location,
            weather_condition="晴れ",
            temperature=20.0,
            comment_type=CommentType.WEATHER_COMMENT,
            usage_count=5,
            datetime=datetime.now()
        )
    
    # 風速・湿度による飛散条件テスト
    def test_high_humidity_blocks_pollen(self, validator):
        """高湿度（80%以上）で花粉が飛散しない"""
        weather = self.create_weather(humidity=85)
        comment = self.create_comment("花粉が多く飛散しています")
        
        is_valid, reason = validator.validate(comment, weather)
        assert not is_valid
        assert "高湿度" in reason
        assert "85%" in reason
    
    def test_strong_wind_blocks_pollen(self, validator):
        """強風（15m/s以上）で花粉が飛び去る"""
        weather = self.create_weather(wind_speed=16.0)
        comment = self.create_comment("花粉症の方は注意")
        
        is_valid, reason = validator.validate(comment, weather)
        assert not is_valid
        assert "強風" in reason
        assert "16.0m/s" in reason
    
    def test_optimal_wind_allows_pollen(self, validator):
        """適度な風速（2-10m/s）では花粉OK"""
        weather = self.create_weather(wind_speed=5.0)
        comment = self.create_comment("スギ花粉が飛散中")
        
        is_valid, _ = validator.validate(comment, weather)
        assert is_valid
    
    # 地域別花粉シーズンテスト
    def test_hokkaido_pollen_season(self, validator):
        """北海道のシラカバ花粉シーズン（4-6月）"""
        # 5月は花粉OK
        weather = self.create_weather(month=5, location="北海道札幌市")
        comment = self.create_comment("シラカバ花粉に注意", "北海道札幌市")
        is_valid, _ = validator.validate(comment, weather)
        assert is_valid
        
        # 7月は花粉NG
        weather = self.create_weather(month=7, location="北海道札幌市")
        is_valid, reason = validator.validate(comment, weather)
        assert not is_valid
        assert "北海道" in reason
        assert "7月は花粉飛散期間外" in reason
    
    def test_kyushu_early_pollen_season(self, validator):
        """九州の早い花粉シーズン（1-4月）"""
        # 1月から花粉OK
        weather = self.create_weather(month=1, location="福岡県福岡市")
        comment = self.create_comment("スギ花粉が飛び始めました", "福岡県福岡市")
        is_valid, _ = validator.validate(comment, weather)
        assert is_valid
        
        # 5月は花粉NG
        weather = self.create_weather(month=5, location="福岡県福岡市")
        is_valid, reason = validator.validate(comment, weather)
        assert not is_valid
    
    def test_okinawa_no_pollen(self, validator):
        """沖縄では花粉がほとんど飛散しない"""
        weather = self.create_weather(month=3, location="沖縄県那覇市")
        comment = self.create_comment("花粉症対策が必要", "沖縄県那覇市")
        
        is_valid, reason = validator.validate(comment, weather)
        assert not is_valid
        assert "沖縄" in reason
        assert "ほとんど飛散しない" in reason
    
    # 複合条件テスト
    def test_rain_overrides_season(self, validator):
        """雨天時は季節に関係なく花粉NG"""
        weather = self.create_weather(
            month=3,  # 花粉シーズン中
            precipitation=5.0,
            description="雨"
        )
        comment = self.create_comment("花粉が飛散中")
        
        is_valid, reason = validator.validate(comment, weather)
        assert not is_valid
        assert "雨天時" in reason
    
    def test_multiple_conditions_fail(self, validator):
        """複数の条件が同時に失敗する場合"""
        # 高湿度かつ強風
        weather = self.create_weather(
            humidity=85,
            wind_speed=20.0
        )
        comment = self.create_comment("花粉に注意")
        
        is_valid, reason = validator.validate(comment, weather)
        assert not is_valid
        # 最初にチェックされた条件が理由として返される
        assert "高湿度" in reason or "強風" in reason
    
    # 統計情報テスト（モック不使用の簡易版）
    def test_validation_stats_tracking(self, validator):
        """統計情報が正しく追跡される"""
        initial_total = validator._validation_stats["total_checks"]
        initial_detected = validator._validation_stats["pollen_detected"]
        
        # 花粉を含むコメントをチェック
        weather = self.create_weather()
        comment = self.create_comment("花粉が飛散中")
        validator.validate(comment, weather)
        
        assert validator._validation_stats["total_checks"] == initial_total + 1
        assert validator._validation_stats["pollen_detected"] == initial_detected + 1
        
        # 花粉を含まないコメントをチェック
        comment_no_pollen = self.create_comment("今日は晴天です")
        validator.validate(comment_no_pollen, weather)
        
        assert validator._validation_stats["total_checks"] == initial_total + 2
        assert validator._validation_stats["pollen_detected"] == initial_detected + 1
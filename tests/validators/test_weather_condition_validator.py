"""天気条件バリデーターのユニットテスト"""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.utils.validators.weather_specific.weather_condition_validator import WeatherConditionValidator
from src.data.weather_data import WeatherForecast


class TestWeatherConditionValidator:
    """WeatherConditionValidatorのテストクラス"""
    
    def test_init_with_default_config(self):
        """デフォルト設定での初期化テスト"""
        validator = WeatherConditionValidator()
        assert validator.weather_forbidden_words is not None
        assert "rain" in validator.weather_forbidden_words
        assert "sunny" in validator.weather_forbidden_words
        assert "cloudy" in validator.weather_forbidden_words
        assert "heavy_rain" in validator.weather_forbidden_words
    
    def test_init_with_custom_config(self):
        """カスタム設定ファイルでの初期化テスト"""
        # 一時的な設定ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "rain": {
                    "weather_comment": ["テスト晴れ"],
                    "advice": ["テスト日焼け止め"]
                }
            }
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            validator = WeatherConditionValidator(config_path)
            assert "テスト晴れ" in validator.weather_forbidden_words["rain"]["weather_comment"]
            assert "テスト日焼け止め" in validator.weather_forbidden_words["rain"]["advice"]
        finally:
            Path(config_path).unlink()
    
    def test_check_weather_conditions_sunny(self):
        """晴天時の検証テスト"""
        validator = WeatherConditionValidator()
        
        # 晴天時に雨関連の表現は不適切
        is_valid, reason = validator.check_weather_conditions(
            "今日は雨が降りそうです", "weather_comment", "晴れ"
        )
        assert not is_valid
        assert "晴天時に「雨」は不適切" in reason
        
        # 晴天時に晴れの表現は適切
        is_valid, reason = validator.check_weather_conditions(
            "青空が広がっています", "weather_comment", "晴れ"
        )
        assert is_valid
    
    def test_check_weather_conditions_rainy(self):
        """雨天時の検証テスト"""
        validator = WeatherConditionValidator()
        
        # 雨天時に晴れ関連の表現は不適切
        is_valid, reason = validator.check_weather_conditions(
            "青空が美しいです", "weather_comment", "雨"
        )
        assert not is_valid
        assert "雨天時に「青空」は不適切" in reason
        
        # 雨天時に傘の表現は適切
        is_valid, reason = validator.check_weather_conditions(
            "傘をお忘れなく", "advice", "雨"
        )
        assert is_valid
    
    def test_check_weather_conditions_heavy_rain(self):
        """大雨時の検証テスト"""
        validator = WeatherConditionValidator()
        
        # 大雨時により多くの表現が不適切
        is_valid, reason = validator.check_weather_conditions(
            "にわか雨かもしれません", "weather_comment", "豪雨"
        )
        assert not is_valid
        assert "大雨時に「にわか雨」は不適切" in reason
    
    def test_check_weather_conditions_cloudy(self):
        """曇天時の検証テスト"""
        validator = WeatherConditionValidator()
        
        # 曇天時に強い日差しの表現は不適切
        is_valid, reason = validator.check_weather_conditions(
            "強い日差しに注意", "weather_comment", "曇り"
        )
        assert not is_valid
        assert "曇天時に「強い日差し」は不適切" in reason
    
    def test_check_rainy_weather_contradictions(self):
        """雨天時の矛盾チェックテスト"""
        validator = WeatherConditionValidator()
        
        # 雨天時に洗濯物を外に干すのは矛盾
        is_valid, reason = validator.check_rainy_weather_contradictions(
            "洗濯物を外に干しましょう", "雨"
        )
        assert not is_valid
        assert "雨天時に「洗濯物を外に」は矛盾" in reason
        
        # 晴天時はチェック対象外
        is_valid, reason = validator.check_rainy_weather_contradictions(
            "洗濯物を外に干しましょう", "晴れ"
        )
        assert is_valid
        assert "雨天チェック対象外" in reason
    
    def test_is_stable_cloudy_weather(self):
        """安定した曇り天気の判定テスト"""
        validator = WeatherConditionValidator()
        
        # 安定した曇り
        weather_data = WeatherForecast(
            location="東京",
            weather_description="曇り",
            temperature=20.0,
            rain_probability=10
        )
        assert validator.is_stable_cloudy_weather(weather_data)
        
        # 不安定な曇り（にわか雨）
        weather_data = WeatherForecast(
            location="東京",
            weather_description="曇り時々にわか雨",
            temperature=20.0,
            rain_probability=40
        )
        assert not validator.is_stable_cloudy_weather(weather_data)
        
        # 晴れ（曇りではない）
        weather_data = WeatherForecast(
            location="東京",
            weather_description="晴れ",
            temperature=20.0,
            rain_probability=0
        )
        assert not validator.is_stable_cloudy_weather(weather_data)
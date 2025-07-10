"""コメント関連設定モジュールのテスト"""

import os
import pytest
from unittest.mock import patch

from src.config.settings.comment_settings import CommentConfig, SevereWeatherConfig
from src.data.weather_data import WeatherCondition


class TestCommentConfig:
    """CommentConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        with patch.dict(os.environ, {}, clear=True):
            config = CommentConfig()
            
            # 温度閾値
            assert config.heat_warning_threshold == 30.0
            assert config.cold_warning_threshold == 15.0
            
            # トレンド分析期間
            assert config.trend_hours_ahead == 12
            
            # 天気スコアが設定されているかテスト
            assert isinstance(config.weather_scores, dict)
            assert config.weather_scores[WeatherCondition.CLEAR] == 5
            assert config.weather_scores[WeatherCondition.RAIN] == 2
            assert config.weather_scores[WeatherCondition.HEAVY_RAIN] == 0
    
    def test_env_override(self):
        """環境変数による設定オーバーライドテスト"""
        env_vars = {
            "COMMENT_HEAT_WARNING_THRESHOLD": "35.0",
            "COMMENT_COLD_WARNING_THRESHOLD": "10.0",
            "COMMENT_TREND_HOURS_AHEAD": "24"
        }
        
        with patch.dict(os.environ, env_vars):
            config = CommentConfig()
            
            assert config.heat_warning_threshold == 35.0
            assert config.cold_warning_threshold == 10.0
            assert config.trend_hours_ahead == 24
    
    def test_weather_scores_completeness(self):
        """すべての天気条件にスコアが設定されているかテスト"""
        config = CommentConfig()
        
        # 主要な天気条件がスコアを持っているか確認
        important_conditions = [
            WeatherCondition.CLEAR,
            WeatherCondition.CLOUDY,
            WeatherCondition.RAIN,
            WeatherCondition.SNOW,
            WeatherCondition.FOG
        ]
        
        for condition in important_conditions:
            assert condition in config.weather_scores
            assert isinstance(config.weather_scores[condition], int)
            assert 0 <= config.weather_scores[condition] <= 5


class TestSevereWeatherConfig:
    """SevereWeatherConfigクラスのテスト"""
    
    def test_default_initialization(self):
        """デフォルト値での初期化テスト"""
        config = SevereWeatherConfig()
        
        # 悪天候条件が設定されているか
        assert isinstance(config.severe_weather_conditions, list)
        assert WeatherCondition.HEAVY_RAIN in config.severe_weather_conditions
        assert WeatherCondition.STORM in config.severe_weather_conditions
        assert WeatherCondition.FOG in config.severe_weather_conditions
        
        # 悪天候コメントが設定されているか
        assert isinstance(config.severe_weather_comments, dict)
        assert "大雨・嵐" in config.severe_weather_comments
        assert "雨" in config.severe_weather_comments
        assert "霧" in config.severe_weather_comments
        
        # 悪天候アドバイスが設定されているか
        assert isinstance(config.severe_weather_advice, dict)
        assert "大雨・嵐" in config.severe_weather_advice
        assert "雨" in config.severe_weather_advice
        assert "霧" in config.severe_weather_advice
    
    def test_is_severe_weather(self):
        """悪天候判定メソッドのテスト"""
        config = SevereWeatherConfig()
        
        # 悪天候として定義されている条件
        assert config.is_severe_weather(WeatherCondition.HEAVY_RAIN) is True
        assert config.is_severe_weather(WeatherCondition.STORM) is True
        assert config.is_severe_weather(WeatherCondition.FOG) is True
        
        # 悪天候として定義されていない条件
        assert config.is_severe_weather(WeatherCondition.CLEAR) is False
        assert config.is_severe_weather(WeatherCondition.PARTLY_CLOUDY) is False
    
    def test_get_recommended_comments(self):
        """推奨コメント取得メソッドのテスト"""
        config = SevereWeatherConfig()
        
        # 雨の場合の推奨コメント
        rain_comments = config.get_recommended_comments(WeatherCondition.RAIN)
        assert "weather" in rain_comments
        assert "advice" in rain_comments
        assert isinstance(rain_comments["weather"], list)
        assert isinstance(rain_comments["advice"], list)
        assert len(rain_comments["weather"]) > 0
        assert len(rain_comments["advice"]) > 0
        
        # 霧の場合の推奨コメント
        fog_comments = config.get_recommended_comments(WeatherCondition.FOG)
        assert "weather" in fog_comments
        assert "advice" in fog_comments
        assert len(fog_comments["weather"]) > 0
        assert len(fog_comments["advice"]) > 0
    
    def test_exclude_keywords(self):
        """除外キーワードのテスト"""
        config = SevereWeatherConfig()
        
        assert isinstance(config.exclude_keywords_severe, list)
        assert "穏やか" in config.exclude_keywords_severe
        assert "快適" in config.exclude_keywords_severe
        assert "晴れ" in config.exclude_keywords_severe
        assert "洗濯日和" in config.exclude_keywords_severe
    
    def test_weather_condition_mapping(self):
        """天気条件の日本語マッピングテスト"""
        config = SevereWeatherConfig()
        
        assert config.weather_condition_japanese[WeatherCondition.HEAVY_RAIN] == "大雨"
        assert config.weather_condition_japanese[WeatherCondition.FOG] == "霧"
        assert config.weather_condition_japanese[WeatherCondition.STORM] == "嵐"
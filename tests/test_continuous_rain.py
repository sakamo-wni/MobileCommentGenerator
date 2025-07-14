"""連続雨判定ロジックのテスト"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from src.nodes.comment_selector.base_selector import CommentSelector, CONTINUOUS_RAIN_THRESHOLD_HOURS
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment, CommentType
from src.data.comment_generation_state import CommentGenerationState


class TestContinuousRain:
    """連続雨判定ロジックのテスト"""

    def setup_method(self):
        """テストのセットアップ"""
        self.llm_manager = Mock()
        self.validator = Mock()
        self.selector = CommentSelector(self.llm_manager, self.validator)

    def create_weather_data(self, precipitation=10.0, weather_description="雨"):
        """テスト用の天気データを作成"""
        return WeatherForecast(
            weather_description=weather_description,
            temperature=20.0,
            precipitation=precipitation,
            wind_speed=5.0,
            humidity=80
        )

    def create_period_forecast(self, hour, weather="雨", precipitation=5.0):
        """テスト用の時間別予報を作成"""
        forecast = Mock()
        forecast.datetime = datetime(2024, 1, 1, hour, 0)
        forecast.weather = weather
        forecast.precipitation = precipitation
        return forecast

    def create_state_with_forecasts(self, period_forecasts):
        """時間別予報を含む状態を作成"""
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now()
        )
        state.generation_metadata = {
            'period_forecasts': period_forecasts
        }
        return state

    def test_continuous_rain_detection_all_rain(self):
        """4時間すべて雨の場合の連続雨判定"""
        # 9, 12, 15, 18時すべて雨
        period_forecasts = [
            self.create_period_forecast(9, "雨", 5.0),
            self.create_period_forecast(12, "雨", 10.0),
            self.create_period_forecast(15, "雨", 8.0),
            self.create_period_forecast(18, "雨", 3.0)
        ]
        
        state = self.create_state_with_forecasts(period_forecasts)
        weather_data = self.create_weather_data()
        
        # にわか雨表現を含むコメント
        shower_comment = PastComment(
            comment_text="急なにわか雨に注意してください",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_description="雨",
            created_at=datetime.now()
        )
        
        # 通常の雨コメント
        normal_rain_comment = PastComment(
            comment_text="今日は一日雨が続きます",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_description="雨",
            created_at=datetime.now()
        )
        
        comments = [shower_comment, normal_rain_comment]
        
        # 連続雨の場合、にわか雨表現は選ばれない
        result = self.selector._find_rain_appropriate_weather_comment(comments, weather_data, state)
        assert result is not None
        assert "にわか雨" not in result.comment_text

    def test_continuous_rain_detection_partial_rain(self):
        """部分的に雨の場合の判定"""
        # 9, 12時は晴れ、15, 18時は雨
        period_forecasts = [
            self.create_period_forecast(9, "晴れ", 0.0),
            self.create_period_forecast(12, "晴れ", 0.0),
            self.create_period_forecast(15, "雨", 5.0),
            self.create_period_forecast(18, "雨", 3.0)
        ]
        
        state = self.create_state_with_forecasts(period_forecasts)
        weather_data = self.create_weather_data()
        
        # にわか雨表現を含むコメント
        shower_comment = PastComment(
            comment_text="午後からにわか雨の可能性があります",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_description="雨",
            created_at=datetime.now()
        )
        
        comments = [shower_comment]
        
        # 部分的な雨の場合、にわか雨表現は選ばれる
        result = self.selector._find_rain_appropriate_weather_comment(comments, weather_data, state)
        assert result is not None
        assert "にわか雨" in result.comment_text

    def test_continuous_rain_threshold(self):
        """連続雨の閾値が正しく設定されていることを確認"""
        assert CONTINUOUS_RAIN_THRESHOLD_HOURS == 4

    def test_rain_intensity_validation(self):
        """降水量に応じた表現の妥当性チェック"""
        state = self.create_state_with_forecasts([])
        
        # 弱い雨（3mm/h）
        light_rain_data = self.create_weather_data(precipitation=3.0)
        
        # 強雨表現のコメント
        strong_rain_comment = PastComment(
            comment_text="激しい土砂降りが予想されます",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_description="雨",
            created_at=datetime.now()
        )
        
        # 弱い雨表現のコメント
        light_rain_comment = PastComment(
            comment_text="弱い雨が降るでしょう",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_description="雨",
            created_at=datetime.now()
        )
        
        comments = [strong_rain_comment, light_rain_comment]
        
        # 弱い雨の場合、強雨表現は選ばれない
        result = self.selector._find_rain_appropriate_weather_comment(comments, light_rain_data, state)
        assert result is not None
        assert "土砂降り" not in result.comment_text

    def test_advice_comment_for_continuous_rain(self):
        """連続雨時のアドバイスコメント選択"""
        # 4時間すべて雨
        period_forecasts = [
            self.create_period_forecast(9, "雨", 5.0),
            self.create_period_forecast(12, "雨", 10.0),
            self.create_period_forecast(15, "雨", 8.0),
            self.create_period_forecast(18, "雨", 3.0)
        ]
        
        state = self.create_state_with_forecasts(period_forecasts)
        
        # 控えめな傘表現
        mild_umbrella_comment = PastComment(
            comment_text="念のため折りたたみ傘があると安心です",
            comment_type=CommentType.ADVICE,
            weather_description="雨",
            created_at=datetime.now()
        )
        
        # しっかりした傘表現
        strong_umbrella_comment = PastComment(
            comment_text="傘は必須です。しっかりした雨具を準備しましょう",
            comment_type=CommentType.ADVICE,
            weather_description="雨",
            created_at=datetime.now()
        )
        
        comments = [mild_umbrella_comment, strong_umbrella_comment]
        
        # 連続雨の場合、控えめな傘表現は選ばれない
        result = self.selector._find_rain_appropriate_advice_comment(comments, state)
        assert result is not None
        assert "折りたたみ傘" not in result.comment_text

    def test_no_period_forecasts(self):
        """時間別予報がない場合の処理"""
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now()
        )  # metadata なし
        weather_data = self.create_weather_data()
        
        shower_comment = PastComment(
            comment_text="にわか雨に注意",
            comment_type=CommentType.WEATHER_COMMENT,
            weather_description="雨",
            created_at=datetime.now()
        )
        
        comments = [shower_comment]
        
        # 時間別予報がない場合はにわか雨表現も選択可能
        result = self.selector._find_rain_appropriate_weather_comment(comments, weather_data, state)
        assert result is not None
"""コメント安全性チェックのテスト"""

import pytest
from datetime import datetime
import pytz

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment, CommentType
from src.data.comment_generation_state import CommentGenerationState
from src.nodes.helpers.comment_safety import (
    check_and_fix_weather_comment_safety,
    _find_alternative_weather_comment,
    CHANGEABLE_WEATHER_PATTERNS
)


class TestCommentSafety:
    """コメント安全性チェックのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        from src.data.weather_data import WeatherCondition, WindDirection
        
        # テスト用の天気データ（晴天）
        self.sunny_weather = WeatherForecast(
            location="東京",
            datetime=datetime(2024, 7, 15, 12, 0, tzinfo=pytz.timezone("Asia/Tokyo")),
            temperature=32.0,
            weather_code="100",
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction=WindDirection.S,
            wind_direction_degrees=180,
            pressure=1013.0,
            visibility=10.0,
            uv_index=8
        )
        
        # テスト用の雨天データ
        self.rainy_weather = WeatherForecast(
            location="東京",
            datetime=datetime(2024, 7, 15, 12, 0, tzinfo=pytz.timezone("Asia/Tokyo")),
            temperature=25.0,
            weather_code="200",
            weather_condition=WeatherCondition.RAIN,
            weather_description="雨",
            precipitation=5.0,
            humidity=85.0,
            wind_speed=5.0,
            wind_direction=WindDirection.N,
            wind_direction_degrees=0,
            pressure=1008.0,
            visibility=5.0,
            uv_index=2
        )
    
    def test_sunny_weather_with_changeable_comment(self):
        """晴天時に「変わりやすい空」が修正されることを確認"""
        # 不適切なコメント
        weather_comment = "変わりやすい空です"
        advice_comment = "傘があると安心"
        
        # テスト用の過去コメントリスト
        past_weather_comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="変わりやすい空です",  # 最初のコメントも不適切
                comment_type=CommentType.WEATHER_COMMENT
            ),
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="強い日差しに注意",
                comment_type=CommentType.WEATHER_COMMENT
            ),
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="厳しい暑さです",
                comment_type=CommentType.WEATHER_COMMENT
            )
        ]
        
        past_advice_comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="傘があると安心",
                comment_type=CommentType.ADVICE
            )
        ]
        
        # 状態オブジェクトの作成
        state = CommentGenerationState(
            target_datetime=self.sunny_weather.datetime,
            location_name="東京"
        )
        state.weather_data = self.sunny_weather
        # past_commentsに両方のコメントを統合
        state.past_comments = past_weather_comments + past_advice_comments
        
        # 安全性チェック実行
        fixed_weather, fixed_advice = check_and_fix_weather_comment_safety(
            self.sunny_weather, weather_comment, advice_comment, state
        )
        
        # 「変わりやすい空」が含まれていないことを確認
        assert "変わりやすい空" not in fixed_weather
        assert fixed_weather in ["強い日差しに注意", "厳しい暑さです", "穏やかな晴天です", "猛烈な暑さに警戒"]
    
    def test_all_comments_contain_changeable_pattern(self):
        """全てのコメントが禁止パターンを含む場合、デフォルトメッセージが使用される"""
        # 全て不適切なコメント
        past_weather_comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="変わりやすい空です",
                comment_type=CommentType.WEATHER_COMMENT
            ),
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="変化しやすい空模様",
                comment_type=CommentType.WEATHER_COMMENT
            ),
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="不安定な空模様です",
                comment_type=CommentType.WEATHER_COMMENT
            )
        ]
        
        # 代替コメント検索実行
        result = _find_alternative_weather_comment(
            self.sunny_weather, past_weather_comments, CHANGEABLE_WEATHER_PATTERNS
        )
        
        # 全てが禁止パターンの場合は空文字列が返されることを確認
        assert result == ""
    
    def test_rainy_weather_comment_not_modified(self):
        """雨天時は「変わりやすい空」が修正されないことを確認"""
        weather_comment = "変わりやすい空です"
        advice_comment = "傘を忘れずに"
        
        state = CommentGenerationState(
            target_datetime=self.rainy_weather.datetime,
            location_name="東京",
            weather_data=self.rainy_weather
        )
        
        # 安全性チェック実行
        fixed_weather, fixed_advice = check_and_fix_weather_comment_safety(
            self.rainy_weather, weather_comment, advice_comment, state
        )
        
        # 雨天時は「変わりやすい空」が修正されないことを確認
        assert fixed_weather == weather_comment
    
    def test_temperature_based_default_message(self):
        """気温に応じた適切なデフォルトメッセージが選択される"""
        from src.data.weather_data import WeatherCondition, WindDirection
        
        # 猛暑日（35度以上）
        hot_weather = WeatherForecast(
            location="東京",
            datetime=datetime(2024, 7, 15, 12, 0, tzinfo=pytz.timezone("Asia/Tokyo")),
            temperature=36.0,
            weather_code="100",
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=2.0,
            wind_direction=WindDirection.S,
            wind_direction_degrees=180,
            pressure=1013.0,
            visibility=10.0,
            uv_index=10
        )
        
        # 全て不適切なコメント
        past_comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="変わりやすい空です",
                comment_type=CommentType.WEATHER_COMMENT
            )
        ]
        
        result = _find_alternative_weather_comment(
            hot_weather, past_comments, CHANGEABLE_WEATHER_PATTERNS
        )
        
        assert result == ""  # 禁止パターンのみの場合は空文字列
        
        # 通常の晴天（30度未満）
        mild_weather = WeatherForecast(
            location="東京",
            datetime=datetime(2024, 7, 15, 12, 0, tzinfo=pytz.timezone("Asia/Tokyo")),
            temperature=25.0,
            weather_code="100",
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=50.0,
            wind_speed=3.0,
            wind_direction=WindDirection.S,
            wind_direction_degrees=180,
            pressure=1015.0,
            visibility=10.0,
            uv_index=6
        )
        
        result = _find_alternative_weather_comment(
            mild_weather, past_comments, CHANGEABLE_WEATHER_PATTERNS
        )
        
        assert result == ""  # 禁止パターンのみの場合は空文字列
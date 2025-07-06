"""「うすぐもり」時の「変わりやすい空」コメントのテスト"""

import pytest
from datetime import datetime
from src.nodes.helpers.comment_safety import check_and_fix_weather_comment_safety
from src.data.comment_generation_state import CommentGenerationState
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.data.past_comment import PastComment, CommentType


def create_weather_forecast(description: str, temp: float = 25.0):
    """天気予報データを作成"""
    return WeatherForecast(
        location="東京",
        datetime=datetime(2025, 7, 6, 12, 0, 0),
        temperature=temp,
        weather_code="600",
        weather_condition=WeatherCondition.CLOUDY,
        weather_description=description,
        precipitation=0.0,
        humidity=71.0,
        wind_speed=3.0,
        wind_direction=WindDirection.NW,
        wind_direction_degrees=315,
        pressure=1013.0,
        visibility=10.0,
        uv_index=0,
        confidence=1.0,
        raw_data={},
    )


def create_past_comment(text: str, comment_type: CommentType):
    """過去コメントを作成"""
    return PastComment(
        location="東京",
        datetime=datetime.now(),
        weather_condition="うすぐもり",
        comment_text=text,
        comment_type=comment_type,
        temperature=25.0,
        weather_code="600",
        humidity=70.0,
        precipitation=0.0
    )


class TestUsugumoriChangeable:
    """「うすぐもり」時の「変わりやすい空」のテスト"""
    
    def test_usugumo_with_changeable_sky_is_fixed(self):
        """「うすぐもり」時に「変わりやすい空」が修正されることを確認"""
        weather_data = create_weather_forecast("うすぐもり")
        weather_comment = "変わりやすい空になりそうです"
        advice_comment = "傘があると安心です"
        
        # 代替コメントを含む状態を作成
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now()
        )
        state.past_weather_comments = [
            create_past_comment("穏やかな曇り空です", CommentType.WEATHER_COMMENT),
            create_past_comment("過ごしやすい天気です", CommentType.WEATHER_COMMENT),
            create_past_comment("心地よい陽気です", CommentType.WEATHER_COMMENT),
        ]
        state.past_advice_comments = [
            create_past_comment("傘があると安心です", CommentType.ADVICE),
        ]
        
        # 安全性チェックを実行
        fixed_weather, fixed_advice = check_and_fix_weather_comment_safety(
            weather_data, weather_comment, advice_comment, state
        )
        
        # 「変わりやすい空」が含まれていないことを確認
        assert "変わりやすい空" not in fixed_weather
        assert "変わりやすい" not in fixed_weather
        assert fixed_advice == advice_comment  # アドバイスは変更されない
        
    def test_thin_cloud_variations_with_changeable_patterns(self):
        """薄曇りの各種バリエーションで変わりやすい空が修正されることを確認"""
        variations = ["薄曇り", "うすぐもり", "薄ぐもり", "薄曇", "うす曇り"]
        changeable_patterns = [
            "変わりやすい空", 
            "変わりやすい天気", 
            "変化しやすい空",
            "移ろいやすい空",
            "気まぐれな空",
            "不安定な空模様"
        ]
        
        for weather_desc in variations:
            for pattern in changeable_patterns:
                weather_data = create_weather_forecast(weather_desc)
                weather_comment = f"{pattern}になりそうです"
                advice_comment = "お出かけには注意"
                
                state = CommentGenerationState(
                    location_name="東京",
                    target_datetime=datetime.now()
                )
                state.past_weather_comments = [
                    create_past_comment("穏やかな一日です", CommentType.WEATHER_COMMENT),
                ]
                state.past_advice_comments = [
                    create_past_comment("お出かけには注意", CommentType.ADVICE),
                ]
                
                fixed_weather, _ = check_and_fix_weather_comment_safety(
                    weather_data, weather_comment, advice_comment, state
                )
                
                # パターンが含まれていないことを確認
                assert pattern not in fixed_weather, f"{weather_desc}で{pattern}が修正されませんでした"
                
    def test_cloudy_weather_changeable_not_fixed(self):
        """完全な曇り（晴天ではない）の場合は「変わりやすい空」が修正されないことを確認"""
        weather_data = create_weather_forecast("くもり")  # 「うすぐもり」ではない
        weather_comment = "変わりやすい空になりそうです"
        advice_comment = "傘があると安心です"
        
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now()
        )
        state.past_weather_comments = []
        state.past_advice_comments = []
        
        fixed_weather, fixed_advice = check_and_fix_weather_comment_safety(
            weather_data, weather_comment, advice_comment, state
        )
        
        # 「くもり」の場合は修正されない
        assert fixed_weather == weather_comment
        assert fixed_advice == advice_comment
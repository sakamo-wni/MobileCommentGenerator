"""comment_filters.pyの単体テスト"""

import pytest
from unittest.mock import Mock
from datetime import datetime
from src.nodes.unified_comment_generation.comment_filters import (
    check_continuous_rain,
    filter_shower_comments,
    filter_mild_umbrella_comments,
    filter_forbidden_phrases,
    filter_seasonal_inappropriate_comments
)
from src.data.past_comment import PastComment, CommentType
from src.data.comment_generation_state import CommentGenerationState


class TestCheckContinuousRain:
    """check_continuous_rain関数のテスト"""
    
    def test_continuous_rain_detected(self):
        """連続雨が検出される場合"""
        state = CommentGenerationState()
        
        # 4時間以上の雨をシミュレート
        forecasts = []
        for i in range(5):
            forecast = Mock()
            forecast.weather = "雨"
            forecast.precipitation = 2.0
            forecast.datetime = datetime(2024, 1, 1, 9 + i * 3)
            forecasts.append(forecast)
        
        state.generation_metadata = {'period_forecasts': forecasts}
        
        assert check_continuous_rain(state) is True
    
    def test_not_continuous_rain(self):
        """連続雨でない場合"""
        state = CommentGenerationState()
        
        # 3時間の雨（閾値未満）
        forecasts = []
        for i in range(3):
            forecast = Mock()
            forecast.weather = "雨" if i < 2 else "晴れ"
            forecast.precipitation = 1.0 if i < 2 else 0.0
            forecast.datetime = datetime(2024, 1, 1, 9 + i * 3)
            forecasts.append(forecast)
        
        state.generation_metadata = {'period_forecasts': forecasts}
        
        assert check_continuous_rain(state) is False
    
    def test_no_metadata(self):
        """メタデータがない場合"""
        state = CommentGenerationState()
        state.generation_metadata = None
        
        assert check_continuous_rain(state) is False
    
    def test_precipitation_based_detection(self):
        """降水量ベースでの検出"""
        state = CommentGenerationState()
        
        forecasts = []
        for i in range(4):
            forecast = Mock()
            forecast.weather = "曇り"  # 天気は雨でない
            forecast.precipitation = 0.2  # 0.1mm以上の降水
            forecast.datetime = datetime(2024, 1, 1, 9 + i * 3)
            forecasts.append(forecast)
        
        state.generation_metadata = {'period_forecasts': forecasts}
        
        assert check_continuous_rain(state) is True


class TestFilterShowerComments:
    """filter_shower_comments関数のテスト"""
    
    def create_comment(self, text: str) -> PastComment:
        """テスト用コメントを作成"""
        return PastComment(
            id=1,
            comment_text=text,
            comment_type=CommentType.WEATHER_COMMENT,
            weather_condition="雨",
            created_at=datetime.now()
        )
    
    def test_filter_shower_keywords(self):
        """にわか雨関連のキーワードをフィルタリング"""
        comments = [
            self.create_comment("今日はにわか雨の可能性があります"),
            self.create_comment("一時的な雨に注意してください"),
            self.create_comment("雨が降り続きます"),
            self.create_comment("急な雨に備えましょう"),
            self.create_comment("本格的な雨になりそうです")
        ]
        
        filtered = filter_shower_comments(comments)
        
        assert len(filtered) == 2
        assert "雨が降り続きます" in [c.comment_text for c in filtered]
        assert "本格的な雨になりそうです" in [c.comment_text for c in filtered]
    
    def test_empty_result_returns_original(self):
        """全てフィルタされた場合は元のリストを返す"""
        comments = [
            self.create_comment("にわか雨に注意"),
            self.create_comment("一時的な雨です")
        ]
        
        filtered = filter_shower_comments(comments)
        
        assert len(filtered) == 2
        assert filtered == comments


class TestFilterMildUmbrellaComments:
    """filter_mild_umbrella_comments関数のテスト"""
    
    def create_comment(self, text: str) -> PastComment:
        """テスト用コメントを作成"""
        return PastComment(
            id=1,
            comment_text=text,
            comment_type=CommentType.ADVICE,
            weather_condition="雨",
            created_at=datetime.now()
        )
    
    def test_filter_mild_expressions(self):
        """控えめな傘表現をフィルタリング"""
        comments = [
            self.create_comment("傘があると安心です"),
            self.create_comment("傘を忘れずに持っていきましょう"),
            self.create_comment("傘がお守りになります"),
            self.create_comment("念のため傘を"),
            self.create_comment("折りたたみ傘があると便利")
        ]
        
        filtered = filter_mild_umbrella_comments(comments)
        
        assert len(filtered) == 1
        assert filtered[0].comment_text == "傘を忘れずに持っていきましょう"


class TestFilterForbiddenPhrases:
    """filter_forbidden_phrases関数のテスト"""
    
    def create_comment(self, text: str) -> PastComment:
        """テスト用コメントを作成"""
        return PastComment(
            id=1,
            comment_text=text,
            comment_type=CommentType.WEATHER_COMMENT,
            weather_condition="晴れ",
            created_at=datetime.now()
        )
    
    def test_filter_forbidden_phrases(self):
        """禁止フレーズを含むコメントをフィルタリング"""
        # 実際の禁止フレーズは FORBIDDEN_PHRASES に依存
        comments = [
            self.create_comment("今日は良い天気です"),
            self.create_comment("天気予報によると晴れです"),
            self.create_comment("素晴らしい一日になりそうです")
        ]
        
        # 禁止フレーズが含まれていない場合は全て残る
        filtered = filter_forbidden_phrases(comments)
        assert len(filtered) == len(comments)


class TestFilterSeasonalInappropriateComments:
    """filter_seasonal_inappropriate_comments関数のテスト"""
    
    def create_comment(self, text: str) -> PastComment:
        """テスト用コメントを作成"""
        return PastComment(
            id=1,
            comment_text=text,
            comment_type=CommentType.ADVICE,
            weather_condition="晴れ",
            created_at=datetime.now()
        )
    
    def test_summer_filtering(self):
        """夏季（6-9月）のフィルタリング"""
        comments = [
            self.create_comment("熱中症に注意しましょう"),
            self.create_comment("防寒対策をしっかりと"),
            self.create_comment("水分補給を忘れずに"),
            self.create_comment("暖房を効かせて過ごしましょう")
        ]
        
        # 7月（夏）
        filtered = filter_seasonal_inappropriate_comments(comments, 7)
        
        assert len(filtered) == 2
        assert "熱中症に注意しましょう" in [c.comment_text for c in filtered]
        assert "水分補給を忘れずに" in [c.comment_text for c in filtered]
    
    def test_winter_filtering(self):
        """冬季（12-2月）のフィルタリング"""
        comments = [
            self.create_comment("暖かくして過ごしましょう"),
            self.create_comment("熱中症対策を万全に"),
            self.create_comment("防寒着を着込んで"),
            self.create_comment("紫外線対策を忘れずに")
        ]
        
        # 1月（冬）
        filtered = filter_seasonal_inappropriate_comments(comments, 1)
        
        assert len(filtered) == 2
        assert "暖かくして過ごしましょう" in [c.comment_text for c in filtered]
        assert "防寒着を着込んで" in [c.comment_text for c in filtered]
    
    def test_spring_autumn_no_filtering(self):
        """春秋（3-5月、10-11月）はフィルタリングなし"""
        comments = [
            self.create_comment("過ごしやすい一日です"),
            self.create_comment("熱中症に注意"),
            self.create_comment("防寒対策を")
        ]
        
        # 4月（春）
        filtered_spring = filter_seasonal_inappropriate_comments(comments, 4)
        assert len(filtered_spring) == len(comments)
        
        # 10月（秋）
        filtered_autumn = filter_seasonal_inappropriate_comments(comments, 10)
        assert len(filtered_autumn) == len(comments)
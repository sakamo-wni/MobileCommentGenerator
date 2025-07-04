"""
過去コメント取得ノードのテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.nodes.retrieve_past_comments_node import (
    retrieve_past_comments_node,
)
from src.data.past_comment import PastComment, PastCommentCollection, CommentType
from src.data.comment_generation_state import CommentGenerationState
from src.data.weather_data import WeatherForecast


class TestRetrievePastCommentsFunction:
    """retrieve_past_comments_node 関数のテスト"""

    def test_retrieve_past_comments_node_success(self):
        """正常ケースのテスト"""
        # モックリポジトリの設定
        mock_comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="いい天気",
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=25.0,
            )
        ]
        
        with patch("src.nodes.retrieve_past_comments_node.LocalCommentRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo.search_similar_comments.return_value = mock_comments
            mock_repo_class.return_value = mock_repo
            
            # 入力状態
            state = CommentGenerationState(
                location_name="東京",
                weather_data=WeatherForecast(
                    location="東京",
                    datetime=datetime.now(),
                    weather_condition="晴れ",
                    temperature=25.0,
                    description="晴れ",
                    humidity=50.0,
                    wind_speed=5.0,
                    precipitation=0.0
                ),
                target_datetime=datetime.now()
            )
            
            # 関数実行
            result = retrieve_past_comments_node(state)
            
            # 結果確認
            assert result.past_comments is not None
            assert len(result.past_comments.comments) == 1
            assert result.past_comments.comments[0].comment_text == "いい天気"

    def test_retrieve_past_comments_node_no_location(self):
        """地点名なしのテスト"""
        state = CommentGenerationState(
            location_name=None,
            weather_data=WeatherForecast(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                temperature=25.0,
                description="晴れ",
                humidity=50.0,
                wind_speed=5.0,
                precipitation=0.0
            )
        )
        
        # 関数実行
        with pytest.raises(ValueError, match="location_name が指定されていません"):
            retrieve_past_comments_node(state)

    def test_retrieve_past_comments_node_no_weather_data(self):
        """天気データなしのテスト"""
        state = CommentGenerationState(
            location_name="東京",
            weather_data=None
        )
        
        # 関数実行
        with pytest.raises(ValueError, match="weather_data が指定されていません"):
            retrieve_past_comments_node(state)



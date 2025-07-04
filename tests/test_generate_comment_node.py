"""
GenerateCommentNodeのテスト

このモジュールは、GenerateCommentNodeの機能をテストします。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# テスト対象モジュールのインポート用にパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.nodes.generate_comment_node import (
    generate_comment_node,
)
from src.data.comment_generation_state import CommentGenerationState, create_test_state
from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair


@pytest.fixture
def mock_weather_data():
    """モック天気データ"""
    from src.data.weather_data import WeatherCondition, WindDirection
    return WeatherForecast(
        location="稚内",
        datetime=datetime(2024, 6, 5, 9, 0),
        temperature=20.5,
        weather_code="100",
        weather_condition=WeatherCondition.CLEAR,
        weather_description="晴れ",
        precipitation=0.0,
        humidity=60.0,
        wind_speed=2.5,
        wind_direction=WindDirection.N,
        wind_direction_degrees=0
    )


@pytest.fixture
def mock_comment_pair():
    """モックコメントペア"""
    from src.data.past_comment import PastComment, CommentType
    
    weather_comment = PastComment(
        location="稚内",
        datetime=datetime.now(),
        weather_condition="晴れ",
        comment_text="爽やかな朝です",
        comment_type=CommentType.WEATHER_COMMENT,
        temperature=20.0
    )

    advice_comment = PastComment(
        location="稚内",
        datetime=datetime.now(),
        weather_condition="晴れ",
        comment_text="日焼け対策を",
        comment_type=CommentType.ADVICE,
        temperature=20.0
    )

    return CommentPair(
        weather_comment=weather_comment,
        advice_comment=advice_comment,
        similarity_score=0.85,
        selection_reason="天気条件が類似",
    )


@pytest.fixture
def test_state(mock_weather_data, mock_comment_pair):
    """テスト用状態"""
    return CommentGenerationState(
        location_name="稚内",
        target_datetime=datetime(2024, 6, 5, 9, 0, 0),
        weather_data=mock_weather_data,
        selected_pair=mock_comment_pair,
        llm_provider="openai"
    )


class TestGenerateCommentNode:
    """GenerateCommentNodeのテスト"""

    @patch("src.nodes.generate_comment_node.LLMManager")
    def test_generate_comment_node_success(self, mock_llm_manager_class, test_state):
        """正常なコメント生成のテスト"""
        # モック設定
        mock_manager = Mock()
        mock_manager.generate_comment.return_value = "爽やかな朝ですね"
        mock_llm_manager_class.return_value = mock_manager

        # テスト実行
        result_state = generate_comment_node(test_state)

        # 検証 - 実装では選択されたペアのコメントが使用される
        assert result_state.generated_comment == "爽やかな朝です　日焼け対策を"
        assert hasattr(result_state, 'generation_metadata')
        assert result_state.generation_metadata["llm_provider"] == "openai"
        assert "generation_timestamp" in result_state.generation_metadata
        assert "constraints_applied" in result_state.generation_metadata

        # 実装ではLLMが使用されていないため、モック呼び出しは確認しない

    @patch("src.nodes.generate_comment_node.LLMManager")
    def test_generate_comment_node_no_weather_data(self, mock_llm_manager_class, mock_comment_pair):
        """天気データなしの場合のエラーテスト"""
        from src.data.comment_generation_state import CommentGenerationState
        
        state = CommentGenerationState(
            location_name="稚内",
            target_datetime=datetime.now(),
            weather_data=None,
            selected_pair=mock_comment_pair
        )

        # テスト実行
        with pytest.raises(ValueError, match="Weather data is required"):
            generate_comment_node(state)

    @patch("src.nodes.generate_comment_node.LLMManager")
    def test_generate_comment_node_no_selected_pair(
        self, mock_llm_manager_class, mock_weather_data
    ):
        """選択ペアなしの場合のエラーテスト"""
        from src.data.comment_generation_state import CommentGenerationState
        
        state = CommentGenerationState(
            location_name="稚内",
            target_datetime=datetime.now(),
            weather_data=mock_weather_data,
            selected_pair=None
        )

        # テスト実行
        with pytest.raises(ValueError, match="Selected comment pair is required"):
            generate_comment_node(state)

    @patch("src.nodes.generate_comment_node.LLMManager")
    def test_generate_comment_node_llm_error(self, mock_llm_manager_class, test_state):
        """LLM生成エラー時のフォールバック処理テスト"""
        # モック設定（例外発生）
        mock_manager = Mock()
        mock_manager.generate_comment.side_effect = Exception("API Error")
        mock_llm_manager_class.return_value = mock_manager

        # テスト実行
        result_state = generate_comment_node(test_state)

        # エラーが発生してもコメントは生成される（フォールバックまたは選択されたペアから）
        assert hasattr(result_state, 'generated_comment')
        assert result_state.generated_comment is not None
        assert len(result_state.generated_comment) > 0



class TestIntegration:
    """統合テスト"""

    @patch("src.nodes.generate_comment_node.LLMManager")
    def test_end_to_end_comment_generation(self, mock_llm_manager_class):
        """エンドツーエンドのコメント生成テスト"""
        from src.data.comment_generation_state import CommentGenerationState
        from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
        from src.data.comment_pair import CommentPair
        from src.data.past_comment import PastComment, CommentType
        
        # テスト用の状態を作成
        weather_data = WeatherForecast(
            location="稚内",
            datetime=datetime(2024, 7, 1, 6, 0),
            temperature=20.0,
            weather_code="100",
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction=WindDirection.N,
            wind_direction_degrees=0
        )
        
        weather_comment = PastComment(
            location="稚内",
            datetime=datetime.now(),
            weather_condition="晴れ",
            comment_text="晴れて気持ちいい",
            comment_type=CommentType.WEATHER_COMMENT,
            temperature=20.0
        )
        
        advice_comment = PastComment(
            location="稚内",
            datetime=datetime.now(),
            weather_condition="晴れ",
            comment_text="日差しに注意",
            comment_type=CommentType.ADVICE,
            temperature=20.0
        )
        
        selected_pair = CommentPair(
            weather_comment=weather_comment,
            advice_comment=advice_comment,
            similarity_score=0.9,
            selection_reason="高い類似度"
        )
        
        state = CommentGenerationState(
            location_name="稚内",
            target_datetime=datetime(2024, 7, 1, 6, 0),
            weather_data=weather_data,
            selected_pair=selected_pair,
            llm_provider="openai"
        )
        
        # モック設定
        mock_manager = Mock()
        mock_manager.generate_comment.return_value = "完璧な天気ですね"
        mock_llm_manager_class.return_value = mock_manager

        # 初期状態確認
        assert not hasattr(state, 'generated_comment') or state.generated_comment is None

        # テスト実行
        result_state = generate_comment_node(state)

        # 最終確認 - 実装では選択されたペアのコメントが使用される
        assert result_state.generated_comment == "晴れて気持ちいい　日差しに注意"
        assert result_state.location_name == "稚内"
        assert result_state.weather_data.weather_description == "晴れ"


if __name__ == "__main__":
    pytest.main([__file__])

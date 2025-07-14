"""統一コメント生成ワークフローのテスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import PastComment, CommentType
from src.nodes.unified_comment_generation_node import unified_comment_generation_node


class TestUnifiedCommentGeneration:
    """統一コメント生成ノードのテストクラス"""
    
    @pytest.fixture
    def mock_weather_data(self):
        """モックの天気データ"""
        weather_data = Mock()
        weather_data.weather_description = "晴れ"
        weather_data.temperature = 25.0
        weather_data.humidity = 60.0
        weather_data.wind_speed = 3.0
        return weather_data
    
    @pytest.fixture
    def mock_past_comments(self):
        """モックの過去コメント"""
        return [
            PastComment(
                id="1",
                comment_text="晴れていい天気",
                comment_type=CommentType.WEATHER_COMMENT,
                weather_condition="晴れ",
                usage_count=10,
                season="春"
            ),
            PastComment(
                id="2",
                comment_text="紫外線に注意",
                comment_type=CommentType.ADVICE,
                weather_condition="晴れ",
                usage_count=5,
                season="春"
            )
        ]
    
    @pytest.fixture
    def mock_state(self, mock_weather_data, mock_past_comments):
        """モックの状態"""
        state = CommentGenerationState()
        state.location_name = "東京"
        state.target_datetime = datetime.now()
        state.weather_data = mock_weather_data
        state.past_comments = mock_past_comments
        state.llm_provider = "openai"
        return state
    
    @patch('src.nodes.unified_comment_generation_node.LLMManager')
    def test_unified_generation_single_llm_call(self, mock_llm_manager_class, mock_state):
        """LLMが1回だけ呼ばれることを検証"""
        # モックのLLMマネージャーを設定
        mock_llm_instance = Mock()
        mock_llm_instance.generate.return_value = '''
        {
            "weather_index": 0,
            "advice_index": 0,
            "generated_comment": "晴れていい天気　紫外線に注意"
        }
        '''
        mock_llm_manager_class.return_value = mock_llm_instance
        
        # テスト実行
        result = unified_comment_generation_node(mock_state)
        
        # LLMが1回だけ呼ばれることを検証
        assert mock_llm_instance.generate.call_count == 1
        
        # 結果の検証
        assert result.final_comment == "晴れていい天気　紫外線に注意"
        assert result.selected_pair is not None
        assert result.generation_metadata.get("unified_generation") is True
    
    @patch('src.nodes.unified_comment_generation_node.LLMManager')
    def test_fallback_when_llm_response_invalid(self, mock_llm_manager_class, mock_state):
        """LLMレスポンスが無効な場合のフォールバック動作"""
        # 無効なJSONレスポンスを返すモック
        mock_llm_instance = Mock()
        mock_llm_instance.generate.return_value = "Invalid JSON response"
        mock_llm_manager_class.return_value = mock_llm_instance
        
        # テスト実行
        result = unified_comment_generation_node(mock_state)
        
        # フォールバックでコメントが結合されることを確認
        assert result.final_comment == "晴れていい天気　紫外線に注意"
        assert result.selected_pair is not None
    
    @patch('src.nodes.unified_comment_generation_node.LLMManager')
    @patch('src.nodes.unified_comment_generation_node.check_ng_words')
    def test_ng_word_detection(self, mock_check_ng_words, mock_llm_manager_class, mock_state):
        """NGワード検出時の動作テスト"""
        # LLMレスポンスのモック
        mock_llm_instance = Mock()
        mock_llm_instance.generate.return_value = '''
        {
            "weather_index": 0,
            "advice_index": 0,
            "generated_comment": "禁止ワードを含むコメント"
        }
        '''
        mock_llm_manager_class.return_value = mock_llm_instance
        
        # NGワードが検出されるように設定
        mock_check_ng_words.return_value = {
            "is_valid": False,
            "found_words": ["禁止ワード"]
        }
        
        # テスト実行
        result = unified_comment_generation_node(mock_state)
        
        # NGワードが検出された場合、選択されたコメントの結合が使用されることを確認
        assert result.final_comment == "晴れていい天気　紫外線に注意"
        assert mock_check_ng_words.called
    
    def test_error_handling_no_weather_data(self, mock_state):
        """天気データがない場合のエラーハンドリング"""
        mock_state.weather_data = None
        
        # テスト実行
        result = unified_comment_generation_node(mock_state)
        
        # エラーが記録されることを確認
        assert result.errors is not None
        assert len(result.errors) > 0
        assert "天気データが利用できません" in str(result.errors)
    
    def test_error_handling_no_past_comments(self, mock_state):
        """過去コメントがない場合のエラーハンドリング"""
        mock_state.past_comments = None
        
        # テスト実行
        result = unified_comment_generation_node(mock_state)
        
        # エラーが記録されることを確認
        assert result.errors is not None
        assert len(result.errors) > 0
        assert "過去コメントが存在しません" in str(result.errors)
    
    def test_weather_forecast_object_compatibility(self, mock_state):
        """WeatherForecastオブジェクトとの互換性テスト"""
        # WeatherForecastオブジェクトのモック
        from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
        weather_forecast = WeatherForecast(
            location="東京",
            datetime=datetime.now(),
            temperature=25.0,
            weather_code="100",
            weather_condition=WeatherCondition.SUNNY,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction=WindDirection.N,
            wind_direction_degrees=0
        )
        mock_state.weather_data = weather_forecast
        
        with patch('src.nodes.unified_comment_generation_node.LLMManager') as mock_llm_manager_class:
            mock_llm_instance = Mock()
            mock_llm_instance.generate.return_value = '''
            {
                "weather_index": 0,
                "advice_index": 0,
                "generated_comment": "晴れていい天気　紫外線に注意"
            }
            '''
            mock_llm_manager_class.return_value = mock_llm_instance
            
            # テスト実行（エラーが発生しないことを確認）
            result = unified_comment_generation_node(mock_state)
            
            assert result.final_comment is not None
            assert result.errors is None or len(result.errors) == 0
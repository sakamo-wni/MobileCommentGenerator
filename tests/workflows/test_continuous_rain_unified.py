"""統一モードでの連続雨判定テスト"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import PastComment, CommentType
from src.nodes.unified_comment_generation_node import (
    unified_comment_generation_node,
    _check_continuous_rain,
    _filter_shower_comments,
    _filter_mild_umbrella_comments
)


class TestContinuousRainUnified:
    """統一モードでの連続雨判定のテストクラス"""
    
    @pytest.fixture
    def mock_weather_data(self):
        """モックの天気データ（雨）"""
        weather_data = Mock()
        weather_data.weather_description = "雨"
        weather_data.temperature = 20.0
        weather_data.humidity = 80.0
        weather_data.wind_speed = 5.0
        weather_data.precipitation = 10.0
        return weather_data
    
    @pytest.fixture
    def mock_period_forecasts_all_rain(self):
        """4時間すべて雨の予報データ"""
        forecasts = []
        for hour in [9, 12, 15, 18]:
            forecast = Mock()
            forecast.datetime = datetime(2024, 1, 1, hour, 0)
            forecast.weather = "雨"
            forecast.precipitation = 5.0
            forecasts.append(forecast)
        return forecasts
    
    @pytest.fixture
    def mock_period_forecasts_partial_rain(self):
        """部分的に雨の予報データ"""
        forecasts = []
        for hour, weather, precip in [(9, "晴れ", 0.0), (12, "晴れ", 0.0), (15, "雨", 5.0), (18, "雨", 3.0)]:
            forecast = Mock()
            forecast.datetime = datetime(2024, 1, 1, hour, 0)
            forecast.weather = weather
            forecast.precipitation = precip
            forecasts.append(forecast)
        return forecasts
    
    @pytest.fixture
    def mock_past_comments_with_shower(self):
        """にわか雨表現を含む過去コメント"""
        return [
            PastComment(
                id="1",
                comment_text="にわか雨が心配です",
                comment_type=CommentType.WEATHER_COMMENT,
                weather_condition="雨",
                usage_count=10,
                season="春"
            ),
            PastComment(
                id="2",
                comment_text="雨が続く一日になりそう",
                comment_type=CommentType.WEATHER_COMMENT,
                weather_condition="雨",
                usage_count=8,
                season="春"
            ),
            PastComment(
                id="3",
                comment_text="傘があると安心です",
                comment_type=CommentType.ADVICE,
                weather_condition="雨",
                usage_count=5,
                season="春"
            ),
            PastComment(
                id="4",
                comment_text="傘は必須です",
                comment_type=CommentType.ADVICE,
                weather_condition="雨",
                usage_count=7,
                season="春"
            )
        ]
    
    def test_check_continuous_rain_all_rain(self, mock_period_forecasts_all_rain):
        """4時間すべて雨の場合の連続雨判定"""
        state = CommentGenerationState()
        state.generation_metadata = {'period_forecasts': mock_period_forecasts_all_rain}
        
        assert _check_continuous_rain(state) is True
    
    def test_check_continuous_rain_partial_rain(self, mock_period_forecasts_partial_rain):
        """部分的に雨の場合の判定"""
        state = CommentGenerationState()
        state.generation_metadata = {'period_forecasts': mock_period_forecasts_partial_rain}
        
        assert _check_continuous_rain(state) is False
    
    def test_check_continuous_rain_no_metadata(self):
        """メタデータがない場合の判定"""
        state = CommentGenerationState()
        assert _check_continuous_rain(state) is False
    
    def test_filter_shower_comments(self, mock_past_comments_with_shower):
        """にわか雨表現のフィルタリング"""
        weather_comments = [c for c in mock_past_comments_with_shower if c.comment_type == CommentType.WEATHER_COMMENT]
        filtered = _filter_shower_comments(weather_comments)
        
        # にわか雨表現を含むコメントが除外されることを確認
        assert len(filtered) == 1
        assert all("にわか雨" not in c.comment_text for c in filtered)
        assert "雨が続く一日になりそう" in filtered[0].comment_text
    
    def test_filter_mild_umbrella_comments(self, mock_past_comments_with_shower):
        """控えめな傘表現のフィルタリング"""
        advice_comments = [c for c in mock_past_comments_with_shower if c.comment_type == CommentType.ADVICE]
        filtered = _filter_mild_umbrella_comments(advice_comments)
        
        # 控えめな表現が除外されることを確認
        assert len(filtered) == 1
        assert all("傘があると安心" not in c.comment_text for c in filtered)
        assert "傘は必須です" in filtered[0].comment_text
    
    @patch('src.nodes.unified_comment_generation_node.LLMManager')
    def test_unified_generation_with_continuous_rain(
        self, 
        mock_llm_manager_class, 
        mock_weather_data,
        mock_period_forecasts_all_rain,
        mock_past_comments_with_shower
    ):
        """連続雨時の統一モード生成テスト"""
        # モックのLLMマネージャーを設定
        mock_llm_instance = Mock()
        mock_llm_instance.generate.return_value = '''
        {
            "weather_index": 0,
            "advice_index": 0,
            "generated_comment": "雨が続く一日　傘は必須です"
        }
        '''
        mock_llm_manager_class.return_value = mock_llm_instance
        
        # 状態の設定
        state = CommentGenerationState()
        state.location_name = "東京"
        state.target_datetime = datetime.now()
        state.weather_data = mock_weather_data
        state.past_comments = mock_past_comments_with_shower
        state.generation_metadata = {'period_forecasts': mock_period_forecasts_all_rain}
        state.llm_provider = "openai"
        
        # テスト実行
        result = unified_comment_generation_node(state)
        
        # プロンプトに連続雨の指示が含まれることを確認
        call_args = mock_llm_instance.generate.call_args[0][0]
        assert "4時間以上の連続した雨が予測されています" in call_args
        assert "にわか雨」「一時的な雨」「急な雨」などの表現は避けてください" in call_args
        
        # 結果の確認
        assert result.final_comment is not None
        assert "にわか雨" not in result.final_comment
        assert result.generation_metadata.get("is_continuous_rain") is True
    
    def test_filter_all_comments_fallback(self):
        """すべてのコメントがフィルタリングされた場合のフォールバック"""
        # すべてにわか雨表現を含むコメント
        all_shower_comments = [
            PastComment(
                id="1",
                comment_text="にわか雨に注意",
                comment_type=CommentType.WEATHER_COMMENT,
                weather_condition="雨",
                usage_count=10,
                season="春"
            ),
            PastComment(
                id="2",
                comment_text="急な雨が心配",
                comment_type=CommentType.WEATHER_COMMENT,
                weather_condition="雨",
                usage_count=8,
                season="春"
            )
        ]
        
        filtered = _filter_shower_comments(all_shower_comments)
        
        # 元のリストが返されることを確認
        assert len(filtered) == len(all_shower_comments)
        assert filtered == all_shower_comments
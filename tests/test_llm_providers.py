"""
LLMプロバイダーのテスト
"""

import pytest
from unittest.mock import patch, MagicMock, Mock

from src.llm.providers.gemini_provider import GeminiProvider
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.data.comment_pair import CommentPair
from src.data.past_comment import PastComment, CommentType
from datetime import datetime


class TestGeminiProvider:
    """Geminiプロバイダーのテストクラス"""

    @pytest.fixture
    def sample_data(self):
        """テスト用サンプルデータ"""
        weather_data = WeatherForecast(
            location="東京",
            datetime=datetime.now(),
            temperature=25.0,
            weather_code="100",
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=50.0,
            wind_speed=5.0,
            wind_direction=WindDirection.N,
            wind_direction_degrees=0
        )

        weather_comment = PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="晴れ",
            temperature=24.0,
            comment_text="爽やかな朝です",
            comment_type=CommentType.WEATHER_COMMENT,
        )

        advice_comment = PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="晴れ",
            temperature=24.0,
            comment_text="日焼け対策を",
            comment_type=CommentType.ADVICE,
        )

        comment_pair = CommentPair(
            weather_comment=weather_comment,
            advice_comment=advice_comment,
            similarity_score=0.95,
            selection_reason="高い類似度",
        )

        constraints = {"max_length": 15, "ng_words": ["災害", "危険"], "time_period": "朝"}

        return weather_data, comment_pair, constraints

    @patch("src.llm.providers.gemini_provider.genai")
    def test_gemini_provider_init(self, mock_genai):
        """Geminiプロバイダー初期化のテスト"""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="test-key", model="gemini-pro")

        mock_genai.configure.assert_called_once_with(api_key="test-key")
        mock_genai.GenerativeModel.assert_called_once_with("gemini-pro")
        assert provider.model_name == "gemini-pro"

    @patch("src.llm.providers.gemini_provider.genai")
    def test_gemini_generate_comment(self, mock_genai, sample_data):
        """Geminiでのコメント生成テスト"""
        # モックの設定
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "今日は爽やかですね"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="test-key")
        weather_data, comment_pair, constraints = sample_data

        result = provider.generate_comment(
            weather_data=weather_data, past_comments=comment_pair, constraints=constraints
        )

        assert result == "今日は爽やかですね"
        mock_model.generate_content.assert_called_once()
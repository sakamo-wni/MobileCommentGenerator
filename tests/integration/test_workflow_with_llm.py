"""
LLM統合を含むワークフローの統合テスト
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os

from src.workflows.comment_generation_workflow import (
    create_comment_generation_workflow,
    run_comment_generation
)
from src.data.past_comment import PastComment, CommentType


class TestWorkflowWithLLMIntegration:
    """ワークフローとLLM統合のテストクラス"""
    
    @pytest.fixture
    def mock_env_vars(self):
        """環境変数のモック"""
        env_vars = {
            "WXTECH_API_KEY": "test-wx-key",
            "OPENAI_API_KEY": "test-openai-key",
            "GEMINI_API_KEY": "test-gemini-key",
            "ANTHROPIC_API_KEY": "test-anthropic-key"
        }
        with patch.dict(os.environ, env_vars):
            yield
    
    @patch('src.nodes.weather_forecast_node.requests.get')
    @patch('src.repositories.lazy_comment_repository.LazyCommentRepository')
    @patch('src.llm.providers.openai_provider.OpenAI')
    def test_complete_workflow_with_openai(
        self,
        mock_openai_class,
        mock_local_repo_class,
        mock_requests_get,
        mock_env_vars
    ):
        """完全なワークフローのテスト（OpenAI使用）"""
        # 天気APIのモック
        mock_weather_response = MagicMock()
        mock_weather_response.json.return_value = {
            "forecasts": [{
                "location": "東京",
                "datetime": "2024-06-05T09:00:00",
                "weather_code": "clear",
                "weather_description": "晴れ",
                "temperature": 25.0,
                "humidity": 60,
                "wind_speed": 2.5
            }]
        }
        mock_requests_get.return_value = mock_weather_response
        
        # S3クライアントのモック
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.return_value = {
            'Contents': [{'Key': 'comments_2024_06.jsonl'}]
        }
        mock_s3.get_object.return_value = {
            'Body': MagicMock(
                read=lambda: '{"location": "東京", "weather_condition": "晴れ", "temperature": 24.0, "comment_text": "爽やかな朝です", "comment_type": "weather_comment"}\n{"location": "東京", "weather_condition": "晴れ", "temperature": 24.0, "comment_text": "日焼け対策を", "comment_type": "advice"}'.encode('utf-8')
            )
        }
        mock_boto_client.return_value = mock_s3
        
        # OpenAIクライアントのモック
        mock_openai = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "今日は爽やかですね"
        mock_openai.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai
        
        # ワークフロー実行
        result = run_comment_generation(
            location_name="東京",
            llm_provider="openai"
        )
        
        # 検証
        assert result["success"] is True
        assert result["final_comment"] == "今日は爽やかですね"
        assert "generation_metadata" in result
        assert result["retry_count"] >= 0
        
        # API呼び出しの検証
        mock_requests_get.assert_called_once()
        mock_openai.chat.completions.create.assert_called_once()
    
    @patch('src.nodes.weather_forecast_node.requests.get')
    @patch('src.nodes.retrieve_past_comments_node.boto3.client')
    @patch('src.llm.providers.gemini_provider.genai')
    def test_complete_workflow_with_gemini(
        self,
        mock_genai,
        mock_local_repo_class,
        mock_requests_get,
        mock_env_vars
    ):
        """完全なワークフローのテスト（Gemini使用）"""
        # 天気APIのモック（OpenAIテストと同じ）
        mock_weather_response = MagicMock()
        mock_weather_response.json.return_value = {
            "forecasts": [{
                "location": "東京",
                "datetime": "2024-06-05T09:00:00",
                "weather_code": "rain",
                "weather_description": "雨",
                "temperature": 20.0,
                "humidity": 80,
                "wind_speed": 3.0
            }]
        }
        mock_requests_get.return_value = mock_weather_response
        
        # S3クライアントのモック
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.return_value = {
            'Contents': [{'Key': 'comments_2024_06.jsonl'}]
        }
        mock_s3.get_object.return_value = {
            'Body': MagicMock(
                read=lambda: '{"location": "東京", "weather_condition": "雨", "temperature": 19.0, "comment_text": "雨の一日です", "comment_type": "weather_comment"}\n{"location": "東京", "weather_condition": "雨", "temperature": 19.0, "comment_text": "傘を持って", "comment_type": "advice"}'.encode('utf-8')
            )
        }
        mock_boto_client.return_value = mock_s3
        
        # Geminiクライアントのモック
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "傘をお忘れなく"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # ワークフロー実行
        result = run_comment_generation(
            location_name="東京",
            llm_provider="gemini"
        )
        
        # 検証
        assert result["success"] is True
        assert result["final_comment"] == "傘をお忘れなく"
        assert "generation_metadata" in result
        
        # API呼び出しの検証
        mock_genai.configure.assert_called_once_with(api_key="test-gemini-key")
        mock_model.generate_content.assert_called_once()
    
    @patch('src.nodes.weather_forecast_node.requests.get')
    @patch('src.repositories.lazy_comment_repository.LazyCommentRepository')
    @patch('src.llm.providers.openai_provider.OpenAI')
    def test_workflow_with_retry_logic(
        self,
        mock_openai_class,
        mock_local_repo_class,
        mock_requests_get,
        mock_env_vars
    ):
        """リトライロジックのテスト"""
        # 天気APIとS3のモック設定（省略）
        mock_weather_response = MagicMock()
        mock_weather_response.json.return_value = {
            "forecasts": [{
                "location": "東京",
                "datetime": "2024-06-05T09:00:00",
                "weather_code": "clear",
                "weather_description": "晴れ",
                "temperature": 25.0
            }]
        }
        mock_requests_get.return_value = mock_weather_response
        
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.return_value = {'Contents': [{'Key': 'test.jsonl'}]}
        mock_s3.get_object.return_value = {
            'Body': MagicMock(
                read=lambda: '{"location": "東京", "weather_condition": "晴れ", "temperature": 24.0, "comment_text": "今日は本当に素晴らしい天気ですね", "comment_type": "weather_comment"}\n{"location": "東京", "weather_condition": "晴れ", "temperature": 24.0, "comment_text": "日焼け止めを", "comment_type": "advice"}'.encode('utf-8')
            )
        }
        mock_boto_client.return_value = mock_s3
        
        # OpenAIクライアントのモック
        # 最初は長すぎるコメント、次はNGワード、最後に成功
        mock_openai = MagicMock()
        responses = [
            "今日は本当に素晴らしい天気ですね",  # 長すぎる
            "危険な天気です",  # NGワード
            "今日は爽やかですね"  # 成功
        ]
        
        mock_response_list = []
        for response_text in responses:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = response_text
            mock_response_list.append(mock_response)
        
        mock_openai.chat.completions.create.side_effect = mock_response_list
        mock_openai_class.return_value = mock_openai
        
        # ワークフロー実行
        result = run_comment_generation(
            location_name="東京",
            llm_provider="openai"
        )
        
        # 検証
        assert result["success"] is True
        assert result["final_comment"] == "今日は爽やかですね"
        assert result["retry_count"] >= 2  # 少なくとも2回はリトライ
        
        # LLMが複数回呼ばれたことを確認
        assert mock_openai.chat.completions.create.call_count >= 3
    
    def test_workflow_with_missing_api_key(self):
        """APIキーがない場合のテスト"""
        # 環境変数をクリア
        with patch.dict(os.environ, {}, clear=True):
            result = run_comment_generation(
                location_name="東京",
                llm_provider="openai"
            )
            
            # エラーで終了することを確認
            assert result["success"] is False
            assert "error" in result

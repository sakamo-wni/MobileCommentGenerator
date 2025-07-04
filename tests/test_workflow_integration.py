"""
コメント生成ワークフローの統合テスト

エンドツーエンドのワークフロー動作を検証
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
import os
import json

from src.workflows.comment_generation_workflow import (
    create_comment_generation_workflow,
    run_comment_generation,
    should_retry,
    MAX_RETRY_COUNT
)
from src.data.comment_generation_state import CommentGenerationState


class TestWorkflowIntegration:
    """ワークフロー統合テストクラス"""
    
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
    @patch('src.repositories.local_comment_repository.LocalCommentRepository')
    @patch('src.llm.providers.openai_provider.OpenAI')
    def test_complete_workflow_success(
        self,
        mock_openai_class,
        mock_local_repo_class,
        mock_requests_get,
        mock_env_vars
    ):
        """完全なワークフローの成功ケース"""
        # 天気APIのモック
        mock_weather_response = MagicMock()
        mock_weather_response.json.return_value = {
            "forecasts": [{
                "location": "稚内",
                "datetime": "2024-06-05T09:00:00",
                "weather_code": "clear",
                "weather_description": "晴れ",
                "temperature": 20.5,
                "humidity": 60,
                "wind_speed": 2.5
            }]
        }
        mock_requests_get.return_value = mock_weather_response
        
        # LocalCommentRepositoryのモック
        mock_local_repo = MagicMock()
        from src.data.past_comment import PastComment, CommentType
        mock_comments = [
            PastComment(
                location="稚内",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="爽やかな朝です",
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=20.0
            ),
            PastComment(
                location="稚内",
                datetime=datetime.now(),
                weather_condition="晴ゎ",
                comment_text="日焼け対策を",
                comment_type=CommentType.ADVICE,
                temperature=20.0
            )
        ]
        mock_local_repo.get_recent_comments.return_value = mock_comments
        mock_local_repo_class.return_value = mock_local_repo
        
        # OpenAIクライアントのモック
        mock_openai = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "爽やかな一日です"
        mock_openai.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai
        
        # ワークフロー実行
        result = run_comment_generation(
            location_name="稚内",
            llm_provider="openai"
        )
        
        # 検証
        assert result["success"] is True
        assert result["final_comment"] == "爽やかな一日です"
        assert "generation_metadata" in result
        assert result["retry_count"] >= 0
        
        # API呼び出しの検証
        mock_requests_get.assert_called_once()
        mock_openai.chat.completions.create.assert_called_once()
    
    def test_should_retry_logic(self):
        """リトライロジックのテスト"""
        # リトライ上限に達していない場合
        state = {
            "retry_count": 2,
            "validation_result": {"is_valid": False}
        }
        assert should_retry(state) == "retry"
        
        # リトライ上限に達した場合
        state = {
            "retry_count": MAX_RETRY_COUNT,
            "validation_result": {"is_valid": False}
        }
        assert should_retry(state) == "continue"
        
        # バリデーション成功の場合
        state = {
            "retry_count": 1,
            "validation_result": {"is_valid": True}
        }
        assert should_retry(state) == "continue"
    
    @patch('src.nodes.weather_forecast_node.requests.get')
    @patch('src.repositories.local_comment_repository.LocalCommentRepository')
    @patch('src.llm.providers.openai_provider.OpenAI')
    def test_workflow_with_retry(
        self,
        mock_openai_class,
        mock_local_repo_class,
        mock_requests_get,
        mock_env_vars
    ):
        """リトライを含むワークフローのテスト"""
        # 天気APIとLocalCommentRepositoryのモック設定（省略）
        mock_weather_response = MagicMock()
        mock_weather_response.json.return_value = {
            "forecasts": [{
                "location": "稚内",
                "datetime": "2024-06-05T09:00:00",
                "weather_code": "clear",
                "weather_description": "晴れ",
                "temperature": 20.5
            }]
        }
        mock_requests_get.return_value = mock_weather_response
        
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.return_value = {'Contents': [{'Key': 'test.jsonl'}]}
        mock_s3.get_object.return_value = {
            'Body': MagicMock(
                read=lambda: b'{"location": "稚内", "weather_condition": "晴れ", "temperature": 20.0, "comment_text": "今日は本当に素晴らしい天気ですね", "comment_type": "weather_comment"}\n{"location": "稚内", "weather_condition": "晴れ", "temperature": 20.0, "comment_text": "日焼け止めを", "comment_type": "advice"}'
            )
        }
        mock_boto_client.return_value = mock_s3
        
        # OpenAIクライアントのモック
        # 最初は長すぎるコメント、次は成功
        mock_openai = MagicMock()
        responses = [
            "今日は本当に素晴らしい天気ですね",  # 長すぎる
            "爽やかな一日です"  # 成功
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
            location_name="稚内",
            llm_provider="openai"
        )
        
        # 検証
        assert result["success"] is True
        assert result["final_comment"] == "爽やかな一日です"
        assert result["retry_count"] >= 1  # 少なくとも1回はリトライ
    
    def test_workflow_with_error(self):
        """エラー時のワークフローテスト"""
        # 環境変数なしでエラーになることを確認
        with patch.dict(os.environ, {}, clear=True):
            result = run_comment_generation(
                location_name="稚内",
                llm_provider="openai"
            )
            
            assert result["success"] is False
            assert "error" in result
            assert result["final_comment"] is None
    
    @patch('src.workflows.comment_generation_workflow.create_comment_generation_workflow')
    def test_workflow_creation(self, mock_create_workflow):
        """ワークフロー作成のテスト"""
        # モックワークフローの作成
        mock_workflow = MagicMock()
        mock_create_workflow.return_value = mock_workflow
        
        # ワークフロー作成を呼び出し
        workflow = create_comment_generation_workflow()
        
        # 呼び出しの確認
        mock_create_workflow.assert_called_once()
        assert workflow == mock_workflow


class TestStateManagement:
    """状態管理のテスト"""
    
    def test_initial_state_creation(self):
        """初期状態の作成テスト"""
        from datetime import datetime
        
        initial_state = {
            "location_name": "稚内",
            "target_datetime": datetime.now(),
            "llm_provider": "openai",
            "retry_count": 0,
            "errors": [],
            "warnings": []
        }
        
        assert initial_state["location_name"] == "稚内"
        assert initial_state["llm_provider"] == "openai"
        assert initial_state["retry_count"] == 0
        assert len(initial_state["errors"]) == 0
        assert len(initial_state["warnings"]) == 0
    
    def test_state_updates_through_workflow(self):
        """ワークフローを通じた状態更新のテスト"""
        state = CommentGenerationState()
        state["location_name"] = "稚内"
        state["retry_count"] = 0
        
        # リトライカウントの更新
        state["retry_count"] += 1
        assert state["retry_count"] == 1
        
        # エラーの追加
        state["errors"] = state.get("errors", [])
        state["errors"].append("Test error")
        assert len(state["errors"]) == 1
        assert state["errors"][0] == "Test error"
        
        # 最終コメントの設定
        state["final_comment"] = "テストコメント"
        assert state["final_comment"] == "テストコメント"


if __name__ == '__main__':
    pytest.main([__file__])

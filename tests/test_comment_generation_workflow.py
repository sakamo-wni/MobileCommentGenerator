"""
天気コメント生成ワークフローのテスト
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.workflows.comment_generation_workflow import (
    create_comment_generation_workflow,
    run_comment_generation,
    should_retry,
)
from src.data.comment_generation_state import CommentGenerationState


class TestCommentGenerationWorkflow:
    """ワークフローのテストスイート"""

    def test_workflow_creation(self):
        """ワークフローが正しく構築されることを確認"""
        workflow = create_comment_generation_workflow()
        assert workflow is not None
        # LangGraphのコンパイル済みグラフであることを確認
        assert hasattr(workflow, "invoke")

    def test_should_retry_logic(self):
        """リトライロジックのテスト"""
        # リトライ不要のケース
        state = {"retry_count": 0, "validation_result": {"is_valid": True}}
        assert should_retry(state) == "continue"

        # リトライ必要のケース
        state = {"retry_count": 2, "validation_result": {"is_valid": False}}
        assert should_retry(state) == "retry"

        # リトライ上限に達したケース
        state = {"retry_count": 5, "validation_result": {"is_valid": False}}
        assert should_retry(state) == "continue"

    @patch("src.workflows.comment_generation_workflow.fetch_weather_forecast_node")
    @patch("src.workflows.comment_generation_workflow.retrieve_past_comments_node")
    @patch("src.workflows.comment_generation_workflow.select_comment_pair_node")
    @patch("src.workflows.comment_generation_workflow.generate_comment_node")
    def test_run_comment_generation_success(self, mock_generate, mock_select, mock_retrieve, mock_fetch):
        """正常系のワークフロー実行テスト"""
        # モックの設定
        mock_fetch.return_value = {
            "weather_data": {"weather_condition": "晴れ", "temperature": 20.0}
        }
        mock_retrieve.return_value = {
            "past_comments": [{"text": "爽やかな朝です", "type": "weather_comment"}]
        }
        mock_select.return_value = {
            "selected_pair": {"weather_comment": "爽やかな朝です", "advice": "日焼け対策を"}
        }
        mock_generate.return_value = {"final_comment": "気持ちいい朝ですね"}

        # 実行
        result = run_comment_generation(location_name="東京", llm_provider="openai")

        # アサーション
        assert result["success"] is True
        assert result["final_comment"] is not None
        assert "generation_metadata" in result

    def test_run_comment_generation_missing_location(self):
        """地点名が指定されていない場合のテスト"""
        result = run_comment_generation(location_name="", llm_provider="openai")

        assert result["success"] is False
        assert result["error"] is not None
        assert result["final_comment"] is None

    @patch("src.workflows.comment_generation_workflow.create_comment_generation_workflow")
    def test_run_comment_generation_workflow_error(self, mock_create):
        """ワークフロー実行中のエラーハンドリング"""
        # ワークフローがエラーを投げるように設定
        mock_workflow = MagicMock()
        mock_workflow.invoke.side_effect = Exception("ワークフローエラー")
        mock_create.return_value = mock_workflow

        result = run_comment_generation(location_name="東京", llm_provider="openai")

        assert result["success"] is False
        assert "ワークフローエラー" in result["error"]
        assert result["final_comment"] is None

    def test_workflow_with_retry_loop(self):
        """リトライループを含むワークフローのテスト"""
        workflow = create_comment_generation_workflow()

        # 初期状態（モックノードでリトライをシミュレート）
        initial_state = {
            "location_name": "東京",
            "target_datetime": datetime.now(),
            "llm_provider": "openai",
            "retry_count": 0,
        }

        # 実行（モックノードがリトライを2回発生させる）
        result = workflow.invoke(initial_state)

        # リトライが発生したことを確認
        assert result.get("retry_count", 0) >= 2
        assert result.get("validation_result", {}).get("is_valid") is True


class TestWorkflowIntegration:
    """ワークフロー統合テスト"""

    @pytest.mark.integration
    def test_end_to_end_workflow(self):
        """エンドツーエンドのワークフローテスト（モックノード使用）"""
        result = run_comment_generation(
            location_name="稚内", target_datetime=datetime.now(), llm_provider="openai"
        )

        # 基本的な結果の確認
        assert result is not None
        assert isinstance(result, dict)

        # メタデータの確認
        if result.get("success"):
            metadata = result.get("generation_metadata", {})
            assert metadata.get("location") == "稚内"
            assert metadata.get("llm_provider") == "openai"
            assert "execution_time_ms" in metadata
            assert "retry_count" in metadata

    @pytest.mark.integration
    def test_workflow_performance(self):
        """ワークフローのパフォーマンステスト"""
        import time

        start_time = time.time()
        result = run_comment_generation(location_name="東京", llm_provider="openai")
        execution_time = time.time() - start_time

        # 30秒以内に完了することを確認
        assert execution_time < 30.0

        # 実行時間がメタデータに記録されていることを確認
        if result.get("success"):
            assert result.get("execution_time_ms", 0) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

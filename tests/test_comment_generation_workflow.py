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
        from src.data.comment_generation_state import CommentGenerationState
        from src.data.weather_data import WeatherForecast
        from src.data.past_comment import PastComment, PastCommentCollection, CommentType
        from src.data.comment_pair import CommentPair
        from datetime import datetime
        
        # モックの設定 - CommentGenerationStateオブジェクトを返すように
        def mock_fetch_side_effect(state):
            from src.data.weather_data import WeatherCondition, WindDirection
            state.weather_data = WeatherForecast(
                location="東京",
                datetime=datetime.now(),
                temperature=20.0,
                weather_code="100",
                weather_condition=WeatherCondition.CLEAR,
                weather_description="晴れ",
                precipitation=0.0,
                humidity=50.0,
                wind_speed=5.0,
                wind_direction=WindDirection.N,
                wind_direction_degrees=0
            )
            return state
            
        def mock_retrieve_side_effect(state):
            state.past_comments = PastCommentCollection(
                comments=[
                    PastComment(
                        location="東京",
                        datetime=datetime.now(),
                        weather_condition="晴れ",
                        comment_text="爽やかな朝です",
                        comment_type=CommentType.WEATHER_COMMENT,
                        temperature=20.0
                    )
                ]
            )
            return state
            
        def mock_generate_side_effect(state):
            state.generated_comment = "気持ちいい朝ですね　日差しが強いので帽子をかぶりましょう"
            return state
        
        def mock_select_side_effect(state):
            state.selected_pair = CommentPair(
                weather_comment=PastComment(
                    location="東京",
                    datetime=datetime.now(),
                    weather_condition="晴れ",
                    comment_text="爽やかな朝です",
                    comment_type=CommentType.WEATHER_COMMENT,
                    temperature=20.0
                ),
                advice_comment=PastComment(
                    location="東京",
                    datetime=datetime.now(),
                    weather_condition="晴れ",
                    comment_text="紫外線対策を忘れずに",
                    comment_type=CommentType.ADVICE,
                    temperature=20.0
                ),
                similarity_score=0.9,
                selection_reason="天気条件が一致"
            )
            return state
            
        mock_fetch.side_effect = mock_fetch_side_effect
        mock_retrieve.side_effect = mock_retrieve_side_effect
        mock_select.side_effect = mock_select_side_effect
        mock_generate.side_effect = mock_generate_side_effect

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

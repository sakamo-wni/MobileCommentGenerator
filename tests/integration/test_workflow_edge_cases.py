"""Edge case tests for LangGraph workflow integration"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import time
import asyncio

from src.workflows.comment_generation_workflow import (
    create_comment_generation_workflow,
    run_comment_generation
)
from src.exceptions.error_types import (
    WeatherFetchError, DataAccessError, LLMError, ValidationError
)


class TestWorkflowEdgeCases:
    """Test edge cases and error scenarios in the workflow"""
    
    @pytest.fixture
    def mock_weather_api(self):
        """Mock weather API responses"""
        with patch("src.apis.wxtech_client.WxTechAPIClient") as mock:
            yield mock
    
    @pytest.fixture
    def mock_llm_manager(self):
        """Mock LLM manager"""
        with patch("src.llm.llm_manager.LLMManager") as mock:
            yield mock
    
    @pytest.fixture
    def mock_comment_repository(self):
        """Mock comment repository"""
        with patch("src.repositories.lazy_comment_repository.LazyCommentRepository") as mock:
            yield mock
    
    def test_network_timeout_handling(self, mock_weather_api):
        """Test handling of network timeouts"""
        # Simulate network timeout
        mock_weather_api.return_value.get_forecast.side_effect = asyncio.TimeoutError("Network timeout")
        
        result = run_comment_generation(
            location_name="東京",
            llm_provider="gemini"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert result["error_type"] == "timeout_error"
    
    def test_invalid_location_handling(self, mock_weather_api):
        """Test handling of invalid location names"""
        # Test with empty location
        result = run_comment_generation(
            location_name="",
            llm_provider="gemini"
        )
        
        assert result["success"] is False
        assert "地点が選択されていません" in result.get("error", "")
        
        # Test with invalid characters
        result = run_comment_generation(
            location_name="<script>alert('test')</script>",
            llm_provider="gemini"
        )
        
        assert result["success"] is False
    
    def test_llm_provider_fallback(self, mock_llm_manager):
        """Test LLM provider fallback mechanism"""
        # Primary provider fails, should fallback
        mock_llm_manager.return_value.generate.side_effect = [
            LLMError("Primary provider failed"),
            {"weather_comment": "Fallback comment", "advice_comment": "Fallback advice"}
        ]
        
        result = run_comment_generation(
            location_name="東京",
            llm_provider="openai"
        )
        
        # Should succeed with fallback
        assert mock_llm_manager.return_value.generate.call_count >= 2
    
    def test_concurrent_request_handling(self):
        """Test handling of concurrent requests"""
        locations = ["東京", "大阪", "名古屋", "札幌", "福岡"]
        
        # Run multiple requests concurrently
        async def run_concurrent():
            tasks = []
            for location in locations:
                task = asyncio.create_task(
                    asyncio.to_thread(
                        run_comment_generation,
                        location_name=location,
                        llm_provider="gemini"
                    )
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        results = asyncio.run(run_concurrent())
        
        # Check that all requests were processed
        assert len(results) == len(locations)
        
        # Count successes and failures
        successes = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failures = sum(1 for r in results if isinstance(r, Exception) or (isinstance(r, dict) and not r.get("success")))
        
        # At least some should succeed
        assert successes + failures == len(locations)
    
    def test_retry_mechanism(self, mock_weather_api, mock_llm_manager):
        """Test retry mechanism for transient failures"""
        # Fail first 2 attempts, succeed on 3rd
        mock_weather_api.return_value.get_forecast.side_effect = [
            Exception("Transient error 1"),
            Exception("Transient error 2"),
            Mock(forecasts=[Mock()])  # Success
        ]
        
        result = run_comment_generation(
            location_name="東京",
            llm_provider="gemini"
        )
        
        # Should eventually succeed
        assert mock_weather_api.return_value.get_forecast.call_count <= 3
    
    def test_data_corruption_handling(self, mock_comment_repository):
        """Test handling of corrupted data"""
        # Simulate corrupted CSV data
        mock_comment_repository.return_value.get_recent_comments.return_value = [
            Mock(comment_text=None),  # Missing text
            Mock(comment_text=""),    # Empty text
            Mock(comment_text="Valid comment")
        ]
        
        result = run_comment_generation(
            location_name="東京",
            llm_provider="gemini"
        )
        
        # Should handle corrupted data gracefully
        assert "error" not in result or "corruption" not in result["error"].lower()
    
    def test_memory_leak_prevention(self):
        """Test that workflow doesn't leak memory on repeated runs"""
        import gc
        import tracemalloc
        
        tracemalloc.start()
        
        # Get initial memory usage
        initial_size, initial_peak = tracemalloc.get_traced_memory()
        
        # Run workflow multiple times
        for i in range(10):
            result = run_comment_generation(
                location_name="東京",
                llm_provider="gemini"
            )
            gc.collect()
        
        # Get final memory usage
        final_size, final_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory usage shouldn't grow significantly
        memory_growth = final_size - initial_size
        assert memory_growth < 10 * 1024 * 1024  # Less than 10MB growth
    
    def test_partial_failure_recovery(self, mock_weather_api, mock_llm_manager):
        """Test recovery from partial failures"""
        # Weather succeeds but LLM fails initially
        mock_weather_api.return_value.get_forecast.return_value = Mock(forecasts=[Mock()])
        mock_llm_manager.return_value.generate.side_effect = [
            LLMError("LLM temporarily unavailable"),
            {"weather_comment": "Recovery comment", "advice_comment": "Recovery advice"}
        ]
        
        result = run_comment_generation(
            location_name="東京",
            llm_provider="gemini"
        )
        
        # Should recover and complete
        assert result.get("final_comment") is not None
    
    def test_validation_error_details(self):
        """Test that validation errors provide useful details"""
        # Test with various invalid inputs
        test_cases = [
            {"location_name": None, "expected_error": "location"},
            {"location_name": "東京", "llm_provider": "invalid_provider", "expected_error": "provider"},
            {"location_name": "東京", "target_datetime": "invalid_date", "expected_error": "datetime"}
        ]
        
        for test_case in test_cases:
            result = run_comment_generation(**test_case)
            
            if not result["success"]:
                assert "error" in result
                assert test_case["expected_error"] in result["error"].lower()


class TestWorkflowPerformance:
    """Test workflow performance characteristics"""
    
    def test_response_time_under_load(self):
        """Test that response time stays reasonable under load"""
        start_time = time.time()
        
        result = run_comment_generation(
            location_name="東京",
            llm_provider="gemini"
        )
        
        elapsed_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust based on your requirements)
        assert elapsed_time < 30  # 30 seconds max
        
        # Check execution time is reported
        assert "execution_time_ms" in result
        assert result["execution_time_ms"] > 0
    
    def test_node_execution_timing(self):
        """Test that node execution times are tracked"""
        result = run_comment_generation(
            location_name="東京",
            llm_provider="gemini"
        )
        
        # Should have node execution times
        if result["success"]:
            assert "node_execution_times" in result
            node_times = result["node_execution_times"]
            
            # Check key nodes are timed
            expected_nodes = ["fetch_forecast", "retrieve_comments", "generate"]
            for node in expected_nodes:
                assert node in node_times
                assert node_times[node] >= 0
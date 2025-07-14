"""Pytest configuration for all tests"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import asyncio

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure async event loop
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Mock environment variables for tests
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        "WXTECH_API_KEY": "test-wxtech-key",
        "OPENAI_API_KEY": "test-openai-key",
        "GEMINI_API_KEY": "test-gemini-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "APP_ENV": "test",
        "LOG_LEVEL": "WARNING",
    }
    with patch.dict(os.environ, env_vars):
        yield

# Mock external services
@pytest.fixture
def mock_wxtech_api():
    """Mock WxTech API client"""
    with patch("src.apis.wxtech_client.WxTechAPIClient") as mock:
        instance = Mock()
        mock.return_value = instance
        
        # Default successful response
        instance.get_forecast.return_value = Mock(
            forecasts=[
                Mock(
                    forecast_datetime="2024-01-01T12:00:00",
                    temperature=20.0,
                    humidity=60,
                    weather_condition="晴れ",
                    wind_speed=5.0,
                    precipitation=0.0
                )
            ]
        )
        yield instance

@pytest.fixture
def mock_llm_manager():
    """Mock LLM Manager"""
    with patch("src.llm.llm_manager.LLMManager") as mock:
        instance = Mock()
        mock.return_value = instance
        
        # Default successful response
        instance.generate.return_value = {
            "weather_comment": "本日は晴れの良い天気です。",
            "advice_comment": "日差しが強いので、日焼け対策をお忘れなく。"
        }
        yield instance

@pytest.fixture
def mock_comment_repository():
    """Mock comment repository"""
    with patch("src.repositories.lazy_comment_repository.LazyCommentRepository") as mock:
        instance = Mock()
        mock.return_value = instance
        
        # Default responses
        instance.get_recent_comments.return_value = []
        instance.get_all_available_comments.return_value = []
        yield instance

# Test data fixtures
@pytest.fixture
def sample_location():
    """Sample location data"""
    return {
        "name": "東京",
        "lat": 35.6762,
        "lon": 139.6503,
        "prefecture": "東京都"
    }

@pytest.fixture
def sample_weather_data():
    """Sample weather data"""
    from src.data.weather_data import WeatherForecast, WeatherCondition
    
    return WeatherForecast(
        location="東京",
        forecast_datetime="2024-01-01T12:00:00",
        temperature=20.0,
        humidity=60,
        weather_condition=WeatherCondition.CLEAR,
        weather_description="晴れ",
        wind_speed=5.0,
        wind_direction="北",
        pressure=1013.0,
        precipitation=0.0,
        pop=0,
        uv_index=5,
        visibility=10.0
    )

@pytest.fixture
def sample_comment_pair():
    """Sample comment pair"""
    from src.data.comment_pair import CommentPair
    
    return CommentPair(
        weather_comment="本日は晴れの良い天気です。",
        advice_comment="日差しが強いので、日焼け対策をお忘れなく。"
    )

# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after tests"""
    yield
    # Clean up any test files created
    test_dirs = ["test_output", "test_cache", "test_data"]
    for dir_name in test_dirs:
        test_dir = project_root / dir_name
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)

# Performance testing fixtures
@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer"""
    import time
    
    class Timer:
        def __init__(self):
            self.times = {}
        
        def start(self, name):
            self.times[name] = time.time()
        
        def stop(self, name):
            if name in self.times:
                elapsed = time.time() - self.times[name]
                del self.times[name]
                return elapsed
            return None
    
    return Timer()

# Playwright configuration for E2E tests
# pytest_plugins = ["pytest_playwright"]  # Commented out - not needed for config tests

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for E2E tests"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "ja-JP",
        "timezone_id": "Asia/Tokyo",
    }
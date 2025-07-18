"""設定テスト用のpytest fixtures"""

import pytest
from src.config.config import reset_config


@pytest.fixture(autouse=True)
def reset_config_singleton():
    """各テストの前後で設定シングルトンをリセット"""
    # テスト前にリセット
    reset_config()
    
    yield
    
    # テスト後にもリセット
    reset_config()
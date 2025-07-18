#!/usr/bin/env python
"""設定読み込みエラーのテスト"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing config import...")
    from src.config.app_settings import get_config
    print("Import successful")
    
    print("Getting config instance...")
    config = get_config()
    print("Config loaded successfully")
    print(f"Weather location: {config.weather.default_location}")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
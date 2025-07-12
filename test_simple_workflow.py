#!/usr/bin/env python3
"""シンプルなワークフローテスト"""

import os
from datetime import datetime
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

# USE_LAZY_CSV_LOADINGを明示的に設定
os.environ["USE_LAZY_CSV_LOADING"] = "true"

from src.workflows.comment_generation_workflow import run_comment_generation


def test_simple():
    """シンプルなテスト"""
    print("=== シンプルワークフローテスト ===\n")
    
    result = run_comment_generation(
        location_name="東京",
        target_datetime=datetime.now(),
        llm_provider="gemini"
    )
    
    print(f"成功: {result['success']}")
    if result["success"]:
        print(f"コメント: {result['final_comment']}")
        metadata = result.get("generation_metadata", {})
        print(f"天気: {metadata.get('weather_condition', '不明')}")
        print(f"気温: {metadata.get('temperature', '不明')}°C")
    else:
        print(f"エラー: {result.get('error', '不明')}")


if __name__ == "__main__":
    test_simple()
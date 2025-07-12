#!/usr/bin/env python3
"""フルワークフローのデバッグ"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# ログレベルをDEBUGに設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 特定のモジュールのログレベルを調整
logging.getLogger("src.utils.validators.temperature_validator").setLevel(logging.DEBUG)
logging.getLogger("src.nodes.select_comment_pair_node").setLevel(logging.DEBUG)

from src.workflows.comment_generation_workflow import run_comment_generation

# 環境変数をロード
load_dotenv()


def test_workflow_debug():
    """ワークフローのデバッグテスト"""
    print("=== ワークフローデバッグテスト ===\n")
    
    # 東京でテスト（26°C）
    print("東京（26°C）のテスト:")
    result = run_comment_generation(
        location_name="東京",
        target_datetime=datetime.now(),
        llm_provider="gemini"
    )
    
    if result["success"]:
        print(f"✅ 成功")
        print(f"コメント: {result['final_comment']}")
        metadata = result.get("generation_metadata", {})
        print(f"天気: {metadata.get('weather_condition', '不明')}")
        print(f"気温: {metadata.get('temperature', '不明')}°C")
    else:
        print(f"❌ エラー: {result.get('error', '不明')}")


if __name__ == "__main__":
    test_workflow_debug()
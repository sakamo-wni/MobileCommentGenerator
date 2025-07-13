#!/usr/bin/env python3
"""
現在の機能と出力を確認するためのテストスクリプト
"""
import sys
import json
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.controllers.comment_generation_controller import CommentGenerationController
    from src.config import LLMProvider
    
    print("=== 現在の動作確認テスト ===")
    print(f"実行時刻: {datetime.now()}")
    
    # コントローラーの初期化
    controller = CommentGenerationController()
    
    # テスト1: 単一地点でのコメント生成
    print("\n1. 単一地点コメント生成テスト:")
    print("地点: 千代田区")
    result = controller.generate_single(
        location="千代田区",
        llm_provider=LLMProvider.GEMINI.value
    )
    
    if result.get("success"):
        print("✓ 成功")
        print(f"生成されたコメント: {result.get('generated_comment', '')[:100]}...")
        print(f"レスポンス時間: {result.get('response_time', 0):.2f}秒")
    else:
        print("✗ 失敗")
        print(f"エラー: {result.get('error', 'Unknown error')}")
    
    # 出力を保存
    output_path = Path("test_output_baseline.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_time": str(datetime.now()),
            "single_generation": result,
            "test_location": "千代田区"
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nベースライン出力を保存しました: {output_path}")
    
except Exception as e:
    print(f"\nエラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
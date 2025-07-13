#!/usr/bin/env python3
"""
シンプルな動作確認テスト
"""
import sys
import json
import os
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # 環境変数の設定
    os.environ['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY', 'test-key')
    
    # 直接ワークフローをインポート
    from src.workflows.comment_generation_workflow import run_comment_generation
    
    print("=== シンプルな動作確認テスト ===")
    print(f"実行時刻: {datetime.now()}")
    
    # テスト1: 単一地点でのコメント生成
    print("\n1. ワークフロー直接実行テスト:")
    print("地点: 東京")
    
    result = run_comment_generation(
        location_name="東京",
        llm_provider="gemini"
    )
    
    print(f"\n結果:")
    print(f"- 成功: {result.get('success', False)}")
    if result.get('success'):
        print(f"- 生成されたコメント: {result.get('generated_comment', '')[:100]}...")
        print(f"- レスポンス時間: {result.get('response_time', 0):.2f}秒")
        print(f"- 天気状態: {result.get('weather_condition', 'N/A')}")
    else:
        print(f"- エラー: {result.get('error', 'Unknown error')}")
    
    # 出力を保存
    output_path = Path("baseline_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_time": str(datetime.now()),
            "result": result,
            "test_location": "千代田区"
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nベースライン出力を保存しました: {output_path}")
    
except Exception as e:
    print(f"\nエラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
"""統一されたワークフローの動作確認"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from datetime import datetime
from src.workflows.comment_generation_workflow import run_comment_generation

def test_unified_workflow():
    """統一されたワークフローの動作確認"""
    print("統一されたワークフロー（並列処理版）の動作確認")
    print("=" * 60)
    
    test_cases = [
        {"location_name": "東京", "llm_provider": "gemini"},
        {"location_name": "大阪", "llm_provider": "gemini", "exclude_previous": True},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nテストケース {i}: {test_case}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            result = run_comment_generation(
                target_datetime=datetime.now(),
                **test_case
            )
            
            elapsed_time = time.time() - start_time
            
            if result.get("success"):
                print(f"✅ 成功!")
                print(f"  実行時間: {elapsed_time:.2f}秒")
                print(f"  コメント: {result.get('final_comment', '')}")
                
                metadata = result.get('generation_metadata', {})
                if metadata:
                    print(f"  並列実行: {metadata.get('parallel_execution', False)}")
                    print(f"  総実行時間: {metadata.get('execution_time_ms', 0)}ms")
            else:
                print(f"❌ 失敗")
                print(f"  エラー: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 例外発生: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("テスト完了")

if __name__ == "__main__":
    test_unified_workflow()
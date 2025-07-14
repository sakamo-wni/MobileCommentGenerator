"""並列処理ワークフローの直接テスト"""

import time
from datetime import datetime
from src.workflows.comment_generation_workflow import run_comment_generation

def test_direct():
    """並列処理ワークフローを直接テスト"""
    print("並列処理ワークフローの直接テスト")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        result = run_comment_generation(
            location_name="東京",
            target_datetime=datetime.now(),
            llm_provider="gemini",
            exclude_previous=False
        )
        
        elapsed_time = time.time() - start_time
        
        if result.get("success"):
            print(f"✅ 成功！")
            print(f"実行時間: {elapsed_time:.2f}秒")
            print(f"コメント: {result.get('final_comment', '')}")
            
            # メタデータを確認
            metadata = result.get('generation_metadata', {})
            print(f"\nメタデータ:")
            print(f"  - 実行時間: {metadata.get('execution_time_ms', 0)}ms")
            print(f"  - 並列処理: {metadata.get('parallel_execution', False)}")
            print(f"  - エラー数: {len(metadata.get('errors', []))}")
        else:
            print(f"❌ 失敗")
            print(f"エラー: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 例外発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct()
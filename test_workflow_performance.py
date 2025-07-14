"""ワークフローのパフォーマンステスト

各ワークフローの動作確認と実行時間を測定します。
"""

import time
import asyncio
from datetime import datetime

# ワークフローのインポート
from src.workflows.comment_generation_workflow import run_comment_generation
from src.workflows.parallel_comment_generation_workflow import run_parallel_comment_generation
from src.workflows.unified_comment_generation_workflow import run_unified_comment_generation


def test_workflow(workflow_func, name, **kwargs):
    """ワークフローをテストして実行時間を測定"""
    print(f"\n{'-' * 50}")
    print(f"Testing: {name}")
    print(f"{'-' * 50}")
    
    start_time = time.time()
    try:
        result = workflow_func(**kwargs)
        elapsed_time = time.time() - start_time
        
        if result.get("success"):
            print(f"✅ 成功: {elapsed_time:.2f}秒")
            print(f"コメント: {result.get('comment', '')[:50]}...")
        else:
            print(f"❌ 失敗: {result.get('error', 'Unknown error')}")
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ エラー: {e}")
        print(f"実行時間: {elapsed_time:.2f}秒")


def main():
    """各ワークフローをテスト"""
    test_params = {
        "location_name": "東京",
        "target_datetime": datetime.now(),
        "llm_provider": "gemini",
        "exclude_previous": False
    }
    
    print("ワークフローのパフォーマンステスト")
    print("=" * 50)
    
    # 1. 通常のワークフロー
    test_workflow(
        run_comment_generation,
        "通常のワークフロー (comment_generation_workflow)",
        **test_params
    )
    
    # 2. 並列処理ワークフロー（デフォルト）
    test_workflow(
        run_parallel_comment_generation,
        "並列処理ワークフロー (parallel_comment_generation_workflow)",
        **test_params,
        use_unified_mode=False
    )
    
    # 3. 統一ワークフロー
    test_workflow(
        run_unified_comment_generation,
        "統一ワークフロー (unified_comment_generation_workflow)",
        **test_params
    )
    
    print(f"\n{'=' * 50}")
    print("テスト完了")


if __name__ == "__main__":
    main()
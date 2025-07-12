"""実際のワークフローのパフォーマンステスト"""

import time
import os

# 環境設定
os.environ["WXTECH_CACHE_TTL"] = "300"  # 5分キャッシュ
os.environ["LLM_PERFORMANCE_MODE"] = "true"

from src.controllers.comment_generation_controller import CommentGenerationController

def test_real_workflow():
    """実際のワークフローをテスト"""
    print("=== 実際のワークフローテスト ===\n")
    
    try:
        controller = CommentGenerationController()
        
        # テストケース
        test_locations = ["東京", "大阪"]
        
        print("初回実行（キャッシュなし）:")
        first_times = []
        for location in test_locations:
            start = time.time()
            try:
                result = controller.generate(location)
                elapsed = time.time() - start
                first_times.append(elapsed)
                print(f"  {location}: {elapsed:.2f}秒")
                if result:
                    print(f"    コメント生成成功: {result.comment[:50]}...")
            except Exception as e:
                print(f"  {location}: エラー - {type(e).__name__}: {str(e)}")
        
        print(f"\n初回平均: {sum(first_times)/len(first_times):.2f}秒")
        
        # 2回目（キャッシュあり）
        print("\n2回目実行（キャッシュあり）:")
        second_times = []
        for location in test_locations:
            start = time.time()
            try:
                result = controller.generate(location)
                elapsed = time.time() - start
                second_times.append(elapsed)
                print(f"  {location}: {elapsed:.2f}秒")
            except Exception as e:
                print(f"  {location}: エラー - {type(e).__name__}: {str(e)}")
        
        if second_times:
            print(f"\n2回目平均: {sum(second_times)/len(second_times):.2f}秒")
            
            if first_times and second_times:
                improvement = (sum(first_times) - sum(second_times)) / sum(first_times) * 100
                print(f"\n改善率: {improvement:.1f}%")
        
    except Exception as e:
        print(f"初期化エラー: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_workflow()
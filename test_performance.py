"""パフォーマンステストスクリプト"""

import time
import os
from src.controllers.comment_generation_controller import CommentGenerationController

def test_performance():
    """実際の処理のパフォーマンスを測定"""
    # 2地点で3回ずつテスト
    locations = ["東京", "大阪"]
    
    print("=== パフォーマンステスト ===\n")
    
    controller = CommentGenerationController()
    
    # ウォームアップ
    print("ウォームアップ中...")
    controller.generate("稚内")
    
    # 実際の測定
    times = []
    for i in range(3):
        print(f"\nラウンド {i+1}/3:")
        
        round_start = time.time()
        for location in locations:
            start_time = time.time()
            try:
                result = controller.generate(location)
                elapsed = time.time() - start_time
                print(f"  {location}: {elapsed:.2f}秒")
            except Exception as e:
                print(f"  {location}: エラー - {str(e)}")
        
        round_time = time.time() - round_start
        times.append(round_time)
        print(f"  合計: {round_time:.2f}秒")
    
    avg_time = sum(times) / len(times)
    print(f"\n平均実行時間: {avg_time:.2f}秒")
    
    return avg_time

if __name__ == "__main__":
    test_performance()
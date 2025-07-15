#!/usr/bin/env python3
"""簡易パフォーマンステスト"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from src.workflows.unified_comment_generation_workflow import create_unified_comment_generation_workflow
from src.data.comment_generation_state import CommentGenerationState

def test_performance():
    """統合ワークフローのパフォーマンスを測定"""
    
    print("統合ワークフロー パフォーマンステスト")
    print("=" * 50)
    
    # テスト地点
    locations = ["東京", "大阪", "名古屋"]
    
    workflow = create_unified_comment_generation_workflow()
    
    for location in locations:
        print(f"\n{location}のテスト:")
        
        # 3回実行して平均を取る
        times = []
        for i in range(3):
            start_time = time.time()
            
            try:
                from datetime import datetime
                initial_state = CommentGenerationState(
                    location_name=location,
                    target_datetime=datetime.now(),
                    llm_provider="gemini"
                )
                result = workflow.invoke(initial_state)
                
                elapsed = time.time() - start_time
                times.append(elapsed)
                
                if hasattr(result, 'generated_comment') and result.generated_comment:
                    print(f"  実行{i+1}: {elapsed:.2f}秒 - {result.generated_comment}")
                else:
                    print(f"  実行{i+1}: {elapsed:.2f}秒 - エラー")
                    
            except Exception as e:
                print(f"  実行{i+1}: エラー - {str(e)}")
                
            # API制限回避のため少し待つ
            time.sleep(1)
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"  平均実行時間: {avg_time:.2f}秒")
    
    print("\n" + "=" * 50)
    print("テスト完了")

if __name__ == "__main__":
    test_performance()
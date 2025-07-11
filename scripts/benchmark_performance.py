#!/usr/bin/env python3
"""
パフォーマンスベンチマークスクリプト

実行時間短縮の効果を測定するためのベンチマークツール
"""

import os
import sys
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.comment_generation_controller import CommentGenerationController
from src.config import get_config


def run_benchmark(
    locations: List[str], 
    llm_provider: str = "openai",
    iterations: int = 3
) -> Dict[str, Any]:
    """ベンチマークを実行
    
    Args:
        locations: テスト対象の地点リスト
        llm_provider: 使用するLLMプロバイダー
        iterations: 実行回数
        
    Returns:
        ベンチマーク結果
    """
    controller = CommentGenerationController()
    execution_times = []
    
    print(f"\n=== ベンチマーク開始 ===")
    print(f"地点数: {len(locations)}")
    print(f"LLMプロバイダー: {llm_provider}")
    print(f"実行回数: {iterations}")
    print(f"並列度: {os.getenv('MAX_LLM_WORKERS', '3')}")
    print(f"パフォーマンスモード: {os.getenv('LLM_PERFORMANCE_MODE', 'false')}")
    print(f"評価リトライ回数: {os.getenv('MAX_EVALUATION_RETRIES', '3')}")
    
    for i in range(iterations):
        print(f"\n--- 実行 {i + 1}/{iterations} ---")
        start_time = time.time()
        
        try:
            result = controller.generate_comments_batch(
                locations=locations,
                llm_provider=llm_provider
            )
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            success_count = sum(1 for r in result['results'] if r['success'])
            print(f"実行時間: {execution_time:.2f}秒")
            print(f"成功数: {success_count}/{len(locations)}")
            
        except Exception as e:
            print(f"エラー発生: {e}")
            continue
    
    if execution_times:
        avg_time = statistics.mean(execution_times)
        std_dev = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        
        return {
            "avg_execution_time": avg_time,
            "std_deviation": std_dev,
            "min_time": min(execution_times),
            "max_time": max(execution_times),
            "all_times": execution_times,
            "per_location_avg": avg_time / len(locations)
        }
    else:
        return {"error": "ベンチマークが正常に実行されませんでした"}


def main():
    """メイン実行関数"""
    # テスト用の地点リスト
    test_locations = [
        "東京",
        "大阪", 
        "名古屋",
        "札幌",
        "福岡"
    ]
    
    print("\n" + "=" * 60)
    print("天気コメント生成 パフォーマンスベンチマーク")
    print("=" * 60)
    
    # デフォルト設定でのベンチマーク
    print("\n### デフォルト設定でのベンチマーク ###")
    default_result = run_benchmark(test_locations)
    
    # パフォーマンスモードでのベンチマーク
    print("\n### パフォーマンスモードでのベンチマーク ###")
    os.environ["LLM_PERFORMANCE_MODE"] = "true"
    os.environ["MAX_LLM_WORKERS"] = "8"
    os.environ["MAX_EVALUATION_RETRIES"] = "2"
    
    performance_result = run_benchmark(test_locations)
    
    # 結果のサマリー
    print("\n" + "=" * 60)
    print("ベンチマーク結果サマリー")
    print("=" * 60)
    
    if "error" not in default_result:
        print(f"\nデフォルト設定:")
        print(f"  平均実行時間: {default_result['avg_execution_time']:.2f}秒")
        print(f"  1地点あたり: {default_result['per_location_avg']:.2f}秒")
        print(f"  標準偏差: {default_result['std_deviation']:.2f}秒")
    
    if "error" not in performance_result:
        print(f"\nパフォーマンスモード:")
        print(f"  平均実行時間: {performance_result['avg_execution_time']:.2f}秒")
        print(f"  1地点あたり: {performance_result['per_location_avg']:.2f}秒")
        print(f"  標準偏差: {performance_result['std_deviation']:.2f}秒")
        
        if "error" not in default_result:
            improvement = (1 - performance_result['avg_execution_time'] / default_result['avg_execution_time']) * 100
            print(f"\n改善率: {improvement:.1f}%")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
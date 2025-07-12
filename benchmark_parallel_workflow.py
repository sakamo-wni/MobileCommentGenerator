#!/usr/bin/env python3
"""並列ワークフローのパフォーマンスベンチマーク

通常のワークフローと並列ワークフローの実行時間を比較します。
"""

import time
from datetime import datetime
import statistics
from src.workflows.comment_generation_workflow import run_comment_generation
from src.workflows.parallel_comment_generation_workflow import run_parallel_comment_generation


def measure_execution_time(func, *args, **kwargs):
    """関数の実行時間を測定"""
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    return (end - start) * 1000, result  # ミリ秒で返す


def run_benchmark(location_name="東京", runs=5):
    """ベンチマークを実行"""
    print(f"=== 並列ワークフローベンチマーク ===")
    print(f"地点: {location_name}")
    print(f"実行回数: {runs}")
    print()
    
    # 通常ワークフローの測定
    normal_times = []
    print("通常ワークフロー実行中...")
    for i in range(runs):
        time_ms, result = measure_execution_time(
            run_comment_generation,
            location_name=location_name,
            target_datetime=datetime.now(),
            llm_provider="gemini"  # Geminiを使用
        )
        if result["success"]:
            normal_times.append(time_ms)
            print(f"  Run {i+1}: {time_ms:.2f}ms")
        else:
            print(f"  Run {i+1}: エラー - {result.get('error', '不明')}")
    
    # 並列ワークフローの測定
    parallel_times = []
    print("\n並列ワークフロー実行中...")
    for i in range(runs):
        time_ms, result = measure_execution_time(
            run_parallel_comment_generation,
            location_name=location_name,
            target_datetime=datetime.now(),
            llm_provider="gemini"  # Geminiを使用
        )
        if result["success"]:
            parallel_times.append(time_ms)
            print(f"  Run {i+1}: {time_ms:.2f}ms")
        else:
            print(f"  Run {i+1}: エラー - {result.get('error', '不明')}")
    
    # 結果の集計
    if normal_times and parallel_times:
        print("\n=== 結果サマリー ===")
        print(f"\n通常ワークフロー:")
        print(f"  平均: {statistics.mean(normal_times):.2f}ms")
        print(f"  中央値: {statistics.median(normal_times):.2f}ms")
        print(f"  最小: {min(normal_times):.2f}ms")
        print(f"  最大: {max(normal_times):.2f}ms")
        
        print(f"\n並列ワークフロー:")
        print(f"  平均: {statistics.mean(parallel_times):.2f}ms")
        print(f"  中央値: {statistics.median(parallel_times):.2f}ms")
        print(f"  最小: {min(parallel_times):.2f}ms")
        print(f"  最大: {max(parallel_times):.2f}ms")
        
        # 改善率の計算
        avg_normal = statistics.mean(normal_times)
        avg_parallel = statistics.mean(parallel_times)
        improvement = ((avg_normal - avg_parallel) / avg_normal) * 100
        
        print(f"\n改善率: {improvement:.1f}%")
        print(f"高速化倍率: {avg_normal / avg_parallel:.2f}x")
        
        # ノード実行時間の詳細（最後の実行から）
        if result.get("node_execution_times"):
            print(f"\n=== ノード実行時間の詳細（並列ワークフロー） ===")
            for node, time_ms in result["node_execution_times"].items():
                print(f"  {node}: {time_ms:.2f}ms")


def run_detailed_comparison():
    """詳細な比較分析"""
    print("\n=== 詳細な比較分析 ===\n")
    
    # 1回だけ実行して内部の詳細を確認
    print("通常ワークフローの詳細:")
    _, normal_result = measure_execution_time(
        run_comment_generation,
        location_name="大阪",
        target_datetime=datetime.now(),
        llm_provider="gemini"
    )
    
    if normal_result.get("generation_metadata", {}).get("node_execution_times"):
        for node, time_ms in normal_result["generation_metadata"]["node_execution_times"].items():
            print(f"  {node}: {time_ms:.2f}ms")
    
    print("\n並列ワークフローの詳細:")
    _, parallel_result = measure_execution_time(
        run_parallel_comment_generation,
        location_name="大阪",
        target_datetime=datetime.now(),
        llm_provider="gemini"
    )
    
    if parallel_result.get("node_execution_times"):
        for node, time_ms in parallel_result["node_execution_times"].items():
            print(f"  {node}: {time_ms:.2f}ms")


if __name__ == "__main__":
    # 基本ベンチマーク
    run_benchmark("東京", runs=2)  # 実行回数を減らす
    
    # 詳細比較
    run_detailed_comparison()
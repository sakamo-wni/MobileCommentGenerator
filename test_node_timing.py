#!/usr/bin/env python3
"""各ノードの実行時間を測定"""

import time
from datetime import datetime
from src.data.comment_generation_state import CommentGenerationState
from src.nodes.input_node import input_node
from src.nodes.weather_forecast_node import fetch_weather_forecast_node
from src.nodes.retrieve_past_comments_node import retrieve_past_comments_node


def measure_node(node_func, state):
    """ノードの実行時間を測定"""
    start = time.time()
    result = node_func(state)
    end = time.time()
    return (end - start) * 1000, result


def main():
    print("=== ノード実行時間測定 ===\n")
    
    # 初期状態の作成
    initial_state = CommentGenerationState(
        location_name="東京",
        target_datetime=datetime.now(),
        llm_provider="gemini"
    )
    
    # input_nodeの実行
    print("1. input_node実行中...")
    time_ms, state = measure_node(input_node, initial_state)
    print(f"   実行時間: {time_ms:.2f}ms")
    
    # 天気予報取得の実行
    print("\n2. fetch_weather_forecast_node実行中...")
    time_ms, state = measure_node(fetch_weather_forecast_node, state)
    print(f"   実行時間: {time_ms:.2f}ms")
    if state.weather_data:
        print(f"   天気: {state.weather_data.weather_description}")
        print(f"   気温: {state.weather_data.temperature}°C")
    
    # 天気データをNoneにしてコメント取得をテスト（並列実行をシミュレート）
    state_copy = CommentGenerationState(
        location_name=state.location_name,
        target_datetime=state.target_datetime,
        llm_provider=state.llm_provider,
        weather_data=None  # 並列実行時のシミュレーション
    )
    
    print("\n3. retrieve_past_comments_node実行中（weather_data=None）...")
    time_ms, result = measure_node(retrieve_past_comments_node, state_copy)
    print(f"   実行時間: {time_ms:.2f}ms")
    print(f"   取得コメント数: {len(result.past_comments)}")
    
    # 通常の順次実行
    print("\n4. retrieve_past_comments_node実行中（weather_dataあり）...")
    time_ms, result = measure_node(retrieve_past_comments_node, state)
    print(f"   実行時間: {time_ms:.2f}ms")
    print(f"   取得コメント数: {len(result.past_comments)}")
    
    # メタデータの確認
    if hasattr(result, 'generation_metadata') and result.generation_metadata:
        if 'comment_retrieval_metadata' in result.generation_metadata:
            metadata = result.generation_metadata['comment_retrieval_metadata']
            print(f"   メタデータ: {metadata}")


if __name__ == "__main__":
    main()
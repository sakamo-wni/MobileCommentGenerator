"""ワークフローの修正確認テスト"""

import os
import logging
from datetime import datetime
from src.data.comment_generation_state import CommentGenerationState
from src.data.weather_data import WeatherForecast
from src.nodes.retrieve_past_comments_node import retrieve_past_comments_node

# ログレベルを設定
logging.basicConfig(level=logging.INFO)

def test_workflow():
    """ワークフローのテスト"""
    print("=== ワークフローテスト ===\n")
    
    # 環境変数を確認
    print(f"USE_LAZY_CSV_LOADING: {os.environ.get('USE_LAZY_CSV_LOADING', 'not set')}")
    
    # 状態を作成
    state = CommentGenerationState(
        location_name="大阪",
        target_datetime=datetime.now()
    )
    
    print(f"state.use_lazy_loading: {state.use_lazy_loading}")
    
    # 天気データを設定（正しい初期化方法）
    from src.data.weather_data import WeatherCondition, WindDirection
    state.weather_data = WeatherForecast(
        location="大阪",
        datetime=datetime.now(),
        temperature=20.0,
        weather_code="100",
        weather_condition=WeatherCondition.CLEAR,
        weather_description="晴れ",
        precipitation=0.0,
        humidity=60,
        wind_speed=3.0,
        wind_direction=WindDirection.S,
        wind_direction_degrees=180
    )
    
    # ノードを実行
    print("\nretrieve_past_comments_nodeを実行中...")
    result_state = retrieve_past_comments_node(state)
    
    print(f"\n結果:")
    print(f"  過去コメント数: {len(result_state.past_comments)}")
    
    if result_state.past_comments:
        print(f"\n  最初の5件:")
        for i, comment in enumerate(result_state.past_comments[:5]):
            print(f"    {i+1}. {comment.comment_text[:30]}... ({comment.comment_type.value})")
    else:
        print("  コメントが取得されませんでした")
        
    # メタデータを確認
    metadata = result_state.generation_metadata.get("comment_retrieval_metadata", {})
    print(f"\n  メタデータ:")
    print(f"    retrieval_successful: {metadata.get('retrieval_successful')}")
    print(f"    total_comments: {metadata.get('total_comments')}")
    if 'error' in metadata:
        print(f"    error: {metadata.get('error')}")

if __name__ == "__main__":
    test_workflow()
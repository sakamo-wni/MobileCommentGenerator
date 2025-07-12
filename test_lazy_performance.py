"""遅延読み込みのパフォーマンステスト"""

import time
import os
from src.repositories.local_comment_repository import LocalCommentRepository
from src.repositories.lazy_comment_repository import LazyCommentRepository

def test_repository_performance():
    """リポジトリのパフォーマンス比較"""
    print("=== CSVリポジトリのパフォーマンス比較 ===\n")
    
    # 1. 通常のリポジトリ（全ファイル読み込み）
    print("1. 通常のリポジトリ（初期化時に全ファイル読み込み）:")
    start = time.time()
    normal_repo = LocalCommentRepository(use_index=False)
    normal_init_time = time.time() - start
    print(f"  初期化時間: {normal_init_time:.3f}秒")
    
    # コメント取得
    start = time.time()
    spring_comments = normal_repo.get_comments_by_season(["春"])
    normal_fetch_time = time.time() - start
    print(f"  春データ取得: {normal_fetch_time:.3f}秒 ({len(spring_comments)}件)")
    
    # 2. 遅延読み込みリポジトリ
    print("\n2. 遅延読み込みリポジトリ:")
    start = time.time()
    lazy_repo = LazyCommentRepository()
    lazy_init_time = time.time() - start
    print(f"  初期化時間: {lazy_init_time:.3f}秒")
    
    # 初回の春データ取得
    start = time.time()
    spring_comments_lazy = lazy_repo.get_comments_by_season("春")
    lazy_first_fetch = time.time() - start
    print(f"  春データ取得（初回）: {lazy_first_fetch:.3f}秒 ({len(spring_comments_lazy)}件)")
    
    # 2回目の春データ取得（キャッシュから）
    start = time.time()
    spring_comments_cached = lazy_repo.get_comments_by_season("春")
    lazy_cached_fetch = time.time() - start
    print(f"  春データ取得（キャッシュ）: {lazy_cached_fetch:.3f}秒")
    
    # 統計情報
    stats = lazy_repo.get_statistics()
    print(f"\n  読み込み済みファイル数: {stats['loaded_files']}")
    print(f"  キャッシュヒット率: {stats['cache_stats']['hit_rate']:.1%}")
    
    # 改善率
    print("\n3. 改善率:")
    init_improvement = (normal_init_time - lazy_init_time) / normal_init_time * 100
    print(f"  初期化時間の改善: {init_improvement:.1f}%")
    
    # メモリ使用量の推定（読み込まれたファイル数から）
    total_files = len(["春", "夏", "秋", "冬", "梅雨", "台風"]) * 2  # 各季節×2タイプ
    memory_saving = (1 - stats['loaded_files'] / total_files) * 100
    print(f"  メモリ節約（推定）: {memory_saving:.1f}%")

def test_workflow_integration():
    """ワークフローでの動作確認"""
    print("\n\n=== ワークフロー統合テスト ===\n")
    
    # 環境変数を設定
    os.environ["USE_LAZY_CSV_LOADING"] = "true"
    
    from src.nodes.retrieve_past_comments_node import retrieve_past_comments_node
    from src.data.comment_generation_state import CommentGenerationState
    from src.data.weather_data import WeatherForecast
    from datetime import datetime
    
    # テスト用の状態を作成
    state = CommentGenerationState(
        location_name="東京",
        target_datetime=datetime.now()
    )
    state.weather_data = WeatherForecast(
        datetime=datetime.now(),
        weather="晴れ",
        temperature=20.0,
        weather_code="100"
    )
    
    # ノードを実行
    start = time.time()
    result = retrieve_past_comments_node(state)
    elapsed = time.time() - start
    
    print(f"過去コメント取得時間: {elapsed:.3f}秒")
    print(f"取得されたコメント数: {len(result.get('past_comments', []))}")

if __name__ == "__main__":
    test_repository_performance()
    test_workflow_integration()
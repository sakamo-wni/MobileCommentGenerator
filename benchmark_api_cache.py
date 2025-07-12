"""APIキャッシュ機能のベンチマークスクリプト"""

import time
import os
from unittest.mock import Mock, patch

from src.apis.wxtech.client import WxTechAPIClient


def create_mock_response():
    """モックレスポンスを作成"""
    return {
        "wxdata": [{
            "srf": [
                {
                    "jst": f"2024-01-01 {i:02d}:00:00",
                    "temp": 20.0 + i * 0.5,
                    "rh": 60,
                    "prec": 0.0,
                    "wdir": 180,
                    "wspd": 5.0,
                    "pres": 1013.0,
                    "weather": "晴れ"
                }
                for i in range(24)
            ],
            "mrf": []
        }]
    }


@patch('src.apis.wxtech.client.WxTechAPI')
def benchmark_cache_performance(mock_api_class):
    """キャッシュのパフォーマンスをベンチマーク"""
    # モックの設定
    mock_api = Mock()
    mock_api_class.return_value = mock_api
    
    # API呼び出しに遅延を追加（実際のAPIをシミュレート）
    def slow_api_call(*args, **kwargs):
        time.sleep(0.1)  # 100ms の遅延
        return create_mock_response()
    
    mock_api.make_request.side_effect = slow_api_call
    
    print("=== APIキャッシュベンチマーク ===\n")
    
    # キャッシュ有効のクライアント
    print("1. キャッシュ有効の場合:")
    client_with_cache = WxTechAPIClient("test_key", enable_cache=True)
    
    # 同じ座標で10回リクエスト
    locations = [(35.0, 139.0), (36.0, 140.0), (37.0, 141.0)]
    
    start_time = time.time()
    for _ in range(3):
        for lat, lon in locations:
            client_with_cache.get_forecast(lat, lon, forecast_hours=24)
    
    with_cache_time = time.time() - start_time
    cache_stats = client_with_cache.get_cache_stats()
    
    print(f"  実行時間: {with_cache_time:.3f}秒")
    print(f"  API呼び出し回数: {mock_api.make_request.call_count}")
    print(f"  キャッシュヒット率: {cache_stats['hit_rate']:.1%}")
    print(f"  キャッシュヒット数: {cache_stats['hits']}")
    print(f"  キャッシュミス数: {cache_stats['misses']}")
    
    # モックをリセット
    mock_api.make_request.reset_mock()
    
    # キャッシュ無効のクライアント
    print("\n2. キャッシュ無効の場合:")
    client_without_cache = WxTechAPIClient("test_key", enable_cache=False)
    
    start_time = time.time()
    for _ in range(3):
        for lat, lon in locations:
            client_without_cache.get_forecast(lat, lon, forecast_hours=24)
    
    without_cache_time = time.time() - start_time
    
    print(f"  実行時間: {without_cache_time:.3f}秒")
    print(f"  API呼び出し回数: {mock_api.make_request.call_count}")
    
    # 改善率の計算
    print("\n3. パフォーマンス改善:")
    improvement = (without_cache_time - with_cache_time) / without_cache_time * 100
    speedup = without_cache_time / with_cache_time
    
    print(f"  実行時間削減: {improvement:.1f}%")
    print(f"  高速化倍率: {speedup:.1f}x")
    print(f"  節約されたAPI呼び出し: {9 - 3} 回")
    
    # 実際のキャッシュサイズ
    print("\n4. メモリ使用量:")
    print(f"  キャッシュサイズ: {cache_stats['size']} エントリ")
    
    return {
        "with_cache_time": with_cache_time,
        "without_cache_time": without_cache_time,
        "improvement": improvement,
        "speedup": speedup
    }


@patch('src.apis.wxtech.client.WxTechAPI')
def benchmark_ttl_behavior(mock_api_class):
    """TTL動作のベンチマーク"""
    mock_api = Mock()
    mock_api_class.return_value = mock_api
    mock_api.make_request.return_value = create_mock_response()
    
    print("\n=== TTL動作のテスト ===\n")
    
    # 短いTTLでテスト（環境変数で設定）
    os.environ["WXTECH_CACHE_TTL"] = "2"  # 2秒のTTL
    
    client = WxTechAPIClient("test_key", enable_cache=True)
    
    # 初回リクエスト
    print("1. 初回リクエスト")
    client.get_forecast(35.0, 139.0)
    print(f"  API呼び出し回数: {mock_api.make_request.call_count}")
    
    # 1秒後（キャッシュ有効）
    time.sleep(1)
    print("\n2. 1秒後のリクエスト（キャッシュ有効）")
    client.get_forecast(35.0, 139.0)
    print(f"  API呼び出し回数: {mock_api.make_request.call_count}")
    
    # 3秒後（キャッシュ期限切れ）
    time.sleep(2)
    print("\n3. 3秒後のリクエスト（キャッシュ期限切れ）")
    client.get_forecast(35.0, 139.0)
    print(f"  API呼び出し回数: {mock_api.make_request.call_count}")
    
    # 環境変数をクリア
    del os.environ["WXTECH_CACHE_TTL"]


def main():
    """メイン処理"""
    print("APIキャッシュ機能のベンチマーク")
    print("=" * 50)
    
    # キャッシュパフォーマンスのベンチマーク
    results = benchmark_cache_performance()
    
    # TTL動作のベンチマーク
    benchmark_ttl_behavior()
    
    print("\n完了！")
    
    return results


if __name__ == "__main__":
    main()
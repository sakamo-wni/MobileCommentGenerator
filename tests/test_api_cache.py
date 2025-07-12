"""APIキャッシュ機能のテスト"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime

from src.utils.cache import TTLCache, generate_cache_key, cached_method
from src.apis.wxtech.client import WxTechAPIClient
from src.data.weather_data import WeatherForecast, WeatherForecastCollection


class TestTTLCache:
    """TTLCacheのテスト"""
    
    def test_basic_get_set(self):
        """基本的なget/set操作のテスト"""
        cache = TTLCache(default_ttl=60)
        
        # データをセット
        cache.set("key1", "value1")
        
        # データを取得
        assert cache.get("key1") == "value1"
        
        # 存在しないキー
        assert cache.get("key2") is None
    
    def test_ttl_expiration(self):
        """TTL期限切れのテスト"""
        cache = TTLCache(default_ttl=1)  # 1秒のTTL
        
        # データをセット
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # 1.1秒待機
        time.sleep(1.1)
        
        # 期限切れでNoneが返る
        assert cache.get("key1") is None
    
    def test_custom_ttl(self):
        """カスタムTTLのテスト"""
        cache = TTLCache(default_ttl=60)
        
        # カスタムTTL（0.5秒）でセット
        cache.set("key1", "value1", ttl=0.5)
        assert cache.get("key1") == "value1"
        
        # 0.6秒待機
        time.sleep(0.6)
        
        # 期限切れ
        assert cache.get("key1") is None
    
    def test_cache_stats(self):
        """キャッシュ統計のテスト"""
        cache = TTLCache()
        
        # 初期状態
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # データをセット
        cache.set("key1", "value1")
        
        # ヒット
        cache.get("key1")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
        
        # ミス
        cache.get("key2")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
    
    def test_cleanup_expired(self):
        """期限切れエントリのクリーンアップテスト"""
        cache = TTLCache(default_ttl=0.5)
        
        # 複数のエントリを追加
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3", ttl=2)  # 長いTTL
        
        # 0.6秒待機
        time.sleep(0.6)
        
        # クリーンアップ実行
        cache.cleanup_expired()
        
        # key1とkey2は削除され、key3は残る
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"


class TestCacheKeyGeneration:
    """キャッシュキー生成のテスト"""
    
    def test_generate_cache_key(self):
        """キャッシュキー生成のテスト"""
        # 同じ引数なら同じキー
        key1 = generate_cache_key(1, 2, 3, foo="bar")
        key2 = generate_cache_key(1, 2, 3, foo="bar")
        assert key1 == key2
        
        # 異なる引数なら異なるキー
        key3 = generate_cache_key(1, 2, 4, foo="bar")
        assert key1 != key3
        
        # 順序が異なってもキーワード引数は同じ
        key4 = generate_cache_key(1, 2, 3, foo="bar", baz="qux")
        key5 = generate_cache_key(1, 2, 3, baz="qux", foo="bar")
        assert key4 == key5


class TestCachedMethod:
    """cached_methodデコレータのテスト"""
    
    def test_cached_method_decorator(self):
        """デコレータの基本動作テスト"""
        
        class TestClass:
            def __init__(self):
                self._cache = TTLCache()
                self.call_count = 0
            
            @cached_method()
            def expensive_method(self, x, y):
                self.call_count += 1
                return x + y
        
        obj = TestClass()
        
        # 初回呼び出し
        result1 = obj.expensive_method(1, 2)
        assert result1 == 3
        assert obj.call_count == 1
        
        # 2回目はキャッシュから
        result2 = obj.expensive_method(1, 2)
        assert result2 == 3
        assert obj.call_count == 1  # 呼び出し回数は増えない
        
        # 異なる引数なら再実行
        result3 = obj.expensive_method(2, 3)
        assert result3 == 5
        assert obj.call_count == 2


class TestWxTechAPIClientCache:
    """WxTechAPIClientのキャッシュ機能テスト"""
    
    @patch('src.apis.wxtech.client.WxTechAPI')
    def test_get_forecast_caching(self, mock_api_class):
        """get_forecastメソッドのキャッシュテスト"""
        # モックの設定
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        # モックレスポンスを設定
        mock_response = {
            "wxdata": [{
                "srf": [{
                    "jst": "2024-01-01 12:00:00",
                    "temp": 20.0,
                    "rh": 60,
                    "prec": 0.0,
                    "wdir": 180,
                    "wspd": 5.0,
                    "pres": 1013.0,
                    "weather": "晴れ"
                }],
                "mrf": []
            }]
        }
        mock_api.make_request.return_value = mock_response
        
        # クライアントを作成（キャッシュ有効）
        client = WxTechAPIClient("test_key", enable_cache=True)
        
        # 初回呼び出し
        result1 = client.get_forecast(35.0, 139.0, forecast_hours=24)
        assert isinstance(result1, WeatherForecastCollection)
        assert mock_api.make_request.call_count == 1
        
        # 2回目はキャッシュから（APIは呼ばれない）
        result2 = client.get_forecast(35.0, 139.0, forecast_hours=24)
        assert isinstance(result2, WeatherForecastCollection)
        assert mock_api.make_request.call_count == 1  # 呼び出し回数は増えない
        
        # 異なるパラメータなら再度API呼び出し
        result3 = client.get_forecast(36.0, 140.0, forecast_hours=24)
        assert isinstance(result3, WeatherForecastCollection)
        assert mock_api.make_request.call_count == 2
    
    @patch('src.apis.wxtech.client.WxTechAPI')
    def test_cache_disabled(self, mock_api_class):
        """キャッシュ無効時のテスト"""
        # モックの設定
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_api.make_request.return_value = {"wxdata": [{"srf": [], "mrf": []}]}
        
        # クライアントを作成（キャッシュ無効）
        client = WxTechAPIClient("test_key", enable_cache=False)
        
        # 同じパラメータで2回呼び出し
        client.get_forecast(35.0, 139.0)
        client.get_forecast(35.0, 139.0)
        
        # キャッシュが無効なので2回APIが呼ばれる
        assert mock_api.make_request.call_count == 2
    
    @patch('src.apis.wxtech.client.WxTechAPI')
    def test_cache_stats(self, mock_api_class):
        """キャッシュ統計のテスト"""
        # モックの設定
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_api.make_request.return_value = {"wxdata": [{"srf": [], "mrf": []}]}
        
        # クライアントを作成
        client = WxTechAPIClient("test_key", enable_cache=True)
        
        # 初期状態
        stats = client.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # API呼び出し
        client.get_forecast(35.0, 139.0)
        client.get_forecast(35.0, 139.0)  # キャッシュヒット
        client.get_forecast(36.0, 140.0)  # キャッシュミス
        
        # 統計確認
        stats = client.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 1/3
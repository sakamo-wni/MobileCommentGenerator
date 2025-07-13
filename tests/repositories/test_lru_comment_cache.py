"""LRUCommentCacheのテスト"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.repositories.lru_comment_cache import LRUCommentCache
from src.data.past_comment import PastComment, CommentType


class TestLRUCommentCache:
    """LRUCommentCacheのテストクラス"""
    
    @pytest.fixture
    def cache(self):
        """テスト用のキャッシュインスタンス"""
        return LRUCommentCache(max_size=3, cache_ttl_minutes=60, max_memory_mb=1)
    
    @pytest.fixture
    def sample_comments(self):
        """テスト用のサンプルコメント"""
        return [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="晴れの日です",
                comment_type=CommentType.WEATHER_COMMENT,
                raw_data={"season": "春", "count": 10}
            ),
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="雨",
                comment_text="傘を持って行きましょう",
                comment_type=CommentType.ADVICE,
                raw_data={"season": "梅雨", "count": 5}
            )
        ]
    
    def test_basic_get_and_set(self, cache, sample_comments):
        """基本的なget/set操作のテスト"""
        # 初期状態では何も取得できない
        assert cache.get("key1") is None
        
        # データを設定
        cache.set("key1", sample_comments)
        
        # データを取得できる
        result = cache.get("key1")
        assert result == sample_comments
    
    def test_lru_eviction(self, cache, sample_comments):
        """LRU削除のテスト"""
        # 最大サイズ3のキャッシュに4つのエントリを追加
        cache.set("key1", [sample_comments[0]])
        cache.set("key2", [sample_comments[0]])
        cache.set("key3", [sample_comments[0]])
        
        # key1にアクセス（最近使用されたことになる）
        cache.get("key1")
        
        # 4つ目を追加（key2が削除されるはず）
        cache.set("key4", [sample_comments[0]])
        
        # key2は削除されている
        assert cache.get("key2") is None
        # key1, key3, key4は残っている
        assert cache.get("key1") is not None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None
    
    def test_ttl_expiration(self, cache, sample_comments):
        """TTL期限切れのテスト"""
        # 有効期限1分のキャッシュを作成
        short_cache = LRUCommentCache(max_size=10, cache_ttl_minutes=1)
        
        # データを設定
        short_cache.set("key1", sample_comments)
        assert short_cache.get("key1") is not None
        
        # タイムスタンプを手動で過去に設定（テスト用）
        key = "key1"
        if key in short_cache._cache:
            comments, _ = short_cache._cache[key]
            expired_time = datetime.now() - timedelta(minutes=2)
            short_cache._cache[key] = (comments, expired_time)
        
        # 期限切れのデータは取得できない
        assert short_cache.get("key1") is None
    
    def test_hit_rate_calculation(self, cache, sample_comments):
        """ヒット率計算のテスト"""
        # 初期状態
        assert cache.get_hit_rate() == 0.0
        
        # キャッシュミス
        cache.get("key1")  # miss
        assert cache.get_hit_rate() == 0.0
        
        # データ設定後のヒット
        cache.set("key1", sample_comments)
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        
        # 3回中2回ヒット = 66.7%
        assert cache.get_hit_rate() == pytest.approx(2/3, rel=0.01)
    
    def test_memory_limit(self, cache):
        """メモリ制限のテスト"""
        # 大きなコメントデータを作成
        large_comment = PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="晴れ",
            comment_text="x" * 10000,  # 10KB程度のテキスト
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"large_data": "y" * 10000}
        )
        
        # メモリ制限1MBのキャッシュに大量のデータを追加
        for i in range(100):
            cache.set(f"key{i}", [large_comment] * 10)
        
        # キャッシュサイズが制限されていることを確認
        stats = cache.get_stats()
        assert stats['memory_usage_mb'] <= 1.0
    
    def test_cleanup_expired(self, cache, sample_comments):
        """期限切れエントリのクリーンアップテスト"""
        # 複数のエントリを追加
        cache.set("key1", sample_comments)
        cache.set("key2", sample_comments)
        cache.set("key3", sample_comments)
        
        # 一部を期限切れにする
        if "key2" in cache._cache:
            comments, _ = cache._cache["key2"]
            expired_time = datetime.now() - timedelta(hours=2)
            cache._cache["key2"] = (comments, expired_time)
        
        # クリーンアップ実行
        cleaned_count = cache.cleanup_expired()
        assert cleaned_count == 1
        
        # key2が削除されている
        assert cache.get("key2") is None
        assert cache.get("key1") is not None
        assert cache.get("key3") is not None
    
    def test_invalidate(self, cache, sample_comments):
        """特定キーの無効化テスト"""
        # データを設定
        cache.set("key1", sample_comments)
        cache.set("key2", sample_comments)
        
        # key1を無効化
        result = cache.invalidate("key1")
        assert result is True
        
        # key1は取得できない
        assert cache.get("key1") is None
        # key2は取得できる
        assert cache.get("key2") is not None
        
        # 存在しないキーの無効化
        result = cache.invalidate("nonexistent")
        assert result is False
    
    def test_clear(self, cache, sample_comments):
        """キャッシュクリアのテスト"""
        # データを設定
        cache.set("key1", sample_comments)
        cache.set("key2", sample_comments)
        
        # クリア実行
        cache.clear()
        
        # すべてのデータが削除されている
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        
        # 統計情報も確認
        stats = cache.get_stats()
        assert stats['size'] == 0
    
    def test_stats(self, cache, sample_comments):
        """統計情報取得のテスト"""
        # 初期状態
        stats = cache.get_stats()
        assert stats['size'] == 0
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        
        # 操作後の統計
        cache.get("key1")  # miss
        cache.set("key1", sample_comments)
        cache.get("key1")  # hit
        
        stats = cache.get_stats()
        assert stats['size'] == 1
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['total_requests'] == 2
        assert stats['hit_rate'] == 0.5
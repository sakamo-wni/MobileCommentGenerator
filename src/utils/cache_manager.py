"""
統一キャッシュマネージャー

アプリケーション全体のキャッシュを管理し、
一貫したキャッシュポリシーを適用する
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

from src.utils.cache import TTLCache
from src.types.aliases import JsonDict
from src.types.cache_types import CacheStats

logger = logging.getLogger(__name__)

# psutilはオプショナル（インストールされていない場合はフォールバック）
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("psutilがインストールされていません。メモリ監視機能が制限されます。")

T = TypeVar('T')


@dataclass
class CacheConfig:
    """キャッシュ設定"""
    default_ttl_seconds: int = 300  # 5分
    max_size: int = 1000
    max_memory_mb: float = 100
    enable_auto_cleanup: bool = True
    cleanup_interval_seconds: int = 60
    enable_memory_pressure_handling: bool = True
    memory_pressure_threshold: float = 0.8  # 80%
    enable_stats_tracking: bool = True
    stats_file_path: Path | None = field(default_factory=lambda: Path("cache_stats.json"))
    

@dataclass
class ExtendedCacheStats:
    """拡張キャッシュ統計情報"""
    basic_stats: CacheStats
    memory_pressure: float = 0.0
    evictions_by_memory_pressure: int = 0
    evictions_by_ttl: int = 0
    evictions_by_lru: int = 0
    average_entry_size_bytes: float = 0.0
    cache_efficiency_score: float = 0.0  # 0-1のスコア
    last_cleanup_time: datetime | None = None
    total_cleanup_count: int = 0


class CacheManager:
    """統一キャッシュマネージャー"""
    
    _instance: CacheManager | None = None
    _lock = threading.Lock()
    
    def __new__(cls) -> CacheManager:
        """シングルトンパターンの実装"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self):
        """初期化"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._caches: dict[str, TTLCache] = {}
        self._configs: dict[str, CacheConfig] = {}
        self._extended_stats: dict[str, ExtendedCacheStats] = {}
        self._global_config = CacheConfig()
        self._monitoring_thread: threading.Thread | None = None
        self._stop_monitoring = threading.Event()
        
        # デフォルトのキャッシュを作成
        self._create_default_caches()
        
        # メモリ監視スレッドを開始
        if self._global_config.enable_memory_pressure_handling:
            self._start_memory_monitoring()
    
    def _create_default_caches(self):
        """デフォルトのキャッシュを作成"""
        # APIレスポンスキャッシュ
        self.create_cache(
            "api_responses",
            CacheConfig(
                default_ttl_seconds=300,
                max_size=500,
                max_memory_mb=50
            )
        )
        
        # コメントキャッシュ
        self.create_cache(
            "comments",
            CacheConfig(
                default_ttl_seconds=3600,  # 1時間
                max_size=1000,
                max_memory_mb=30
            )
        )
        
        # 天気予報キャッシュ
        self.create_cache(
            "weather_forecasts",
            CacheConfig(
                default_ttl_seconds=600,  # 10分
                max_size=200,
                max_memory_mb=20
            )
        )
    
    def create_cache(self, name: str, config: CacheConfig | None = None) -> TTLCache:
        """新しいキャッシュを作成"""
        if config is None:
            config = self._global_config
            
        cache = TTLCache(
            default_ttl=config.default_ttl_seconds,
            max_size=config.max_size,
            auto_cleanup=config.enable_auto_cleanup,
            cleanup_interval=config.cleanup_interval_seconds
        )
        
        self._caches[name] = cache
        self._configs[name] = config
        self._extended_stats[name] = ExtendedCacheStats(
            basic_stats=cache.get_stats()
        )
        
        logger.info(f"Created cache '{name}' with config: {config}")
        return cache
    
    def get_cache(self, name: str) -> TTLCache:
        """キャッシュを取得"""
        if name not in self._caches:
            logger.warning(f"Cache '{name}' not found, creating with default config")
            return self.create_cache(name)
        return self._caches[name]
    
    def get_all_stats(self) -> dict[str, ExtendedCacheStats]:
        """全キャッシュの統計情報を取得"""
        for name, cache in self._caches.items():
            basic_stats = cache.get_stats()
            extended_stats = self._extended_stats[name]
            extended_stats.basic_stats = basic_stats
            
            # 効率スコアを計算
            if basic_stats["total_requests"] > 0:
                efficiency = basic_stats["hit_rate"] * 0.7  # ヒット率の重み
                
                # メモリ効率を加味
                config = self._configs[name]
                max_memory = config.max_memory_mb * 1024 * 1024
                memory_usage_ratio = basic_stats["memory_usage_bytes"] / max_memory
                memory_efficiency = 1.0 - memory_usage_ratio
                efficiency += memory_efficiency * 0.3
                
                extended_stats.cache_efficiency_score = min(1.0, efficiency)
        
        return self._extended_stats.copy()
    
    def get_stats_summary(self) -> JsonDict:
        """統計情報のサマリーを取得"""
        all_stats = self.get_all_stats()
        
        total_memory = sum(
            stats.basic_stats.memory_usage_bytes 
            for stats in all_stats.values()
        )
        
        total_hits = sum(
            stats.basic_stats.hits 
            for stats in all_stats.values()
        )
        
        total_misses = sum(
            stats.basic_stats.misses 
            for stats in all_stats.values()
        )
        
        total_requests = total_hits + total_misses
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0
        
        return {
            "total_caches": len(self._caches),
            "total_memory_usage_mb": total_memory / (1024 * 1024),
            "overall_hit_rate": overall_hit_rate,
            "total_requests": total_requests,
            "memory_pressure": self._get_system_memory_pressure(),
            "cache_details": {
                name: {
                    "size": stats.basic_stats.size,
                    "hit_rate": stats.basic_stats.hit_rate,
                    "memory_usage_mb": stats.basic_stats.memory_usage_bytes / (1024 * 1024),
                    "efficiency_score": stats.cache_efficiency_score
                }
                for name, stats in all_stats.items()
            }
        }
    
    def warm_cache(self, name: str, data: dict[str, Any], ttl: int | None = None):
        """キャッシュをウォーミング（事前にデータを投入）"""
        cache = self.get_cache(name)
        
        for key, value in data.items():
            cache.set(key, value, ttl)
        
        logger.info(f"Warmed cache '{name}' with {len(data)} entries")
    
    def _get_system_memory_pressure(self) -> float:
        """システムのメモリプレッシャーを取得（0-1）"""
        if not HAS_PSUTIL:
            # psutilがない場合はデフォルト値を返す
            return 0.5
        
        try:
            memory = psutil.virtual_memory()
            return memory.percent / 100.0
        except Exception as e:
            logger.error(f"Failed to get system memory info: {e}")
            return 0.0
    
    def _handle_memory_pressure(self):
        """メモリプレッシャーに対応"""
        pressure = self._get_system_memory_pressure()
        
        if pressure > self._global_config.memory_pressure_threshold:
            logger.warning(f"High memory pressure detected: {pressure:.2%}")
            
            # 各キャッシュのサイズを削減
            for name, cache in self._caches.items():
                stats = cache.get_stats()
                if stats["size"] > 0:
                    # 10%のエントリを削除
                    target_evictions = max(1, int(stats["size"] * 0.1))
                    
                    # パブリックメソッドを使用
                    evicted = cache.evict_lru(target_evictions)
                    
                    self._extended_stats[name].evictions_by_memory_pressure += evicted
                    
            logger.info("Memory pressure handled by evicting entries")
    
    def _start_memory_monitoring(self):
        """メモリ監視スレッドを開始"""
        def monitor_memory():
            while not self._stop_monitoring.is_set():
                try:
                    self._handle_memory_pressure()
                    
                    # 統計情報を保存
                    if self._global_config.enable_stats_tracking:
                        self._save_stats()
                        
                except Exception as e:
                    logger.error(f"Error in memory monitoring: {e}")
                
                # 30秒ごとにチェック
                self._stop_monitoring.wait(30)
        
        self._monitoring_thread = threading.Thread(
            target=monitor_memory,
            daemon=True,
            name="CacheMemoryMonitor"
        )
        self._monitoring_thread.start()
        logger.info("Started cache memory monitoring")
    
    def _save_stats(self):
        """統計情報をファイルに保存"""
        if not self._global_config.stats_file_path:
            return
            
        try:
            stats = self.get_stats_summary()
            stats["timestamp"] = datetime.now().isoformat()
            
            # 既存のデータを読み込み
            stats_file = self._global_config.stats_file_path
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            # 新しいデータを追加（最新100件を保持）
            history.append(stats)
            history = history[-100:]
            
            # 保存
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cache stats: {e}")
    
    def clear_all_caches(self):
        """全キャッシュをクリア"""
        for name, cache in self._caches.items():
            cache.clear()
        logger.info("Cleared all caches")
    
    def shutdown(self):
        """シャットダウン処理"""
        self._stop_monitoring.set()
        
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        
        # 各キャッシュのクリーンアップを停止
        for cache in self._caches.values():
            cache.stop_cleanup()
        
        logger.info("Cache manager shutdown complete")


# グローバルインスタンス
_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """キャッシュマネージャーのグローバルインスタンスを取得"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def get_cache(name: str) -> TTLCache:
    """指定された名前のキャッシュを取得（ショートカット）"""
    return get_cache_manager().get_cache(name)
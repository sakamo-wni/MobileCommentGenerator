"""
改善されたキャッシュデコレーター

統一キャッシュマネージャーと連携し、
より柔軟なキャッシュ制御を提供する
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, TypeVar, ParamSpec
from collections.abc import Callable
from functools import wraps

from src.utils.cache_manager import get_cache
from src.utils.cache import generate_cache_key

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


def smart_cache(
    cache_name: str = "default",
    ttl: int | None = None,
    key_prefix: str | None = None,
    condition: Callable[[Any], bool] | None = None,
    bypass_cache: bool = False
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    スマートキャッシュデコレーター
    
    統一キャッシュマネージャーを使用し、条件付きキャッシュや
    バイパス機能をサポートする高度なキャッシュデコレーター
    
    Args:
        cache_name: 使用するキャッシュの名前
        ttl: TTL（秒）。Noneの場合はキャッシュのデフォルト値を使用
        key_prefix: キャッシュキーのプレフィックス
        condition: キャッシュするかどうかを判定する関数（結果を引数に取る）
        bypass_cache: Trueの場合、キャッシュをバイパス（デバッグ用）
    
    Returns:
        デコレートされた関数
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        is_async = inspect.iscoroutinefunction(func)
        cache = get_cache(cache_name)
        
        # キープレフィックスの生成
        prefix = key_prefix or f"{func.__module__}.{func.__name__}"
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                # キャッシュバイパスチェック
                if bypass_cache or kwargs.get('_bypass_cache', False):
                    kwargs.pop('_bypass_cache', None)
                    return await func(*args, **kwargs)
                
                # キャッシュキーの生成
                cache_key = f"{prefix}:{generate_cache_key(*args, **kwargs)}"
                
                # キャッシュから取得を試みる
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit: {prefix}")
                    return cached_result
                
                # 関数を実行
                result = await func(*args, **kwargs)
                
                # 条件チェック
                if condition is None or condition(result):
                    cache.set(cache_key, result, ttl)
                    logger.debug(f"Cached result: {prefix}")
                else:
                    logger.debug(f"Result not cached due to condition: {prefix}")
                
                return result
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                # キャッシュバイパスチェック
                if bypass_cache or kwargs.get('_bypass_cache', False):
                    kwargs.pop('_bypass_cache', None)
                    return func(*args, **kwargs)
                
                # キャッシュキーの生成
                cache_key = f"{prefix}:{generate_cache_key(*args, **kwargs)}"
                
                # キャッシュから取得を試みる
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit: {prefix}")
                    return cached_result
                
                # 関数を実行
                result = func(*args, **kwargs)
                
                # 条件チェック
                if condition is None or condition(result):
                    cache.set(cache_key, result, ttl)
                    logger.debug(f"Cached result: {prefix}")
                else:
                    logger.debug(f"Result not cached due to condition: {prefix}")
                
                return result
            
            return sync_wrapper
    
    return decorator


def cache_result(
    ttl: int = 300,
    cache_name: str = "api_responses",
    cache_errors: bool = False
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    API結果をキャッシュするデコレーター
    
    Args:
        ttl: キャッシュの有効期限（秒）
        cache_name: 使用するキャッシュの名前
        cache_errors: エラーもキャッシュするかどうか
    
    Returns:
        デコレートされた関数
    """
    def should_cache(result: Any) -> bool:
        """キャッシュすべきかどうかを判定"""
        if cache_errors:
            return True
        
        # エラーレスポンスはキャッシュしない
        if isinstance(result, dict):
            if result.get('error') or not result.get('success', True):
                return False
        
        return True
    
    return smart_cache(
        cache_name=cache_name,
        ttl=ttl,
        condition=should_cache
    )


def method_cache(
    ttl: int | None = None,
    cache_attr: str = "_cache",
    key_include_self: bool = False
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    インスタンスメソッド用のキャッシュデコレーター
    
    インスタンスの属性としてキャッシュを保持する場合に使用
    
    Args:
        ttl: キャッシュの有効期限（秒）
        cache_attr: キャッシュを保存する属性名
        key_include_self: selfをキャッシュキーに含めるかどうか
    
    Returns:
        デコレートされたメソッド
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(self, *args: P.args, **kwargs: P.kwargs) -> T:
                # インスタンスキャッシュを取得または作成
                if not hasattr(self, cache_attr):
                    from src.utils.cache import TTLCache
                    setattr(self, cache_attr, TTLCache())
                
                cache = getattr(self, cache_attr)
                
                # キャッシュキーの生成（統一された関数を使用）
                if key_include_self:
                    cache_key = f"{func.__name__}:{id(self)}:{generate_cache_key(*args, **kwargs)}"
                else:
                    cache_key = f"{func.__name__}:{generate_cache_key(*args, **kwargs)}"
                
                # キャッシュから取得
                cached = cache.get(cache_key)
                if cached is not None:
                    return cached
                
                # 実行してキャッシュ
                result = await func(self, *args, **kwargs)
                cache.set(cache_key, result, ttl)
                
                return result
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(self, *args: P.args, **kwargs: P.kwargs) -> T:
                # インスタンスキャッシュを取得または作成
                if not hasattr(self, cache_attr):
                    from src.utils.cache import TTLCache
                    setattr(self, cache_attr, TTLCache())
                
                cache = getattr(self, cache_attr)
                
                # キャッシュキーの生成（統一された関数を使用）
                if key_include_self:
                    cache_key = f"{func.__name__}:{id(self)}:{generate_cache_key(*args, **kwargs)}"
                else:
                    cache_key = f"{func.__name__}:{generate_cache_key(*args, **kwargs)}"
                
                # キャッシュから取得
                cached = cache.get(cache_key)
                if cached is not None:
                    return cached
                
                # 実行してキャッシュ
                result = func(self, *args, **kwargs)
                cache.set(cache_key, result, ttl)
                
                return result
            
            return sync_wrapper
    
    return decorator


# 後方互換性のためのエイリアス
cached = smart_cache
async_cached = smart_cache
"""
メモリ関連のユーティリティ関数

より正確なメモリサイズ計算を提供
"""

from __future__ import annotations

import sys
from typing import Any
from collections.abc import Mapping, Container


def get_deep_size(obj: Any, seen: set[int] | None = None) -> int:
    """
    オブジェクトの深いメモリサイズを計算
    
    ネストされたデータ構造も含めて、より正確なメモリ使用量を計算します。
    循環参照を適切に処理します。
    
    Args:
        obj: サイズを計算するオブジェクト
        seen: 既に計算したオブジェクトのIDセット（循環参照対策）
    
    Returns:
        バイト単位のメモリサイズ
    """
    if seen is None:
        seen = set()
    
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    
    # 既に見たオブジェクトとしてマーク
    seen.add(obj_id)
    
    size = sys.getsizeof(obj)
    
    # 辞書の場合
    if isinstance(obj, dict):
        for key, value in obj.items():
            size += get_deep_size(key, seen)
            size += get_deep_size(value, seen)
    
    # リスト、タプル、セットなどのコンテナ
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            size += get_deep_size(item, seen)
    
    # カスタムオブジェクト（__dict__を持つ）
    elif hasattr(obj, '__dict__'):
        size += get_deep_size(obj.__dict__, seen)
    
    # __slots__を持つオブジェクト
    elif hasattr(obj, '__slots__'):
        for slot in obj.__slots__:
            if hasattr(obj, slot):
                size += get_deep_size(getattr(obj, slot), seen)
    
    return size


def estimate_cache_memory_usage(cache_dict: dict[str, Any]) -> dict[str, int]:
    """
    キャッシュのメモリ使用量を詳細に推定
    
    Args:
        cache_dict: キャッシュの辞書
    
    Returns:
        メモリ使用量の詳細情報
    """
    total_size = sys.getsizeof(cache_dict)
    key_sizes = 0
    value_sizes = 0
    entry_count = len(cache_dict)
    
    # 各エントリのサイズを計算
    largest_entries = []
    
    for key, value in cache_dict.items():
        key_size = get_deep_size(key)
        value_size = get_deep_size(value)
        entry_size = key_size + value_size
        
        key_sizes += key_size
        value_sizes += value_size
        
        # 大きなエントリを記録（上位10個）
        if len(largest_entries) < 10 or entry_size > largest_entries[-1][1]:
            largest_entries.append((key, entry_size))
            largest_entries.sort(key=lambda x: x[1], reverse=True)
            largest_entries = largest_entries[:10]
    
    return {
        "total_size": total_size + key_sizes + value_sizes,
        "dict_overhead": total_size,
        "key_sizes": key_sizes,
        "value_sizes": value_sizes,
        "entry_count": entry_count,
        "average_entry_size": (key_sizes + value_sizes) / entry_count if entry_count > 0 else 0,
        "largest_entries": [
            {"key": str(key)[:50], "size": size} 
            for key, size in largest_entries
        ]
    }


def format_bytes(bytes_size: int) -> str:
    """
    バイトサイズを人間が読みやすい形式にフォーマット
    
    Args:
        bytes_size: バイト単位のサイズ
    
    Returns:
        フォーマットされた文字列（例: "1.5 MB"）
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def get_memory_efficient_cache_size(available_memory_mb: float, 
                                  target_usage_percent: float = 0.1) -> int:
    """
    利用可能なメモリに基づいて適切なキャッシュサイズを計算
    
    Args:
        available_memory_mb: 利用可能なメモリ（MB）
        target_usage_percent: キャッシュに使用する割合（デフォルト: 10%）
    
    Returns:
        推奨されるキャッシュエントリ数
    """
    # 1エントリあたりの平均サイズを仮定（1KB）
    average_entry_size_bytes = 1024
    
    target_memory_bytes = available_memory_mb * 1024 * 1024 * target_usage_percent
    recommended_size = int(target_memory_bytes / average_entry_size_bytes)
    
    # 最小・最大値でクリップ
    return max(100, min(recommended_size, 10000))
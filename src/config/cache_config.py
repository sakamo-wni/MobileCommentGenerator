"""
キャッシュ設定

環境変数または設定ファイルからキャッシュパラメータを読み込む
"""

from __future__ import annotations
import os
from typing import Any


class CacheConfig:
    """キャッシュ設定クラス"""
    
    # デフォルト値
    DEFAULT_LEVENSHTEIN_CACHE_SIZE = 4096
    DEFAULT_WXTECH_CACHE_SIZE = 100
    DEFAULT_WXTECH_CACHE_TTL = 300  # 5分
    
    @staticmethod
    def get_levenshtein_cache_size() -> int:
        """レーベンシュタイン距離計算のキャッシュサイズを取得
        
        環境変数 LEVENSHTEIN_CACHE_SIZE から読み込み、
        未設定の場合はデフォルト値を使用
        
        Returns:
            キャッシュサイズ
        """
        return int(os.environ.get(
            'LEVENSHTEIN_CACHE_SIZE', 
            str(CacheConfig.DEFAULT_LEVENSHTEIN_CACHE_SIZE)
        ))
    
    @staticmethod
    def get_wxtech_cache_size() -> int:
        """WxTech APIキャッシュサイズを取得
        
        環境変数 WXTECH_CACHE_SIZE から読み込み、
        未設定の場合はデフォルト値を使用
        
        Returns:
            キャッシュサイズ
        """
        return int(os.environ.get(
            'WXTECH_CACHE_SIZE',
            str(CacheConfig.DEFAULT_WXTECH_CACHE_SIZE)
        ))
    
    @staticmethod
    def get_wxtech_cache_ttl() -> int:
        """WxTech APIキャッシュのTTL（秒）を取得
        
        環境変数 WXTECH_CACHE_TTL から読み込み、
        未設定の場合はデフォルト値を使用
        
        Returns:
            TTL（秒）
        """
        return int(os.environ.get(
            'WXTECH_CACHE_TTL',
            str(CacheConfig.DEFAULT_WXTECH_CACHE_TTL)
        ))
    
    @staticmethod
    def get_all_settings() -> dict[str, Any]:
        """すべてのキャッシュ設定を取得
        
        Returns:
            キャッシュ設定の辞書
        """
        return {
            'levenshtein_cache_size': CacheConfig.get_levenshtein_cache_size(),
            'wxtech_cache_size': CacheConfig.get_wxtech_cache_size(),
            'wxtech_cache_ttl': CacheConfig.get_wxtech_cache_ttl(),
        }
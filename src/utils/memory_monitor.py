"""
Memory usage monitor

メモリ使用量の監視
"""

from __future__ import annotations
import psutil
import os
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryMonitor:
    """メモリ使用量モニター
    
    システムのメモリ使用量を監視し、
    閾値を超えた場合に警告を発行
    """
    
    def __init__(self, 
                 warning_threshold_percent: float = 80.0,
                 critical_threshold_percent: float = 90.0):
        """初期化
        
        Args:
            warning_threshold_percent: 警告閾値（％）
            critical_threshold_percent: 危険閾値（％）
        """
        self.warning_threshold = warning_threshold_percent
        self.critical_threshold = critical_threshold_percent
        self._process = psutil.Process(os.getpid())
        self._last_check = datetime.now()
        
    def get_memory_info(self) -> Dict[str, Any]:
        """メモリ情報を取得
        
        Returns:
            メモリ使用状況の辞書
        """
        # プロセスメモリ情報
        process_info = self._process.memory_info()
        process_percent = self._process.memory_percent()
        
        # システムメモリ情報
        virtual_memory = psutil.virtual_memory()
        
        info = {
            "process": {
                "rss_mb": process_info.rss / 1024 / 1024,  # Resident Set Size (MB)
                "vms_mb": process_info.vms / 1024 / 1024,  # Virtual Memory Size (MB)
                "percent": process_percent,
                "pid": self._process.pid
            },
            "system": {
                "total_mb": virtual_memory.total / 1024 / 1024,
                "available_mb": virtual_memory.available / 1024 / 1024,
                "percent": virtual_memory.percent,
                "used_mb": virtual_memory.used / 1024 / 1024
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return info
    
    def check_memory_usage(self) -> tuple[bool, str]:
        """メモリ使用量をチェック
        
        Returns:
            (警告が必要か, メッセージ)
        """
        info = self.get_memory_info()
        system_percent = info["system"]["percent"]
        process_mb = info["process"]["rss_mb"]
        
        if system_percent >= self.critical_threshold:
            msg = (
                f"⚠️ メモリ使用量が危険域に達しています: "
                f"システム {system_percent:.1f}%, "
                f"プロセス {process_mb:.1f}MB"
            )
            logger.critical(msg)
            return True, msg
            
        elif system_percent >= self.warning_threshold:
            msg = (
                f"⚡ メモリ使用量が高くなっています: "
                f"システム {system_percent:.1f}%, "
                f"プロセス {process_mb:.1f}MB"
            )
            logger.warning(msg)
            return True, msg
            
        return False, ""
    
    def get_cache_memory_estimate(self, 
                                cache_sizes: Dict[str, int],
                                avg_entry_size_kb: float = 2.0) -> Dict[str, float]:
        """キャッシュのメモリ使用量を推定
        
        Args:
            cache_sizes: 各キャッシュのエントリ数
            avg_entry_size_kb: エントリあたりの平均サイズ（KB）
            
        Returns:
            各キャッシュの推定メモリ使用量（MB）
        """
        estimates = {}
        total_mb = 0.0
        
        for cache_name, entry_count in cache_sizes.items():
            size_mb = (entry_count * avg_entry_size_kb) / 1024
            estimates[cache_name] = size_mb
            total_mb += size_mb
            
        estimates["total"] = total_mb
        
        # 現在のプロセスメモリに対する割合
        process_info = self._process.memory_info()
        process_mb = process_info.rss / 1024 / 1024
        estimates["cache_percent_of_process"] = (total_mb / process_mb * 100) if process_mb > 0 else 0
        
        return estimates
    
    @staticmethod
    def format_memory_size(size_mb: float) -> str:
        """メモリサイズを読みやすい形式にフォーマット
        
        Args:
            size_mb: サイズ（MB）
            
        Returns:
            フォーマットされた文字列
        """
        if size_mb < 1024:
            return f"{size_mb:.1f}MB"
        else:
            return f"{size_mb / 1024:.1f}GB"
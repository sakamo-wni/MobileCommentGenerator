"""
Test module for MemoryMonitor

メモリ監視機能のテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from src.utils.memory_monitor import MemoryMonitor, PSUTIL_AVAILABLE


class TestMemoryMonitor:
    """MemoryMonitorのテストクラス"""
    
    @pytest.fixture
    def monitor(self):
        """テスト用のMemoryMonitorインスタンス"""
        return MemoryMonitor(
            warning_threshold_percent=80.0,
            critical_threshold_percent=90.0
        )
    
    def test_init_with_psutil_unavailable(self):
        """psutilが利用できない場合の初期化テスト"""
        with patch('src.utils.memory_monitor.PSUTIL_AVAILABLE', False):
            monitor = MemoryMonitor()
            assert monitor._process is None
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_init_with_psutil_available(self):
        """psutilが利用可能な場合の初期化テスト"""
        monitor = MemoryMonitor()
        assert monitor._process is not None
        assert monitor.warning_threshold == 80.0
        assert monitor.critical_threshold == 90.0
    
    def test_get_memory_info_without_psutil(self):
        """psutilなしでのメモリ情報取得テスト"""
        with patch('src.utils.memory_monitor.PSUTIL_AVAILABLE', False):
            monitor = MemoryMonitor()
            info = monitor.get_memory_info()
            
            assert info["monitoring_disabled"] is True
            assert info["process"]["rss_mb"] == 0
            assert info["system"]["percent"] == 0
            assert info["process"]["pid"] == os.getpid()
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_get_memory_info_with_psutil(self, monitor):
        """psutilありでのメモリ情報取得テスト"""
        info = monitor.get_memory_info()
        
        assert "monitoring_disabled" not in info
        assert info["process"]["rss_mb"] > 0
        assert info["process"]["pid"] == os.getpid()
        assert 0 <= info["system"]["percent"] <= 100
        assert info["system"]["total_mb"] > 0
    
    def test_check_memory_usage_without_psutil(self):
        """psutilなしでのメモリ使用量チェックテスト"""
        with patch('src.utils.memory_monitor.PSUTIL_AVAILABLE', False):
            monitor = MemoryMonitor()
            warning_needed, msg = monitor.check_memory_usage()
            
            assert warning_needed is False
            assert msg == ""
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_check_memory_usage_normal(self, monitor):
        """通常のメモリ使用量チェックテスト"""
        with patch.object(monitor, 'get_memory_info') as mock_get_info:
            mock_get_info.return_value = {
                "system": {"percent": 50.0},
                "process": {"rss_mb": 100.0}
            }
            
            warning_needed, msg = monitor.check_memory_usage()
            
            assert warning_needed is False
            assert msg == ""
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_check_memory_usage_warning(self, monitor):
        """警告閾値でのメモリ使用量チェックテスト"""
        with patch.object(monitor, 'get_memory_info') as mock_get_info:
            mock_get_info.return_value = {
                "system": {"percent": 85.0},
                "process": {"rss_mb": 500.0}
            }
            
            warning_needed, msg = monitor.check_memory_usage()
            
            assert warning_needed is True
            assert "メモリ使用量が高くなっています" in msg
            assert "85.0%" in msg
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_check_memory_usage_critical(self, monitor):
        """危険閾値でのメモリ使用量チェックテスト"""
        with patch.object(monitor, 'get_memory_info') as mock_get_info:
            mock_get_info.return_value = {
                "system": {"percent": 95.0},
                "process": {"rss_mb": 1000.0}
            }
            
            warning_needed, msg = monitor.check_memory_usage()
            
            assert warning_needed is True
            assert "メモリ使用量が危険域に達しています" in msg
            assert "95.0%" in msg
    
    def test_get_cache_memory_estimate(self, monitor):
        """キャッシュメモリ推定のテスト"""
        cache_sizes = {
            "memory_cache": 100,
            "spatial_cache": 50,
            "comment_cache": 200
        }
        
        estimates = monitor.get_cache_memory_estimate(cache_sizes, avg_entry_size_kb=2.0)
        
        # 各キャッシュのサイズ計算確認
        assert estimates["memory_cache"] == (100 * 2.0) / 1024
        assert estimates["spatial_cache"] == (50 * 2.0) / 1024
        assert estimates["comment_cache"] == (200 * 2.0) / 1024
        
        # 合計サイズ確認
        expected_total = (350 * 2.0) / 1024
        assert estimates["total"] == expected_total
    
    def test_get_cache_memory_estimate_with_psutil_unavailable(self):
        """psutilなしでのキャッシュメモリ推定テスト"""
        with patch('src.utils.memory_monitor.PSUTIL_AVAILABLE', False):
            monitor = MemoryMonitor()
            cache_sizes = {"test_cache": 100}
            
            estimates = monitor.get_cache_memory_estimate(cache_sizes)
            
            assert estimates["test_cache"] == (100 * 2.0) / 1024
            assert estimates["cache_percent_of_process"] == 0
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_get_cache_memory_estimate_with_process_memory(self, monitor):
        """プロセスメモリに対する割合計算のテスト"""
        # プロセスメモリ情報をモック
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100MB
        mock_process.memory_info.return_value = mock_memory_info
        monitor._process = mock_process
        
        cache_sizes = {"test_cache": 1024}  # 2MB相当
        estimates = monitor.get_cache_memory_estimate(cache_sizes)
        
        # 2MB / 100MB = 2%
        assert estimates["cache_percent_of_process"] == 2.0
    
    def test_format_memory_size(self):
        """メモリサイズフォーマットのテスト"""
        # MB表示
        assert MemoryMonitor.format_memory_size(512.5) == "512.5MB"
        assert MemoryMonitor.format_memory_size(1023.9) == "1023.9MB"
        
        # GB表示
        assert MemoryMonitor.format_memory_size(1024.0) == "1.0GB"
        assert MemoryMonitor.format_memory_size(2048.0) == "2.0GB"
        assert MemoryMonitor.format_memory_size(1536.0) == "1.5GB"
    
    def test_custom_thresholds(self):
        """カスタム閾値の設定テスト"""
        monitor = MemoryMonitor(
            warning_threshold_percent=70.0,
            critical_threshold_percent=85.0
        )
        
        assert monitor.warning_threshold == 70.0
        assert monitor.critical_threshold == 85.0
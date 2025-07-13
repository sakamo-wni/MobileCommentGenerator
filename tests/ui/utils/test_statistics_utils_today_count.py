"""統計ユーティリティのtoday_count機能のテスト"""

import pytest
from datetime import datetime, date, timedelta
from src.ui.utils.statistics_utils import get_statistics


class TestStatisticsUtilsTodayCount:
    """today_count機能のテストクラス"""
    
    def test_today_count_empty_history(self):
        """空の履歴での今日のカウント"""
        stats = get_statistics([])
        assert stats["today_count"] == 0
    
    def test_today_count_single_today(self):
        """今日の1件のみ"""
        today = datetime.now()
        history = [{
            "timestamp": today.isoformat(),
            "success": True,
            "location": "Tokyo"
        }]
        stats = get_statistics(history)
        assert stats["today_count"] == 1
    
    def test_today_count_multiple_today(self):
        """今日の複数件"""
        today = datetime.now()
        history = [
            {
                "timestamp": today.isoformat(),
                "success": True,
                "location": "Tokyo"
            },
            {
                "timestamp": (today - timedelta(hours=1)).isoformat(),
                "success": True,
                "location": "Osaka"
            },
            {
                "timestamp": (today - timedelta(hours=2)).isoformat(),
                "success": False,
                "location": "Nagoya"
            }
        ]
        stats = get_statistics(history)
        assert stats["today_count"] == 3
    
    def test_today_count_mixed_dates(self):
        """今日と昨日の混在"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        history = [
            {
                "timestamp": today.isoformat(),
                "success": True,
                "location": "Tokyo"
            },
            {
                "timestamp": yesterday.isoformat(),
                "success": True,
                "location": "Osaka"
            },
            {
                "timestamp": today.isoformat(),
                "success": False,
                "location": "Nagoya"
            }
        ]
        stats = get_statistics(history)
        assert stats["today_count"] == 2
    
    def test_today_count_no_today(self):
        """今日のデータがない場合"""
        yesterday = datetime.now() - timedelta(days=1)
        last_week = datetime.now() - timedelta(days=7)
        history = [
            {
                "timestamp": yesterday.isoformat(),
                "success": True,
                "location": "Tokyo"
            },
            {
                "timestamp": last_week.isoformat(),
                "success": True,
                "location": "Osaka"
            }
        ]
        stats = get_statistics(history)
        assert stats["today_count"] == 0
    
    def test_latest_generation(self):
        """最新生成日時の取得"""
        now = datetime.now()
        earlier = now - timedelta(hours=2)
        yesterday = now - timedelta(days=1)
        
        history = [
            {
                "timestamp": yesterday.isoformat(),
                "success": True,
                "location": "Tokyo"
            },
            {
                "timestamp": now.isoformat(),
                "success": True,
                "location": "Osaka"
            },
            {
                "timestamp": earlier.isoformat(),
                "success": True,
                "location": "Nagoya"
            }
        ]
        stats = get_statistics(history)
        assert stats["latest_generation"] == now.isoformat()
    
    def test_successful_generations_count(self):
        """成功した生成数のカウント"""
        today = datetime.now()
        history = [
            {
                "timestamp": today.isoformat(),
                "success": True,
                "location": "Tokyo"
            },
            {
                "timestamp": today.isoformat(),
                "success": False,
                "location": "Osaka"
            },
            {
                "timestamp": today.isoformat(),
                "success": True,
                "location": "Nagoya"
            },
            {
                "timestamp": today.isoformat(),
                "success": False,
                "location": "Kyoto"
            }
        ]
        stats = get_statistics(history)
        assert stats["successful_generations"] == 2
        assert stats["total_generations"] == 4
        assert stats["success_rate"] == 50.0
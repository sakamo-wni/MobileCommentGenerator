#!/usr/bin/env python3
"""
キャッシュ優先度のテスト

最新のキャッシュデータが優先されることを確認
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz
from src.data.forecast_cache import ForecastCache

def test_cache_prioritization():
    """キャッシュから最新データが取得されることを確認"""
    
    cache = ForecastCache()
    jst = pytz.timezone("Asia/Tokyo")
    
    # テスト対象: 八丈島の明日15時
    location_name = "八丈島"
    tomorrow = datetime.now(jst).date() + timedelta(days=1)
    target_time = jst.localize(datetime.combine(tomorrow, datetime.min.time().replace(hour=15)))
    
    print(f"テスト対象: {location_name} @ {target_time.strftime('%Y-%m-%d %H:%M')}")
    print("-" * 60)
    
    # キャッシュから取得
    entry = cache.get_forecast_at_time(location_name, target_time, tolerance_hours=3)
    
    if entry:
        print(f"取得されたエントリ:")
        print(f"  予報時刻: {entry.forecast_datetime.strftime('%Y-%m-%d %H:%M')}")
        print(f"  キャッシュ保存時刻: {entry.cached_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"  天気: {entry.weather_description}")
        print(f"  降水量: {entry.precipitation}mm")
        print(f"  気温: {entry.temperature}°C")
        
        # 最新のキャッシュが取得されているか確認
        if entry.cached_at.date() == datetime.now(jst).date():
            print("\n✅ 最新のキャッシュデータが取得されました")
        else:
            print(f"\n⚠️ 古いキャッシュデータが取得されました (保存日: {entry.cached_at.date()})")
    else:
        print("❌ キャッシュエントリが見つかりませんでした")

if __name__ == "__main__":
    test_cache_prioritization()
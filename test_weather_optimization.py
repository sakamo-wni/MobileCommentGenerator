#!/usr/bin/env python3
"""
天気予報データ取得の最適化をテストするスクリプト
"""

import os
import sys
from datetime import datetime, timedelta
import pytz
import json

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.apis.wxtech.client import WxTechAPIClient
from src.nodes.weather_forecast.services import CacheService
from src.config.config_loader import load_config


def test_optimized_forecast_fetching():
    """最適化された天気予報取得をテスト"""
    
    # 設定読み込み
    try:
        config = load_config('weather_settings')
        api_key = config.wxtech_api_key
    except:
        print("⚠️ 環境変数 WXTECH_API_KEY を設定してください")
        api_key = os.getenv('WXTECH_API_KEY')
        if not api_key:
            print("❌ APIキーが設定されていません")
            return
    
    # テスト用の地点（東京）
    test_location = {
        'name': '東京',
        'lat': 35.6762,
        'lon': 139.6503
    }
    
    print("=== 天気予報データ取得最適化テスト ===")
    print(f"地点: {test_location['name']} ({test_location['lat']}, {test_location['lon']})")
    
    # 現在時刻
    jst = pytz.timezone("Asia/Tokyo")
    now_jst = datetime.now(jst)
    print(f"現在時刻: {now_jst.strftime('%Y-%m-%d %H:%M:%S JST')}")
    
    # APIクライアント作成
    client = WxTechAPIClient(api_key)
    
    try:
        # 最適化された取得メソッドを呼び出し
        print("\n📡 翌日の天気予報データを取得中...")
        forecast_collection = client.get_forecast_for_next_day_hours(
            test_location['lat'], 
            test_location['lon']
        )
        
        if forecast_collection and forecast_collection.forecasts:
            print(f"✅ {len(forecast_collection.forecasts)}件のデータを取得")
            
            # 取得したデータの時刻を表示
            print("\n取得したデータの時刻:")
            for i, forecast in enumerate(forecast_collection.forecasts[:10]):
                forecast_jst = forecast.datetime.astimezone(jst)
                print(f"  {i+1}. {forecast_jst.strftime('%Y-%m-%d %H:%M')} - "
                      f"気温: {forecast.temperature}℃, 天気: {forecast.weather_description}")
            
            # 翌日の9,12,15,18時のデータが含まれているか確認
            target_date = now_jst.date() + timedelta(days=1)
            target_hours = [9, 12, 15, 18]
            
            print(f"\n翌日({target_date})の主要時刻データ確認:")
            for hour in target_hours:
                found = False
                for forecast in forecast_collection.forecasts:
                    forecast_jst = forecast.datetime.astimezone(jst)
                    if (forecast_jst.date() == target_date and 
                        forecast_jst.hour == hour):
                        print(f"  ✅ {hour}時: データあり")
                        found = True
                        break
                if not found:
                    print(f"  ❌ {hour}時: データなし")
            
            # キャッシュ保存のテスト
            print("\n💾 キャッシュ保存テスト...")
            cache_service = CacheService()
            
            # 最初の予報データを選択（テスト用）
            selected_forecast = forecast_collection.forecasts[0]
            
            # キャッシュに保存
            cache_service.save_forecasts(
                selected_forecast,
                forecast_collection.forecasts,
                test_location['name']
            )
            
            print("✅ キャッシュ保存完了")
            
        else:
            print("❌ 予報データが取得できませんでした")
            
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
    
    print("\n=== テスト完了 ===")


if __name__ == "__main__":
    test_optimized_forecast_fetching()
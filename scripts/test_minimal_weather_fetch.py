#!/usr/bin/env python3
"""
最小限の天気データ取得をテストするスクリプト

現在時刻から翌日の9,12,15,18時のデータのみを効率的に取得できるかテストします。
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
from datetime import datetime, timedelta
import pytz
import logging
from dotenv import load_dotenv

from src.apis.wxtech.client import WxTechAPIClient
from src.apis.wxtech.api import WxTechAPI
from src.apis.wxtech.parser import parse_forecast_response

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

def analyze_current_implementation(client: WxTechAPIClient, lat: float, lon: float):
    """現在の実装での取得データを分析"""
    logger.info("=" * 80)
    logger.info("🔍 現在の実装での取得データを分析")
    logger.info("=" * 80)
    
    # 現在の実装を実行
    forecast_collection = client.get_forecast_for_next_day_hours(lat, lon)
    
    logger.info(f"📊 取得したデータ数: {len(forecast_collection.forecasts)}件")
    
    # 時刻別にグループ化
    hourly_data = {}
    for forecast in forecast_collection.forecasts:
        hour = forecast.datetime.hour
        if hour not in hourly_data:
            hourly_data[hour] = []
        hourly_data[hour].append(forecast)
    
    logger.info(f"📅 時刻別データ:")
    for hour in sorted(hourly_data.keys()):
        logger.info(f"  {hour:02d}時: {len(hourly_data[hour])}件")
    
    # 翌日の9,12,15,18時のデータを確認
    target_hours = [9, 12, 15, 18]
    jst = pytz.timezone("Asia/Tokyo")
    tomorrow = datetime.now(jst).date() + timedelta(days=1)
    
    logger.info(f"\n🎯 翌日({tomorrow})の目標時刻のデータ:")
    for hour in target_hours:
        if hour in hourly_data:
            for forecast in hourly_data[hour]:
                if forecast.datetime.date() == tomorrow:
                    logger.info(f"  {hour:02d}時: ✅ {forecast.datetime.strftime('%Y-%m-%d %H:%M')} - {forecast.weather_description}")
        else:
            logger.info(f"  {hour:02d}時: ❌ データなし")
    
    return forecast_collection


def test_minimal_fetch(api_key: str, lat: float, lon: float):
    """最小限のデータ取得をテスト"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 最小限のデータ取得テスト")
    logger.info("=" * 80)
    
    jst = pytz.timezone("Asia/Tokyo")
    now_jst = datetime.now(jst)
    target_date = now_jst.date() + timedelta(days=1)
    
    logger.info(f"⏰ 現在時刻: {now_jst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"📅 目標日付: {target_date}")
    
    # 方法1: 最小時間範囲の動的計算（翌日8時-19時）
    tomorrow_8am = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=8)))
    tomorrow_7pm = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=19)))
    
    hours_to_8am = (tomorrow_8am - now_jst).total_seconds() / 3600
    hours_to_7pm = (tomorrow_7pm - now_jst).total_seconds() / 3600
    
    logger.info(f"\n📊 時間計算:")
    logger.info(f"  翌日8時まで: {hours_to_8am:.1f}時間")
    logger.info(f"  翌日19時まで: {hours_to_7pm:.1f}時間")
    
    # 最適な取得時間を決定
    if hours_to_8am > 0:
        # まだ翌日8時前なので、8時から19時までの12時間分
        forecast_hours = int(hours_to_8am) + 12
        logger.info(f"  → 取得時間: {forecast_hours}時間（現在から翌日8時 + 12時間）")
    else:
        # すでに翌日8時を過ぎているので、現在から19時まで
        forecast_hours = max(int(hours_to_7pm) + 1, 1)
        logger.info(f"  → 取得時間: {forecast_hours}時間（現在から翌日19時まで）")
    
    # APIリクエスト
    api = WxTechAPI(api_key)
    params = {
        "lat": lat,
        "lon": lon,
        "hours": forecast_hours
    }
    
    logger.info(f"\n🔄 APIリクエスト: {params}")
    raw_data = api.make_request("ss1wx", params)
    
    # レスポンス解析
    if "wxdata" in raw_data and raw_data["wxdata"]:
        wxdata = raw_data["wxdata"][0]
        srf_data = wxdata.get("srf", [])
        mrf_data = wxdata.get("mrf", [])
        
        logger.info(f"\n📦 APIレスポンス:")
        logger.info(f"  SRF（短期予報）: {len(srf_data)}件")
        logger.info(f"  MRF（中期予報）: {len(mrf_data)}件")
        logger.info(f"  合計データ数: {len(srf_data) + len(mrf_data)}件")
        
        # データをパース
        forecast_collection = parse_forecast_response(raw_data, f"lat:{lat},lon:{lon}")
        
        # 時刻別に分析
        hourly_data = {}
        for forecast in forecast_collection.forecasts:
            hour = forecast.datetime.hour
            date = forecast.datetime.date()
            key = (date, hour)
            if key not in hourly_data:
                hourly_data[key] = []
            hourly_data[key].append(forecast)
        
        logger.info(f"\n📊 取得したデータの時刻分布:")
        for (date, hour) in sorted(hourly_data.keys()):
            count = len(hourly_data[(date, hour)])
            logger.info(f"  {date} {hour:02d}時: {count}件")
        
        # 翌日の目標時刻データを確認
        target_hours = [9, 12, 15, 18]
        logger.info(f"\n✅ 翌日の目標時刻データ確認:")
        target_data_count = 0
        for hour in target_hours:
            key = (target_date, hour)
            if key in hourly_data:
                target_data_count += len(hourly_data[key])
                logger.info(f"  {hour:02d}時: ✅ {len(hourly_data[key])}件")
            else:
                logger.info(f"  {hour:02d}時: ❌ データなし")
        
        # 効率性の評価
        total_data = len(forecast_collection.forecasts)
        efficiency = (target_data_count / total_data * 100) if total_data > 0 else 0
        
        logger.info(f"\n📈 効率性評価:")
        logger.info(f"  総データ数: {total_data}件")
        logger.info(f"  目標時刻データ: {target_data_count}件")
        logger.info(f"  データ効率: {efficiency:.1f}%")
        logger.info(f"  現在の実装（72時間）と比較: {forecast_hours}/72 = {forecast_hours/72*100:.1f}%のデータ量")
        
        return forecast_collection
    
    else:
        logger.error("❌ APIレスポンスにデータがありません")
        return None


def compare_implementations(api_key: str, lat: float, lon: float):
    """現在の実装と最小限取得の比較"""
    logger.info("\n" + "=" * 80)
    logger.info("📊 実装比較")
    logger.info("=" * 80)
    
    # 現在の実装でのデータ数をカウント
    client = WxTechAPIClient(api_key)
    current_impl = client.get_forecast_for_next_day_hours(lat, lon)
    current_count = len(current_impl.forecasts)
    
    # 最小限取得でのデータ数をカウント
    minimal_impl = test_minimal_fetch(api_key, lat, lon)
    minimal_count = len(minimal_impl.forecasts) if minimal_impl else 0
    
    logger.info(f"\n📊 比較結果:")
    logger.info(f"  現在の実装: {current_count}件のデータ")
    logger.info(f"  最小限実装: {minimal_count}件のデータ")
    logger.info(f"  削減率: {(1 - minimal_count/current_count)*100:.1f}%" if current_count > 0 else "N/A")
    
    client.close()


def main():
    """メイン処理"""
    # API キーの確認
    api_key = os.getenv("WXTECH_API_KEY")
    if not api_key:
        logger.error("❌ WXTECH_API_KEY が設定されていません")
        sys.exit(1)
    
    # テスト地点（東京）
    lat = 35.6762
    lon = 139.6503
    
    logger.info("🚀 最小限天気データ取得テスト開始")
    logger.info(f"📍 テスト地点: 東京 (緯度: {lat}, 経度: {lon})")
    
    # 現在の実装を分析
    client = WxTechAPIClient(api_key)
    try:
        analyze_current_implementation(client, lat, lon)
        
        # 最小限取得をテスト
        test_minimal_fetch(api_key, lat, lon)
        
        # 実装を比較
        compare_implementations(api_key, lat, lon)
        
    finally:
        client.close()
    
    logger.info("\n✅ テスト完了")


if __name__ == "__main__":
    main()
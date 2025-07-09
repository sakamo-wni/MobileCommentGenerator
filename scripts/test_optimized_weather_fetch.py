#!/usr/bin/env python3
"""
最適化された天気データ取得をテストするスクリプト

翌日8-19時の12時間分のみを取得する最適化版
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
from src.data.weather_data import WeatherForecastCollection

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()


def get_forecast_for_next_day_hours_optimized(api: WxTechAPI, lat: float, lon: float) -> WeatherForecastCollection:
    """翌日の9,12,15,18時のデータを効率的に取得する最適化版
    
    翌日8時から19時までの12時間分のみを取得
    """
    jst = pytz.timezone("Asia/Tokyo")
    now_jst = datetime.now(jst)
    target_date = now_jst.date() + timedelta(days=1)
    
    logger.info(f"⏰ 現在時刻: {now_jst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"📅 目標日付: {target_date}")
    
    # 最小限のデータ取得: 翌日8時から19時までの12時間分のみ
    tomorrow_8am = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=8)))
    tomorrow_7pm = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=19)))
    
    hours_to_8am = (tomorrow_8am - now_jst).total_seconds() / 3600
    
    # 計算ロジック
    if hours_to_8am > 0:
        # まだ翌日8時前なので、8時から19時までの12時間分
        forecast_hours = int(hours_to_8am) + 12
        logger.info(f"📊 翌日8時まで: {hours_to_8am:.1f}時間")
        logger.info(f"  → 取得時間: {forecast_hours}時間（翌日8時まで + 12時間）")
    else:
        # すでに翌日8時を過ぎているので、現在から19時まで
        hours_to_7pm = (tomorrow_7pm - now_jst).total_seconds() / 3600
        forecast_hours = max(int(hours_to_7pm) + 1, 1)
        logger.info(f"📊 翌日19時まで: {hours_to_7pm:.1f}時間")
        logger.info(f"  → 取得時間: {forecast_hours}時間（現在から翌日19時まで）")
    
    # APIリクエスト
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
        
        logger.info(f"📦 APIレスポンス:")
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
    
    # 翌日のデータのみを抽出
    tomorrow_data = [(date, hour) for (date, hour) in hourly_data.keys() if date == target_date]
    
    logger.info(f"\n📊 翌日のデータ分布:")
    for (date, hour) in sorted(tomorrow_data):
        count = len(hourly_data[(date, hour)])
        logger.info(f"  {hour:02d}時: {count}件")
    
    # 9,12,15,18時のデータのみをフィルタリング
    target_hours = [9, 12, 15, 18]
    filtered_forecasts = []
    
    logger.info(f"\n🎯 目標時刻のデータをフィルタリング:")
    for forecast in forecast_collection.forecasts:
        if (forecast.datetime.date() == target_date and 
            forecast.datetime.hour in target_hours):
            filtered_forecasts.append(forecast)
            logger.info(f"  ✅ {forecast.datetime.strftime('%Y-%m-%d %H:%M')} - {forecast.weather_description}")
    
    # フィルタリング結果を返す
    filtered_collection = WeatherForecastCollection(
        location=forecast_collection.location,
        forecasts=filtered_forecasts
    )
    
    # 効率性の評価
    original_count = len(forecast_collection.forecasts)
    filtered_count = len(filtered_forecasts)
    efficiency = (filtered_count / original_count * 100) if original_count > 0 else 0
    
    logger.info(f"\n📈 効率性評価:")
    logger.info(f"  取得データ数: {original_count}件")
    logger.info(f"  必要データ数: {filtered_count}件")
    logger.info(f"  データ効率: {efficiency:.1f}%")
    logger.info(f"  データ削減: {forecast_hours}/72時間 = {forecast_hours/72*100:.1f}%")
    
    return filtered_collection


def compare_all_approaches(api_key: str, lat: float, lon: float):
    """すべてのアプローチを比較"""
    logger.info("\n" + "=" * 80)
    logger.info("📊 すべてのアプローチの比較")
    logger.info("=" * 80)
    
    results = {}
    
    # 1. 現在の実装（翌日18時までのすべて）
    logger.info("\n1️⃣ 現在の実装")
    client = WxTechAPIClient(api_key)
    start = datetime.now()
    current_impl = client.get_forecast_for_next_day_hours(lat, lon)
    end = datetime.now()
    results["current"] = {
        "data_count": len(current_impl.forecasts),
        "time": (end - start).total_seconds(),
        "has_target_hours": check_target_hours(current_impl)
    }
    client.close()
    
    # 2. 最適化版（翌日8-19時のみ）
    logger.info("\n2️⃣ 最適化版")
    api = WxTechAPI(api_key)
    start = datetime.now()
    optimized_impl = get_forecast_for_next_day_hours_optimized(api, lat, lon)
    end = datetime.now()
    results["optimized"] = {
        "data_count": len(optimized_impl.forecasts),
        "time": (end - start).total_seconds(),
        "has_target_hours": check_target_hours(optimized_impl)
    }
    
    # 3. 72時間版（従来の実装）
    logger.info("\n3️⃣ 従来の72時間版")
    start = datetime.now()
    params = {"lat": lat, "lon": lon, "hours": 72}
    raw_data = api.make_request("ss1wx", params)
    full_collection = parse_forecast_response(raw_data, f"lat:{lat},lon:{lon}")
    end = datetime.now()
    results["full_72h"] = {
        "data_count": len(full_collection.forecasts),
        "time": (end - start).total_seconds(),
        "has_target_hours": check_target_hours(full_collection)
    }
    
    # 結果比較
    logger.info("\n" + "=" * 80)
    logger.info("📊 比較結果サマリー")
    logger.info("=" * 80)
    
    logger.info(f"\n{'実装':<15} {'データ数':<10} {'実行時間':<10} {'9,12,15,18時':<15}")
    logger.info("-" * 50)
    
    for impl_name, result in results.items():
        has_all = "✅ すべて有" if result["has_target_hours"]["all"] else "❌ 不足"
        logger.info(
            f"{impl_name:<15} {result['data_count']:<10} "
            f"{result['time']:.2f}秒{'':<4} {has_all:<15}"
        )
    
    # 効率性比較
    if results["full_72h"]["data_count"] > 0:
        logger.info(f"\n📈 データ削減率（72時間版と比較）:")
        for impl_name, result in results.items():
            if impl_name != "full_72h":
                reduction = (1 - result["data_count"] / results["full_72h"]["data_count"]) * 100
                logger.info(f"  {impl_name}: {reduction:.1f}%削減")


def check_target_hours(collection: WeatherForecastCollection) -> dict:
    """目標時刻のデータが含まれているかチェック"""
    jst = pytz.timezone("Asia/Tokyo")
    tomorrow = datetime.now(jst).date() + timedelta(days=1)
    target_hours = [9, 12, 15, 18]
    
    found_hours = set()
    for forecast in collection.forecasts:
        if forecast.datetime.date() == tomorrow:
            if forecast.datetime.hour in target_hours:
                found_hours.add(forecast.datetime.hour)
    
    return {
        "found": sorted(list(found_hours)),
        "missing": sorted([h for h in target_hours if h not in found_hours]),
        "all": len(found_hours) == len(target_hours)
    }


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
    
    logger.info("🚀 最適化された天気データ取得テスト開始")
    logger.info(f"📍 テスト地点: 東京 (緯度: {lat}, 経度: {lon})")
    
    # すべてのアプローチを比較
    compare_all_approaches(api_key, lat, lon)
    
    logger.info("\n✅ テスト完了")


if __name__ == "__main__":
    main()
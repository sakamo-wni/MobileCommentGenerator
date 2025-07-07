"""
WxTech API クライアント

高レベルのAPI操作インターフェースを提供
"""

from typing import Dict, Any, Optional, Type
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import pytz
from datetime import timedelta, datetime

from src.data.weather_data import WeatherForecastCollection
from src.data.location_manager import Location
from src.apis.wxtech.api import WxTechAPI
from src.apis.wxtech.parser import parse_forecast_response, analyze_response_patterns
from src.apis.wxtech.errors import WxTechAPIError

logger = logging.getLogger(__name__)


class WxTechAPIClient:
    """WxTech API クライアント
    
    天気予報データの取得・処理を行う高レベルインターフェース
    """
    
    def __init__(self, api_key: str, timeout: int = 30):
        """クライアントを初期化
        
        Args:
            api_key: WxTech API キー
            timeout: タイムアウト秒数（デフォルト: 30秒）
        """
        self.api = WxTechAPI(api_key, timeout)
    
    def get_forecast(self, lat: float, lon: float, forecast_hours: int = 72) -> WeatherForecastCollection:
        """指定座標の天気予報を取得
        
        Args:
            lat: 緯度
            lon: 経度
            forecast_hours: 予報時間数（デフォルト: 72時間）
            
        Returns:
            天気予報コレクション
            
        Raises:
            WxTechAPIError: API エラーが発生した場合
        """
        # パラメータ検証
        if not (-90 <= lat <= 90):
            raise ValueError(f"緯度が範囲外です: {lat} （-90～90の範囲で指定してください）")
        if not (-180 <= lon <= 180):
            raise ValueError(f"経度が範囲外です: {lon} （-180～180の範囲で指定してください）")
        if forecast_hours <= 0 or forecast_hours > 168:  # 最大7日間
            raise ValueError(f"予報時間数が範囲外です: {forecast_hours} （1-168時間の範囲で指定してください）")
        
        # API リクエスト実行
        params = {
            "lat": lat, 
            "lon": lon,
            "hours": forecast_hours
        }
        
        logger.info(f"🔄 WxTech API リクエスト: endpoint=ss1wx, params={params}")
        
        raw_data = self.api.make_request("ss1wx", params)
        
        # レスポンスの基本情報をログ出力
        if "wxdata" in raw_data and raw_data["wxdata"]:
            wxdata = raw_data["wxdata"][0]
            srf_count = len(wxdata.get("srf", []))
            mrf_count = len(wxdata.get("mrf", []))
            logger.info(f"📊 WxTech API レスポンス: srf={srf_count}件, mrf={mrf_count}件")
        
        # レスポンスデータの変換
        return parse_forecast_response(raw_data, f"lat:{lat},lon:{lon}")
    
    def get_forecast_by_location(self, location: Location) -> WeatherForecastCollection:
        """Location オブジェクトから天気予報を取得
        
        Args:
            location: 地点情報
            
        Returns:
            天気予報コレクション
            
        Raises:
            ValueError: 地点に緯度経度情報がない場合
            WxTechAPIError: API エラーが発生した場合
        """
        if location.latitude is None or location.longitude is None:
            raise ValueError(f"地点 '{location.name}' に緯度経度情報がありません")
        
        forecast_collection = self.get_forecast_for_next_day_hours(location.latitude, location.longitude)
        
        # 地点名を正しく設定
        forecast_collection.location = location.name
        for forecast in forecast_collection.forecasts:
            forecast.location = location.name
        
        return forecast_collection
    
    def get_forecast_for_next_day_hours(self, lat: float, lon: float) -> WeatherForecastCollection:
        """翌日の9, 12, 15, 18時JSTの最も近い時刻のデータのみを取得
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            翌日の最も近い時刻の天気予報コレクション
            
        Raises:
            WxTechAPIError: API エラーが発生した場合
        """
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        
        # 翌日の日付
        target_date = now_jst.date() + timedelta(days=1)
        
        # 翌日の9, 12, 15, 18時JSTの時刻を作成
        target_hours = [9, 12, 15, 18]
        target_times = []
        for hour in target_hours:
            target_dt = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=hour)))
            target_times.append(target_dt)
        
        # 現在時刻から各時刻までの時間を計算
        hours_to_targets = []
        for target_time in target_times:
            hours_diff = (target_time - now_jst).total_seconds() / 3600
            hours_to_targets.append(hours_diff)
        
        # 9時から18時までをカバーする最適化された取得
        # 最初の時刻（9時）から最後の時刻（18時）までの範囲のみ取得
        min_hours = min(hours_to_targets)  # 9時までの時間
        max_hours = max(hours_to_targets)  # 18時までの時間
        
        # 9時〜18時の範囲（9時間分）+ 前後1時間の余裕 = 11時間分のデータ
        range_hours = 11  # 8時〜19時の範囲
        
        # APIコール時は現在から18時過ぎまでの時間を指定
        forecast_hours = max(int(max_hours) + 1, 1)
        
        # ログ出力で各時刻を表示
        time_info = []
        for i, (hour, hours_after) in enumerate(zip(target_hours, hours_to_targets)):
            time_info.append(f"{hour}時({hours_after:.1f}h後)")
        
        logger.info(f"翌日の4時刻: {', '.join(time_info)}")
        logger.info(f"最適化: {forecast_hours}時間分のデータを取得（従来: 24-42時間）")
        
        # データを取得
        response_data = self.get_forecast(lat, lon, forecast_hours=forecast_hours)
        
        # 翌日の9-18時の範囲外のデータをフィルタリング
        filtered_forecasts = []
        start_time = target_times[0] - timedelta(hours=1)  # 8時
        end_time = target_times[-1] + timedelta(hours=1)   # 19時
        
        for forecast in response_data.forecasts:
            # forecast.datetimeがnaiveの場合はJSTとして扱う
            if forecast.datetime.tzinfo is None:
                forecast_time = jst.localize(forecast.datetime)
            else:
                forecast_time = forecast.datetime
            
            # 8時〜19時の範囲内のデータのみ保持
            if start_time <= forecast_time <= end_time:
                filtered_forecasts.append(forecast)
        
        # 新しいコレクションを作成
        collection = WeatherForecastCollection()
        collection.forecasts = filtered_forecasts
        collection.location = response_data.location
        
        logger.info(f"フィルタリング結果: {len(response_data.forecasts)}件 → {len(filtered_forecasts)}件")
        
        return collection
    
    def test_specific_time_parameters(self, lat: float, lon: float) -> Dict[str, Any]:
        """特定時刻指定パラメータのテスト
        
        様々なパラメータでWxTech APIをテストし、特定時刻指定が可能か検証する
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            テスト結果とレスポンスデータ
        """
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        
        # 翌日の9時のタイムスタンプを作成
        target_date = now_jst.date() + timedelta(days=1)
        target_dt = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=9)))
        target_timestamp = int(target_dt.timestamp())
        
        test_results = {}
        
        # テストパラメータのリスト
        test_params = [
            # 1. タイムスタンプ指定
            {
                "name": "timestamp",
                "params": {"lat": lat, "lon": lon, "timestamp": target_timestamp}
            },
            {
                "name": "timestamps", 
                "params": {"lat": lat, "lon": lon, "timestamps": str(target_timestamp)}
            },
            # 2. 開始・終了時刻指定
            {
                "name": "start_time",
                "params": {"lat": lat, "lon": lon, "start_time": target_timestamp}
            },
            {
                "name": "end_time",
                "params": {"lat": lat, "lon": lon, "start_time": target_timestamp, "end_time": target_timestamp + 3600}
            },
            # 3. 日時文字列指定
            {
                "name": "datetime",
                "params": {"lat": lat, "lon": lon, "datetime": target_dt.isoformat()}
            },
            {
                "name": "date_time",
                "params": {"lat": lat, "lon": lon, "date_time": target_dt.strftime("%Y-%m-%dT%H:%M:%S")}
            },
            # 4. 間隔指定
            {
                "name": "interval",
                "params": {"lat": lat, "lon": lon, "hours": 24, "interval": 3}
            },
            {
                "name": "step",
                "params": {"lat": lat, "lon": lon, "hours": 24, "step": 3}
            },
            # 5. 特定時刻リスト
            {
                "name": "times",
                "params": {"lat": lat, "lon": lon, "times": "9,12,15,18"}
            },
            {
                "name": "hours_list",
                "params": {"lat": lat, "lon": lon, "hours_list": "9,12,15,18"}
            }
        ]
        
        logger.info(f"🔍 WxTech API パラメータテスト開始 - ターゲット: {target_dt}")
        
        for test in test_params:
            try:
                logger.info(f"🧪 テスト: {test['name']} - {test['params']}")
                raw_data = self.api.make_request("ss1wx", test['params'])
                
                # 成功した場合のレスポンス解析
                if "wxdata" in raw_data and raw_data["wxdata"]:
                    wxdata = raw_data["wxdata"][0]
                    srf_count = len(wxdata.get("srf", []))
                    mrf_count = len(wxdata.get("mrf", []))
                    
                    test_results[test['name']] = {
                        "success": True,
                        "srf_count": srf_count,
                        "mrf_count": mrf_count,
                        "response_size": len(str(raw_data)),
                        "first_srf_date": wxdata.get("srf", [{}])[0].get("date") if srf_count > 0 else None
                    }
                    logger.info(f"✅ {test['name']}: 成功 - srf={srf_count}, mrf={mrf_count}")
                else:
                    test_results[test['name']] = {
                        "success": False,
                        "error": "空のレスポンス"
                    }
                    logger.warning(f"⚠️ {test['name']}: 空のレスポンス")
                    
            except WxTechAPIError as e:
                test_results[test['name']] = {
                    "success": False,
                    "error": str(e),
                    "error_type": e.error_type,
                    "status_code": e.status_code
                }
                logger.error(f"❌ {test['name']}: APIエラー - {e.error_type}: {e}")
                
            except Exception as e:
                test_results[test['name']] = {
                    "success": False,
                    "error": str(e),
                    "error_type": "unknown"
                }
                logger.error(f"❌ {test['name']}: 不明エラー - {e}")
        
        # テスト結果のサマリー
        successful_tests = [name for name, result in test_results.items() if result.get("success", False)]
        logger.info(f"📊 テスト結果サマリー: {len(successful_tests)}/{len(test_params)} 成功")
        
        if successful_tests:
            logger.info(f"✅ 成功したパラメータ: {', '.join(successful_tests)}")
        
        return {
            "target_datetime": target_dt.isoformat(),
            "target_timestamp": target_timestamp,
            "test_results": test_results,
            "successful_params": successful_tests,
            "total_tests": len(test_params),
            "successful_count": len(successful_tests)
        }
    
    def test_specific_times_only(self, lat: float, lon: float) -> Dict[str, Any]:
        """特定時刻のみのデータ取得テスト
        
        翌日の9,12,15,18時のみのデータが取得できるかテスト
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            テスト結果とレスポンスデータの詳細解析
        """
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        
        # 翌日の9, 12, 15, 18時JSTのタイムスタンプを作成
        target_date = now_jst.date() + timedelta(days=1)
        target_times = []
        target_timestamps = []
        
        for hour in [9, 12, 15, 18]:
            target_dt = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=hour)))
            target_times.append(target_dt)
            target_timestamps.append(int(target_dt.timestamp()))
        
        timestamps_str = ",".join(map(str, target_timestamps))
        
        logger.info(f"🔍 特定時刻のみテスト開始")
        logger.info(f"📅 ターゲット時刻: {[t.strftime('%H:%M') for t in target_times]}")
        logger.info(f"🔢 タイムスタンプ: {timestamps_str}")
        
        test_results = {}
        
        # 最も有望なパラメータをテスト
        promising_params = [
            {
                "name": "timestamps_specific",
                "params": {"lat": lat, "lon": lon, "timestamps": timestamps_str}
            },
            {
                "name": "times_specific", 
                "params": {"lat": lat, "lon": lon, "times": "9,12,15,18"}
            },
            {
                "name": "hours_list_specific",
                "params": {"lat": lat, "lon": lon, "hours_list": "9,12,15,18"}
            },
            {
                "name": "start_end_time",
                "params": {
                    "lat": lat, 
                    "lon": lon, 
                    "start_time": target_timestamps[0],
                    "end_time": target_timestamps[-1]
                }
            },
            {
                "name": "reference_hours_1",
                "params": {"lat": lat, "lon": lon, "hours": 1}
            },
            {
                "name": "reference_hours_4",
                "params": {"lat": lat, "lon": lon, "hours": 4}
            }
        ]
        
        for test in promising_params:
            try:
                logger.info(f"🧪 テスト: {test['name']}")
                raw_data = self.api.make_request("ss1wx", test['params'])
                
                if "wxdata" in raw_data and raw_data["wxdata"]:
                    wxdata = raw_data["wxdata"][0]
                    srf_data = wxdata.get("srf", [])
                    mrf_data = wxdata.get("mrf", [])
                    
                    # データの詳細解析
                    srf_times = [entry.get("date") for entry in srf_data[:10]]  # 最初の10件
                    mrf_times = [entry.get("date") for entry in mrf_data[:5]]   # 最初の5件
                    
                    test_results[test['name']] = {
                        "success": True,
                        "srf_count": len(srf_data),
                        "mrf_count": len(mrf_data),
                        "srf_sample_times": srf_times,
                        "mrf_sample_times": mrf_times,
                        "response_size": len(str(raw_data))
                    }
                    
                    logger.info(f"✅ {test['name']}: srf={len(srf_data)}, mrf={len(mrf_data)}")
                    logger.info(f"🕰️ 最初のsrf時刻: {srf_times[:3]}")
                    
                else:
                    test_results[test['name']] = {
                        "success": False,
                        "error": "空のレスポンス"
                    }
                    
            except Exception as e:
                test_results[test['name']] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"❌ {test['name']}: {e}")
        
        return {
            "target_times": [t.isoformat() for t in target_times],
            "target_timestamps": target_timestamps,
            "test_results": test_results,
            "analysis": analyze_response_patterns(test_results)
        }
    
    async def get_forecast_async(self, lat: float, lon: float, forecast_hours: int = 72) -> WeatherForecastCollection:
        """非同期で天気予報を取得
        
        Args:
            lat: 緯度
            lon: 経度
            forecast_hours: 予報時間数（デフォルト: 72時間）
            
        Returns:
            天気予報コレクション
        """
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.get_forecast, lat, lon, forecast_hours)
    
    def close(self):
        """セッションを閉じる"""
        self.api.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None:
        self.close()


# 既存の関数との互換性を保つためのラッパー関数
async def get_japan_1km_mesh_weather_forecast(
    lat: float, lon: float, api_key: str
) -> Dict[str, Any]:
    """既存の get_japan_1km_mesh_weather_forecast 関数の互換ラッパー
    
    Args:
        lat: 緯度
        lon: 経度
        api_key: WxTech API キー
        
    Returns:
        天気予報データの辞書
    """
    client = WxTechAPIClient(api_key)
    try:
        forecast_collection = await client.get_forecast_async(lat, lon, forecast_hours=72)
        return forecast_collection.to_dict()
    finally:
        client.close()
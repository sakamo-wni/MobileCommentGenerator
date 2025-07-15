"""
WxTech API パラメータテスト

特定時刻指定やパラメータの組み合わせをテストする
"""

import logging
import pytz
from datetime import timedelta, datetime
from typing import Any

from src.apis.wxtech.api import WxTechAPI
from src.apis.wxtech.errors import WxTechAPIError
from src.apis.wxtech.parser import analyze_response_patterns

logger = logging.getLogger(__name__)


class WxTechParameterTester:
    """WxTech API のパラメータをテストするクラス"""
    
    def __init__(self, api_key: str, timeout: int = 30):
        """テスターを初期化
        
        Args:
            api_key: WxTech API キー
            timeout: タイムアウト秒数（デフォルト: 30秒）
        """
        self.api = WxTechAPI(api_key, timeout)
    
    def test_specific_time_parameters(self, lat: float, lon: float) -> dict[str, Any]:
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
    
    def test_specific_times_only(self, lat: float, lon: float) -> dict[str, Any]:
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


if __name__ == "__main__":
    # APIキーを環境変数から取得
    import os
    api_key = os.environ.get("WXTECH_API_KEY", "your-test-api-key")
    
    # テスト実行
    tester = WxTechParameterTester(api_key)
    
    # 東京の座標でテスト
    tokyo_lat = 35.6762
    tokyo_lon = 139.6503
    
    print("=== 特定時刻パラメータテスト ===")
    result1 = tester.test_specific_time_parameters(tokyo_lat, tokyo_lon)
    print(f"成功: {result1['successful_count']}/{result1['total_tests']}")
    
    print("\n=== 特定時刻のみ取得テスト ===")
    result2 = tester.test_specific_times_only(tokyo_lat, tokyo_lon)
    print(f"テスト結果: {len(result2['test_results'])}件")
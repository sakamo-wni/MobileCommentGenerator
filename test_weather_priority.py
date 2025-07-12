#!/usr/bin/env python3
"""天気予報の優先度選択が正しく動作しているかテスト"""

import os
from datetime import datetime
from dotenv import load_dotenv

from src.workflows.comment_generation_workflow import run_comment_generation

# 環境変数をロード
load_dotenv()


def test_weather_priority():
    """天気予報の優先度選択をテスト"""
    print("=== 天気予報優先度選択テスト ===\n")
    
    # テスト実行
    result = run_comment_generation(
        location_name="東京",
        target_datetime=datetime.now(),
        llm_provider="gemini"
    )
    
    if result["success"]:
        print(f"✅ 成功")
        print(f"コメント: {result['final_comment']}")
        
        # メタデータから天気情報を取得
        metadata = result.get("generation_metadata", {})
        
        # 天気予報情報
        if "weather_condition" in metadata:
            print(f"\n選択された天気:")
            print(f"  天気: {metadata['weather_condition']}")
            print(f"  気温: {metadata.get('temperature', '不明')}°C")
            print(f"  降水量: {metadata.get('precipitation', '不明')}mm")
            print(f"  時刻: {metadata.get('forecast_time', '不明')}")
        
        # ノード実行時間
        if "node_execution_times" in metadata:
            print(f"\nノード実行時間:")
            for node, time_ms in metadata["node_execution_times"].items():
                print(f"  {node}: {time_ms:.2f}ms")
        
        # 天気予報取得の詳細
        if "weather_forecast_metadata" in metadata:
            weather_meta = metadata["weather_forecast_metadata"]
            print(f"\n天気予報取得の詳細:")
            print(f"  総予報数: {weather_meta.get('total_forecasts', 0)}")
            print(f"  APIキャッシュヒット: {weather_meta.get('api_cache_hit', False)}")
            
            # 翌日の9,12,15,18時のデータ
            if "period_forecasts" in weather_meta:
                print(f"\n翌日の時間別予報:")
                for hour, forecast in weather_meta["period_forecasts"].items():
                    print(f"  {hour}時: {forecast['weather_description']}, "
                          f"{forecast['temperature']}°C, "
                          f"降水量{forecast['precipitation']}mm")
            
            # 優先度選択の結果
            if "priority_selection" in weather_meta:
                priority = weather_meta["priority_selection"]
                print(f"\n優先度選択結果:")
                print(f"  選択理由: {priority.get('reason', '不明')}")
                print(f"  選択時刻: {priority.get('selected_hour', '不明')}時")
                
                # 他の候補
                if "candidates" in priority:
                    print(f"\n  他の候補:")
                    for candidate in priority["candidates"]:
                        print(f"    {candidate['hour']}時: {candidate['weather']}, "
                              f"{candidate['temperature']}°C, "
                              f"降水量{candidate['precipitation']}mm")
        
    else:
        print(f"❌ エラー: {result.get('error', '不明')}")


if __name__ == "__main__":
    test_weather_priority()
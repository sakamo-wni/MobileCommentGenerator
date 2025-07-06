#!/usr/bin/env python3
"""
WxTech API特定時刻指定パラメータのテストスクリプト

様々なパラメータでWxTech APIをテストし、特定時刻指定が可能かを検証する
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

from src.apis.wxtech_client import WxTechAPIClient, WxTechAPIError

# 環境変数をロード
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """WxTech APIパラメータテストのメイン関数"""
    
    # APIキーの確認
    api_key = os.getenv("WXTECH_API_KEY")
    if not api_key:
        logger.error("WXTECH_API_KEY環境変数が設定されていません")
        return
    
    # テスト用の座標（東京）
    lat, lon = 35.6762, 139.6503
    
    logger.info("🚀 WxTech API特定時刻指定パラメータテスト開始")
    logger.info(f"📍 テスト座標: ({lat}, {lon})")
    logger.info(f"🕐 実行時刻: {datetime.now()}")
    
    try:
        # WxTech APIクライアントの作成
        client = WxTechAPIClient(api_key)
        
        # 特定時刻指定パラメータのテスト実行
        test_results = client.test_specific_time_parameters(lat, lon)
        
        # 詳細テストも実行
        detailed_results = client.test_specific_times_only(lat, lon)
        
        # 結果の詳細表示
        print("\n" + "="*80)
        print("🔍 WxTech API特定時刻指定パラメータテスト結果")
        print("="*80)
        
        print(f"📅 ターゲット日時: {test_results['target_datetime']}")
        print(f"🔢 ターゲットタイムスタンプ: {test_results['target_timestamp']}")
        print(f"📊 総テスト数: {test_results['total_tests']}")
        print(f"✅ 成功数: {test_results['successful_count']}")
        print(f"🎯 成功率: {test_results['successful_count']/test_results['total_tests']*100:.1f}%")
        
        if test_results['successful_params']:
            print(f"\n🎉 成功したパラメータ:")
            for param_name in test_results['successful_params']:
                result = test_results['test_results'][param_name]
                print(f"  ✅ {param_name}: srf={result.get('srf_count', 0)}, mrf={result.get('mrf_count', 0)}")
                if result.get('first_srf_date'):
                    print(f"     📆 最初のデータ日時: {result['first_srf_date']}")
        
        print(f"\n❌ 失敗したパラメータ:")
        for param_name, result in test_results['test_results'].items():
            if not result.get('success', False):
                error_info = f"{result.get('error_type', 'unknown')}: {result.get('error', 'unknown error')}"
                print(f"  ❌ {param_name}: {error_info}")
        
        # 結果をJSONファイルに保存
        output_file = f"wxtech_api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 詳細結果を保存: {output_file}")
        
        # 詳細テスト結果を表示
        print(f"\n" + "="*80)
        print(f"🔍 詳細分析: 特定時刻データのみ取得テスト")
        print(f"="*80)
        
        analysis = detailed_results['analysis']
        print(f"📊 データサイズのバリエーション:")
        print(f"  SRFカウント: {analysis['unique_srf_counts']}")
        print(f"  MRFカウント: {analysis['unique_mrf_counts']}")
        print(f"  レスポンスサイズ: {analysis['unique_response_sizes']}")
        
        if analysis['minimum_data_response']:
            min_resp = analysis['minimum_data_response']
            print(f"\n🎆 最小データレスポンス: {min_resp['name']}")
            print(f"  SRF: {min_resp['srf_count']}, MRF: {min_resp['mrf_count']}")
            
        if analysis['appears_time_specific']:
            print(f"\n✨ 結論: 特定時刻指定が機能している可能性があります！")
            print(f"   異なるデータサイズが確認されました。")
        else:
            print(f"\n😔 結論: すべてのパラメータが同じデータサイズを返しています。")
            print(f"   特定時刻指定は機能していない可能性があります。")
            print(f"   現在の実装（hoursパラメータ + クライアント側フィルタリング）が最適です。")
        
        # 詳細結果も保存
        detailed_output_file = f"wxtech_api_detailed_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(detailed_output_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 詳細テスト結果を保存: {detailed_output_file}")
    
    except WxTechAPIError as e:
        logger.error(f"WxTech APIエラー: {e}")
        print(f"❌ APIエラー: {e}")
        
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        print(f"❌ エラー: {e}")
    
    finally:
        print(f"\n🏁 テスト完了")

if __name__ == "__main__":
    main()
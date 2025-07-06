#!/usr/bin/env python3
"""
WxTech API詳細テストスクリプト

特定時刻のデータのみが取得できるかを詳細にテストする
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
    """詳細テストのメイン関数"""
    
    # APIキーの確認
    api_key = os.getenv("WXTECH_API_KEY")
    if not api_key:
        logger.error("WXTECH_API_KEY環境変数が設定されていません")
        return
    
    # テスト用の座標（東京）
    lat, lon = 35.6762, 139.6503
    
    logger.info("🚀 WxTech API詳細テスト開始")
    logger.info(f"📍 テスト座標: ({lat}, {lon})")
    logger.info(f"🕐 実行時刻: {datetime.now()}")
    
    try:
        client = WxTechAPIClient(api_key)
        
        # 詳細テスト実行
        detailed_results = client.test_specific_times_only(lat, lon)
        
        # 結果の詳細表示
        print("\n" + "="*80)
        print("🔍 WxTech API 特定時刻データのみ取得テスト結果")
        print("="*80)
        
        print(f"📅 ターゲット時刻: {[t.split('T')[1][:5] for t in detailed_results['target_times']]}")
        print(f"🔢 タイムスタンプ: {detailed_results['target_timestamps']}")
        
        # 各テスト結果を表示
        print(f"\n📊 テスト結果:")
        for name, result in detailed_results['test_results'].items():
            if result.get('success'):
                print(f"  ✅ {name}: SRF={result['srf_count']}, MRF={result['mrf_count']}")
                if result.get('srf_sample_times'):
                    sample_times = [t.split('T')[1][:5] if 'T' in t else t for t in result['srf_sample_times'][:3]]
                    print(f"     🕐 サンプル時刻: {sample_times}")
            else:
                print(f"  ❌ {name}: {result.get('error', 'エラー')}")
        
        # 分析結果
        analysis = detailed_results['analysis']
        print(f"\n📈 分析結果:")
        print(f"  SRFカウントの種類: {analysis['unique_srf_counts']}")
        print(f"  MRFカウントの種類: {analysis['unique_mrf_counts']}")
        print(f"  レスポンスサイズの種類: {analysis['unique_response_sizes']}")
        
        if analysis['minimum_data_response']:
            min_resp = analysis['minimum_data_response']
            print(f"\n🎯 最小データレスポンス: {min_resp['name']}")
            print(f"  SRF: {min_resp['srf_count']}, MRF: {min_resp['mrf_count']}")
        
        # 結論
        if analysis['appears_time_specific']:
            print(f"\n✨ 結論: 特定時刻指定が機能している可能性があります！")
            print(f"   異なるデータサイズが確認されました。")
        else:
            print(f"\n😔 結論: すべてのパラメータが同じデータサイズを返しています。")
            print(f"   特定時刻指定は機能していない可能性があります。")
            print(f"   現在の実装（hoursパラメータ + クライアント側フィルタリング）が最適です。")
        
        # 結果をJSONファイルに保存
        output_file = f"wxtech_detailed_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 詳細テスト結果を保存: {output_file}")
    
    except WxTechAPIError as e:
        logger.error(f"WxTech APIエラー: {e}")
        print(f"❌ APIエラー: {e}")
        
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        print(f"❌ エラー: {e}")
    
    finally:
        print(f"\n🏁 詳細テスト完了")

if __name__ == "__main__":
    main()
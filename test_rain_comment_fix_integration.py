#!/usr/bin/env python3
"""雨天時の「梅雨の中休み」問題の統合テスト"""

import sys
import os
import requests
import json
from datetime import datetime

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_api_with_rainy_weather():
    """APIサーバーを使った雨天時のテスト"""
    print("🚨 APIサーバー経由での雨天時テストを開始")
    
    # APIエンドポイント
    api_url = "http://localhost:8000/api/generate"
    
    # 雨天時の条件でテスト
    test_data = {
        "location": "東京",
        "llm_provider": "openai",
        "target_datetime": datetime.now().isoformat()
    }
    
    print(f"テスト条件:")
    print(f"  地点: {test_data['location']}")
    print(f"  LLMプロバイダー: {test_data['llm_provider']}")
    print(f"  対象日時: {test_data['target_datetime']}")
    print("  ※実際の天気データはWxTech APIから取得されます")
    
    try:
        # APIリクエスト送信
        response = requests.post(api_url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ API呼び出し成功")
            
            # 結果の分析
            if result.get('success') and 'comment' in result:
                comment = result.get('comment', '')
                metadata = result.get('metadata', {})
                
                print(f"\n📝 生成されたコメント:")
                print(f"  コメント: '{comment}'")
                
                if metadata:
                    print(f"  天気条件: {metadata.get('weather_condition', 'N/A')}")
                    print(f"  気温: {metadata.get('temperature', 'N/A')}°C")
                    print(f"  天気コメント: '{metadata.get('selected_weather_comment', 'N/A')}'")
                    print(f"  アドバイス: '{metadata.get('selected_advice_comment', 'N/A')}'")
                
                # 問題となった表現が含まれていないかチェック
                prohibited_phrases = [
                    "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み",
                    "梅雨明け", "からっと", "さっぱり"
                ]
                
                # コメント全体と個別コメントの両方をチェック
                full_text = comment
                if metadata:
                    full_text += " " + metadata.get('selected_weather_comment', '')
                    full_text += " " + metadata.get('selected_advice_comment', '')
                
                issues_found = []
                for phrase in prohibited_phrases:
                    if phrase in full_text:
                        issues_found.append(phrase)
                
                if issues_found:
                    print(f"\n❌ 問題発見: 以下の不適切な表現が含まれています:")
                    for issue in issues_found:
                        print(f"    - '{issue}'")
                    return False
                else:
                    print(f"\n✅ 問題なし: 禁止表現は含まれていません")
                    
                    # 適切なキーワードが選択されているかチェック
                    good_keywords = ["雨", "注意", "傘", "濡れ", "警戒", "安全", "室内"]
                    found_keywords = []
                    for keyword in good_keywords:
                        if keyword in full_text:
                            found_keywords.append(keyword)
                    
                    if found_keywords:
                        print(f"✅ 適切なキーワード検出: {', '.join(found_keywords)}")
                    else:
                        print(f"ℹ️  天気に応じたキーワードを確認中...")
                    
                    return True
            else:
                error = result.get('error', 'Unknown error')
                print(f"❌ コメント生成失敗: {error}")
                return False
                
        else:
            print(f"❌ APIエラー: Status {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ APIサーバーに接続できません。サーバーが起動していることを確認してください。")
        print("💡 サーバー起動コマンド: python api_server.py")
        return False
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False

def test_multiple_weather_conditions():
    """複数の地点でのテスト（実際の気象データ使用）"""
    print("\n🌤️ 複数の地点でのテスト")
    
    test_locations = [
        {"name": "東京", "location": "東京"},
        {"name": "神戸", "location": "神戸"},
        {"name": "大阪", "location": "大阪"}
    ]
    
    api_url = "http://localhost:8000/api/generate"
    results = []
    
    for location_info in test_locations:
        print(f"\n--- {location_info['name']} ---")
        
        test_data = {
            "location": location_info['location'],
            "llm_provider": "openai",
            "target_datetime": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(api_url, json=test_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and 'comment' in result:
                    comment = result.get('comment', '')
                    metadata = result.get('metadata', {})
                    
                    print(f"生成されたコメント: '{comment}'")
                    if metadata:
                        print(f"天気条件: {metadata.get('weather_condition', 'N/A')}")
                        print(f"気温: {metadata.get('temperature', 'N/A')}°C")
                    
                    # 矛盾チェック
                    prohibited = ["中休み", "晴れ間", "梅雨の中休み", "回復", "一時的な晴れ"]
                    has_issue = any(phrase in comment for phrase in prohibited)
                    
                    if has_issue:
                        print("❌ 不適切な表現が検出されました")
                        print(f"   問題のある表現: {[p for p in prohibited if p in comment]}")
                        results.append(False)
                    else:
                        print("✅ 問題なし")
                        results.append(True)
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"❌ コメント生成失敗: {error}")
                    results.append(False)
            else:
                print(f"❌ API エラー: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 テスト結果: {len([r for r in results if r])}/{len(results)} 成功 ({success_rate:.1f}%)")
    
    return all(results)

if __name__ == "__main__":
    print("🧪 雨天時の「梅雨の中休み」問題修正の統合テスト")
    print("=" * 50)
    
    # 基本テスト
    basic_test_passed = test_api_with_rainy_weather()
    
    # 複数条件テスト
    multi_test_passed = test_multiple_weather_conditions()
    
    print("\n" + "=" * 50)
    if basic_test_passed and multi_test_passed:
        print("🎉 すべてのテストが成功しました！修正が正しく動作しています。")
    else:
        print("⚠️  一部のテストが失敗しました。さらなる調整が必要な可能性があります。")
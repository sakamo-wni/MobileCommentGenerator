#!/usr/bin/env python3
"""API統合テストスクリプト"""

import requests
import json

def test_api():
    """APIの基本機能をテスト"""
    base_url = "http://localhost:8000"
    
    print("=== API統合テスト ===")
    
    # ヘルスチェック
    print("\n1. ヘルスチェック")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ ステータス: {response.status_code}")
        print(f"   レスポンス: {response.json()}")
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    
    # 地点一覧取得
    print("\n2. 地点一覧取得")
    try:
        response = requests.get(f"{base_url}/api/locations")
        locations = response.json()['locations']
        print(f"✅ {len(locations)} 件の地点を取得")
        print(f"   例: {locations[:5]}")
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    
    # プロバイダー一覧取得
    print("\n3. LLMプロバイダー一覧取得")
    try:
        response = requests.get(f"{base_url}/api/providers")
        providers = response.json()['providers']
        print(f"✅ {len(providers)} 件のプロバイダーを取得")
        for p in providers:
            print(f"   - {p['id']}: {p['name']}")
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    
    print("\n✅ すべてのAPIテストが成功しました！")
    return True

if __name__ == "__main__":
    import sys
    success = test_api()
    sys.exit(0 if success else 1)
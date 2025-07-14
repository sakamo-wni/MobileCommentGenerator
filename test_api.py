#!/usr/bin/env python3
"""APIの動作確認スクリプト"""

import requests
import json

def test_api():
    # ヘルスチェック
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health Check: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return
    
    # コメント生成（高速化オプション付き）
    try:
        data = {
            "location": "東京",
            "use_parallel_mode": True,
            "use_unified_mode": True,
            "use_indexed_csv": True
        }
        
        print("\n=== Testing comment generation with performance options ===")
        print(f"Request: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            "http://localhost:8000/api/comments/generate",
            json=data,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', False)}")
            print(f"Comment: {result.get('comment', 'N/A')}")
            print(f"Execution Time: {result.get('metadata', {}).get('execution_time', 'N/A')}秒")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error during comment generation: {e}")

if __name__ == "__main__":
    test_api()
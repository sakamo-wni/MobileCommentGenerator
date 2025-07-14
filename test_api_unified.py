"""APIの動作確認テスト（統一ワークフロー版）"""

import requests
import json
import time

def test_api():
    """APIが正常に動作するか確認"""
    url = "http://localhost:8000/generate/comment"
    
    payload = {
        "location": "東京",
        "llm_provider": "gemini",
        "exclude_previous": False
    }
    
    print("APIテスト開始...")
    print(f"リクエスト: {json.dumps(payload, ensure_ascii=False)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload)
        elapsed_time = time.time() - start_time
        
        response.raise_for_status()
        result = response.json()
        
        print(f"\n✅ APIテスト成功！")
        print(f"実行時間: {elapsed_time:.2f}秒")
        print(f"ステータスコード: {response.status_code}")
        print(f"成功: {result.get('success')}")
        print(f"コメント: {result.get('comment', '')}")
        print(f"アドバイス: {result.get('advice_comment', '')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ APIテスト失敗")
        print(f"実行時間: {elapsed_time:.2f}秒")
        print(f"エラー: {e}")
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"エラー詳細: {json.dumps(error_detail, ensure_ascii=False, indent=2)}")
            except:
                print(f"レスポンス: {e.response.text}")
        
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("APIテスト（並列処理ワークフロー統一版）")
    print("=" * 50)
    
    if test_api():
        print("\n✅ 並列処理ワークフローが正常に動作しています")
    else:
        print("\n❌ エラーが発生しました")
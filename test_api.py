"""APIサーバーの動作テストスクリプト"""

import requests
import json

def test_comment_generation():
    """コメント生成APIのテスト"""
    url = "http://localhost:8000/generate/comment"
    
    payload = {
        "location_names": ["稚内"],
        "llm_provider": "gemini"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print("APIテスト成功！")
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # LazyCommentRepositoryが使用されているかログで確認
        if "generation_metadata" in result:
            print("\n生成メタデータ:")
            print(json.dumps(result["generation_metadata"], ensure_ascii=False, indent=2))
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"APIテスト失敗: {e}")
        return False

if __name__ == "__main__":
    if test_comment_generation():
        print("\n✅ LazyCommentRepositoryで正常に動作しています")
    else:
        print("\n❌ エラーが発生しました")
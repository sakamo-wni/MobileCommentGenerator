#!/usr/bin/env python3
"""連続雨時のにわか雨フィルタリングテスト"""

import asyncio
import json
from datetime import datetime
import pytz

# リクエストデータを準備
request_data = {
    "location": {
        "name": "東京都千代田区",
        "latitude": 35.689487,
        "longitude": 139.691706
    },
    "target_datetime": datetime.now(pytz.timezone("Asia/Tokyo")).isoformat(),
    "use_unified_mode": True  # 統一モードを使用
}

async def test_shower_rain_filtering():
    """連続雨時のフィルタリングをテスト"""
    from api_server import generate_comment
    
    print("連続雨時のコメント生成テスト開始...")
    print(f"リクエストデータ: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
    
    # APIを呼び出し
    result = await generate_comment(request_data)
    
    print("\n結果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # コメントに「にわか雨」が含まれていないことを確認
    if "にわか雨" in result.get("final_comment", ""):
        print("\n❌ エラー: 連続雨時にも関わらず「にわか雨」が含まれています")
    else:
        print("\n✅ 成功: 「にわか雨」が含まれていません")
    
    # メタデータを確認
    metadata = result.get("metadata", {})
    if metadata.get("is_continuous_rain"):
        print("✅ 連続雨が正しく検出されました")
    else:
        print("⚠️ 連続雨が検出されませんでした")

if __name__ == "__main__":
    asyncio.run(test_shower_rain_filtering())
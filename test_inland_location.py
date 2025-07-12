#!/usr/bin/env python3
"""内陸地域でのコメント生成テスト"""

import os
from datetime import datetime
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

from src.workflows.comment_generation_workflow import run_comment_generation


def test_inland_locations():
    """内陸地域でのテスト"""
    print("=== 内陸地域コメント生成テスト ===\n")
    
    # 内陸地域のリスト
    inland_locations = ["京都", "長野", "奈良", "岐阜"]
    
    for location in inland_locations:
        print(f"\n{location}のテスト:")
        result = run_comment_generation(
            location_name=location,
            target_datetime=datetime.now(),
            llm_provider="gemini"
        )
        
        if result["success"]:
            comment = result['final_comment']
            metadata = result.get("generation_metadata", {})
            
            print(f"  天気: {metadata.get('weather_condition', '不明')}")
            print(f"  気温: {metadata.get('temperature', '不明')}°C")
            print(f"  コメント: {comment}")
            
            # 海岸関連キーワードをチェック
            coastal_keywords = ["海", "波", "沿岸", "高波", "しけ", "磯", "浜"]
            found_keywords = [kw for kw in coastal_keywords if kw in comment]
            
            if found_keywords:
                print(f"  ⚠️  海岸関連キーワード検出: {found_keywords}")
            else:
                print(f"  ✅ 海岸関連キーワードなし")
                
            # 天気回復表現をチェック
            recovery_phrases = ["天気回復へ", "回復へ", "回復傾向"]
            found_recovery = [phrase for phrase in recovery_phrases if phrase in comment]
            
            if found_recovery:
                print(f"  ⚠️  天気回復表現検出: {found_recovery}")
        else:
            print(f"  ❌ エラー: {result.get('error', '不明')}")


if __name__ == "__main__":
    test_inland_locations()
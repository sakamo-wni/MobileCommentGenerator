#!/usr/bin/env python3
"""
重複除去機能のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.comment_deduplicator import CommentDeduplicator, deduplicate_final_comment


def test_deduplication():
    """重複除去のテスト"""
    
    test_cases = [
        {
            "name": "熱中症の完全重複",
            "weather": "熱中症に警戒",
            "advice": "熱中症に注意",
            "expected": "異なるコメントになること"
        },
        {
            "name": "熱中症の部分重複",
            "weather": "今日は熱中症に警戒",
            "advice": "外出時は熱中症に注意",
            "expected": "アドバイスが変更されること"
        },
        {
            "name": "雨関連の重複",
            "weather": "雨に注意",
            "advice": "傘をお忘れなく",
            "expected": "重複なし（異なる表現なのでOK）"
        },
        {
            "name": "雨の完全重複",
            "weather": "雨に注意",
            "advice": "雨に注意",
            "expected": "アドバイスが変更されること"
        },
        {
            "name": "異なるテーマ",
            "weather": "晴れて暑い一日",
            "advice": "紫外線対策を忘れずに",
            "expected": "変更なし"
        },
        {
            "name": "風の重複",
            "weather": "強風に注意",
            "advice": "風に注意して",
            "expected": "アドバイスが変更されること"
        },
        {
            "name": "寒さの重複",
            "weather": "寒さ対策を",
            "advice": "防寒対策をしっかりと",
            "expected": "アドバイスが変更されること"
        }
    ]
    
    print("=== コメント重複除去テスト ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"テスト{i}: {test_case['name']}")
        print(f"  入力:")
        print(f"    天気: {test_case['weather']}")
        print(f"    アドバイス: {test_case['advice']}")
        
        # 重複除去実行
        deduplicated_weather, deduplicated_advice = CommentDeduplicator.deduplicate_comment(
            test_case['weather'], test_case['advice']
        )
        
        print(f"  出力:")
        print(f"    天気: {deduplicated_weather}")
        print(f"    アドバイス: {deduplicated_advice}")
        print(f"  期待される結果: {test_case['expected']}")
        
        # 変更があったかチェック
        if deduplicated_weather != test_case['weather'] or deduplicated_advice != test_case['advice']:
            print(f"  結果: ✓ 重複が除去されました")
        else:
            print(f"  結果: - 変更なし")
        
        print()
    
    # 結合済みコメントのテスト
    print("=== 結合済みコメントの重複除去テスト ===\n")
    
    combined_test_cases = [
        {
            "name": "熱中症の重複",
            "comment": "熱中症に警戒　熱中症に注意",
            "expected": "重複が除去される"
        },
        {
            "name": "正常なコメント",
            "comment": "晴れて暑い一日　水分補給を忘れずに",
            "expected": "変更なし"
        },
        {
            "name": "雨の重複",
            "comment": "雨に注意　雨に警戒",
            "expected": "重複が除去される"
        }
    ]
    
    for i, test_case in enumerate(combined_test_cases, 1):
        print(f"テスト{i}: {test_case['name']}")
        print(f"  入力: {test_case['comment']}")
        
        deduplicated = deduplicate_final_comment(test_case['comment'])
        
        print(f"  出力: {deduplicated}")
        print(f"  期待される結果: {test_case['expected']}")
        
        if deduplicated != test_case['comment']:
            print(f"  結果: ✓ 重複が除去されました")
        else:
            print(f"  結果: - 変更なし")
        
        print()


if __name__ == "__main__":
    test_deduplication()
#!/usr/bin/env python3
"""季節別コメント取得のテストスクリプト"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from src.repositories.local_comment_repository import LocalCommentRepository


def test_seasonal_comment_selection():
    """季節別コメント選択のテスト"""
    
    try:
        repository = LocalCommentRepository()
        
        # 異なる月でのテスト
        test_months = [3, 6, 9, 12]  # 春、梅雨、台風、冬
        
        for month in test_months:
            print(f"\n📅 {month}月のテスト:")
            
            # 月を一時的に変更して関連季節を取得
            relevant_seasons = repository._get_relevant_seasons(month)
            print(f"  関連季節: {relevant_seasons}")
            
            # その月での期待取得件数を計算
            expected_total = len(relevant_seasons) * 100  # 各季節100件ずつ
            print(f"  期待取得数: {expected_total}件 (各季節100件 × {len(relevant_seasons)}季節)")
    
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()


def test_current_month_comments():
    """現在月でのコメント取得テスト"""
    
    try:
        repository = LocalCommentRepository()
        
        print("🗓️ 現在月でのコメント取得テスト:")
        current_month = datetime.now().month
        print(f"現在月: {current_month}月")
        
        # コメント取得
        comments = repository.get_recent_comments(limit=200)  # 多めに取得
        
        print(f"取得コメント数: {len(comments)}件")
        
        # 季節別の内訳を表示
        season_counts = {}
        for comment in comments:
            season = comment.raw_data.get('season', '不明')
            season_counts[season] = season_counts.get(season, 0) + 1
        
        print("季節別内訳:")
        for season, count in sorted(season_counts.items()):
            print(f"  {season}: {count}件")
        
        # タイプ別の内訳も表示
        type_counts = {}
        for comment in comments:
            comment_type = comment.comment_type.value
            type_counts[comment_type] = type_counts.get(comment_type, 0) + 1
        
        print("タイプ別内訳:")
        for type_name, count in sorted(type_counts.items()):
            print(f"  {type_name}: {count}件")
        
        # サンプルコメントを表示
        print("\n📝 サンプルコメント（上位5件）:")
        for i, comment in enumerate(comments[:5], 1):
            season = comment.raw_data.get('season', '不明')
            count = comment.raw_data.get('count', 0)
            print(f"  {i}. [{season}] {comment.comment_text} (使用回数: {count})")
    
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()


def main():
    """メインテスト実行"""
    print("🧪 季節別コメント取得システムテスト開始\n")
    
    test_seasonal_comment_selection()
    test_current_month_comments()
    
    print("\n✅ テスト完了")


if __name__ == "__main__":
    main()
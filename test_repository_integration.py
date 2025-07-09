#!/usr/bin/env python3
"""リポジトリ統合のテストスクリプト"""

import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.repositories.local_comment_repository import LocalCommentRepository

def test_basic_functionality():
    """基本的な機能をテスト"""
    print("=== LocalCommentRepository 基本機能テスト ===")
    
    # 通常のキャッシュベース実装
    print("\n1. 通常のキャッシュベース実装のテスト")
    try:
        repo_normal = LocalCommentRepository(use_index=False)
        comments = repo_normal.get_recent_comments(limit=10)
        print(f"✅ 通常実装: {len(comments)} 件のコメントを取得")
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    
    # インデックスベース実装
    print("\n2. インデックスベース実装のテスト")
    try:
        repo_indexed = LocalCommentRepository(use_index=True)
        comments = repo_indexed.get_recent_comments(limit=10)
        print(f"✅ インデックス実装: {len(comments)} 件のコメントを取得")
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    
    # get_all_available_commentsのテスト
    print("\n3. get_all_available_comments メソッドのテスト")
    try:
        # 通常実装
        all_comments_normal = repo_normal.get_all_available_comments(max_per_season_per_type=5)
        print(f"✅ 通常実装: {len(all_comments_normal)} 件の全コメントを取得")
        
        # インデックス実装
        all_comments_indexed = repo_indexed.get_all_available_comments(max_per_season_per_type=5)
        print(f"✅ インデックス実装: {len(all_comments_indexed)} 件の全コメントを取得")
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    
    print("\n✅ すべてのテストが成功しました！")
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
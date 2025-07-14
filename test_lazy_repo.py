"""LazyCommentRepositoryの動作確認テスト"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.repositories.lazy_comment_repository import LazyCommentRepository

def test_lazy_repository():
    """LazyCommentRepositoryが正常に動作するか確認"""
    try:
        print("LazyCommentRepositoryを初期化中...")
        repository = LazyCommentRepository()
        
        print("過去コメントを取得中...")
        comments = repository.get_recent_comments(limit=10)
        
        print(f"✅ 成功！ {len(comments)}件のコメントを取得しました")
        
        if comments:
            print(f"\n最初のコメント: {comments[0].comment_text[:50]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_lazy_repository():
        print("\n✅ LazyCommentRepositoryは正常に動作しています")
    else:
        print("\n❌ LazyCommentRepositoryの動作に問題があります")
"""遅延読み込みのデバッグスクリプト"""

import logging
from src.repositories.lazy_comment_repository import LazyCommentRepository
from src.data.past_comment import CommentType

# ログレベルを設定
logging.basicConfig(level=logging.DEBUG)

def debug_lazy_loading():
    """遅延読み込みの動作をデバッグ"""
    print("=== 遅延読み込みデバッグ ===\n")
    
    # リポジトリを作成
    repo = LazyCommentRepository()
    
    # 統計情報を確認
    print("1. 初期状態:")
    stats = repo.get_statistics()
    print(f"  読み込み済みファイル: {stats['loaded_files']}")
    print(f"  利用可能な季節: {repo.SEASONS}")
    print(f"  利用可能なタイプ: {repo.COMMENT_TYPES}")
    
    # get_recent_commentsをテスト
    print("\n2. get_recent_comments()を実行:")
    recent = repo.get_recent_comments(limit=10)
    print(f"  取得されたコメント数: {len(recent)}")
    
    if recent:
        print("  最初のコメント:")
        comment = recent[0]
        print(f"    テキスト: {comment.comment_text[:30]}...")
        print(f"    タイプ: {comment.comment_type}")
        print(f"    raw_data: {comment.raw_data}")
    
    # 統計情報を再確認
    stats = repo.get_statistics()
    print(f"\n  読み込み済みファイル数: {stats['loaded_files']}")
    print(f"  読み込み詳細: {stats['loaded_details']}")
    
    # 春のデータだけを取得
    print("\n3. 春のデータのみ取得:")
    spring_comments = repo.get_comments_by_season("春")
    print(f"  春のコメント数: {len(spring_comments)}")
    
    # ファイルパスを確認
    print("\n4. ファイルパスの確認:")
    for season in ["春"]:
        for comment_type in repo.COMMENT_TYPES:
            file_path = repo._get_csv_file_path(season, comment_type)
            print(f"  {file_path}: 存在={file_path.exists()}")
    
    # 直接ファイルを読み込んでみる
    print("\n5. 直接ファイル読み込みテスト:")
    test_path = repo._get_csv_file_path("春", "weather_comment")
    if test_path.exists():
        comments = repo._load_comments_from_file(test_path, "weather_comment", "春")
        print(f"  春の天気コメント数: {len(comments)}")
        if comments:
            print(f"  最初のコメント: {comments[0].comment_text[:30]}...")

if __name__ == "__main__":
    debug_lazy_loading()
"""Test lazy CSV loading directly"""

from src.repositories.lazy_comment_repository import LazyCommentRepository

def test_lazy_loading():
    """Test LazyCommentRepository directly"""
    print("=== Testing LazyCommentRepository ===\n")
    
    # Create repository
    repo = LazyCommentRepository()
    
    # Test getting recent comments
    print("1. Testing get_recent_comments():")
    try:
        comments = repo.get_recent_comments(limit=10)
        print(f"   Found {len(comments)} comments")
        if comments:
            print(f"   First comment: {comments[0].comment_text[:50]}...")
        else:
            print("   No comments found!")
    except Exception as e:
        print(f"   Error: {type(e).__name__}: {str(e)}")
    
    # Check statistics
    print("\n2. Repository statistics:")
    stats = repo.get_statistics()
    print(f"   Loaded files: {stats['loaded_files']}")
    print(f"   Cache stats: {stats['cache_stats']}")
    
    # Test loading specific season
    print("\n3. Testing get_comments_by_season('春'):")
    try:
        spring_comments = repo.get_comments_by_season('春', limit=5)
        print(f"   Found {len(spring_comments)} spring comments")
    except Exception as e:
        print(f"   Error: {type(e).__name__}: {str(e)}")
    
    # Check what files it's looking for
    print("\n4. Expected file paths:")
    for season in repo.SEASONS[:2]:  # Just show first 2
        for comment_type in repo.COMMENT_TYPES:
            path = repo._get_csv_file_path(season, comment_type)
            exists = path.exists()
            print(f"   {path}: {'EXISTS' if exists else 'NOT FOUND'}")

if __name__ == "__main__":
    test_lazy_loading()
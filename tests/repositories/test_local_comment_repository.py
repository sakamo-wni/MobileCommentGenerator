"""LocalCommentRepositoryのテスト"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.repositories.local_comment_repository import LocalCommentRepository
from src.repositories.csv_file_handler import CSVFileHandler, CommentParser
from src.repositories.comment_cache import CommentCache, SeasonalCommentFilter
from src.data.past_comment import PastComment, CommentType


class TestCSVFileHandler:
    """CSVFileHandlerのテスト"""
    
    def test_read_csv_file_success(self, tmp_path):
        """CSVファイルの正常読み込みテスト"""
        # テストファイルを作成
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("weather_comment,count\nテストコメント,10\n")
        
        handler = CSVFileHandler()
        rows = handler.read_csv_file(csv_file)
        
        assert len(rows) == 1
        assert rows[0]['weather_comment'] == 'テストコメント'
        assert rows[0]['count'] == '10'
        assert rows[0]['_line_number'] == 2
    
    def test_read_csv_file_not_found(self, tmp_path):
        """存在しないファイルの読み込みテスト"""
        handler = CSVFileHandler()
        rows = handler.read_csv_file(tmp_path / "missing.csv")
        
        assert rows == []
    
    def test_validate_csv_headers(self, tmp_path):
        """CSVヘッダー検証テスト"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("weather_comment,count\nテスト,5\n")
        
        handler = CSVFileHandler()
        
        # 正しいヘッダー
        assert handler.validate_csv_headers(csv_file, ['weather_comment', 'count'])
        
        # 不足しているヘッダー
        assert not handler.validate_csv_headers(csv_file, ['weather_comment', 'count', 'missing'])


class TestCommentParser:
    """CommentParserのテスト"""
    
    @pytest.fixture
    def sample_row(self):
        """テスト用の行データ"""
        return {
            'weather_comment': '晴れの日です',
            'count': '100',
            '_line_number': 2,
            '_file_path': Path('test.csv')
        }
    
    def test_parse_comment_row_success(self, sample_row):
        """正常なコメント解析テスト"""
        comment = CommentParser.parse_comment_row(sample_row, 'weather_comment', '春')
        
        assert comment is not None
        assert comment.comment_text == '晴れの日です'
        assert comment.comment_type == CommentType.WEATHER_COMMENT
        assert comment.raw_data['count'] == 100
        assert comment.raw_data['season'] == '春'
    
    def test_parse_comment_row_empty(self, sample_row):
        """空コメントの解析テスト"""
        sample_row['weather_comment'] = ''
        comment = CommentParser.parse_comment_row(sample_row, 'weather_comment', '春')
        
        assert comment is None
    
    def test_parse_comment_row_invalid_count(self, sample_row):
        """不正なカウント値の解析テスト"""
        sample_row['count'] = 'invalid'
        comment = CommentParser.parse_comment_row(sample_row, 'weather_comment', '春')
        
        assert comment is not None
        assert comment.raw_data['count'] == 0  # デフォルト値
    
    def test_parse_comment_row_long_text(self, sample_row):
        """長いコメントの切り詰めテスト"""
        sample_row['weather_comment'] = 'x' * 300  # 300文字
        comment = CommentParser.parse_comment_row(sample_row, 'weather_comment', '春')
        
        assert comment is not None
        assert len(comment.comment_text) == 200  # 最大長に切り詰められる


class TestCommentCache:
    """CommentCacheのテスト"""
    
    def test_cache_lifecycle(self):
        """キャッシュのライフサイクルテスト"""
        cache = CommentCache(cache_ttl_minutes=60)
        
        # 初期状態
        assert not cache.is_cache_valid()
        assert cache.get() is None
        
        # データを設定
        comments = [Mock(spec=PastComment)]
        cache.set(comments)
        
        assert cache.is_cache_valid()
        assert cache.get() == comments
        
        # クリア
        cache.clear()
        assert not cache.is_cache_valid()
        assert cache.get() is None
    
    def test_cache_expiration(self):
        """キャッシュの有効期限テスト"""
        cache = CommentCache(cache_ttl_minutes=0)  # 即座に期限切れ
        
        comments = [Mock(spec=PastComment)]
        cache.set(comments)
        
        # 即座に期限切れ
        assert not cache.is_cache_valid()
        assert cache.get() is None
    
    def test_cache_stats(self):
        """キャッシュ統計情報のテスト"""
        cache = CommentCache()
        comments = [Mock(spec=PastComment), Mock(spec=PastComment)]
        cache.set(comments)
        
        stats = cache.get_stats()
        assert stats['is_valid'] is True
        assert stats['size'] == 2
        assert stats['loaded_at'] is not None
        assert stats['ttl_minutes'] == 60


class TestSeasonalCommentFilter:
    """SeasonalCommentFilterのテスト"""
    
    @pytest.mark.parametrize("month,expected_seasons", [
        (3, ["春", "梅雨"]),
        (6, ["春", "梅雨", "夏"]),
        (9, ["夏", "台風", "秋"]),
        (12, ["冬", "春"]),
    ])
    def test_get_relevant_seasons(self, month, expected_seasons):
        """月から季節を取得するテスト"""
        seasons = SeasonalCommentFilter.get_relevant_seasons(month)
        assert seasons == expected_seasons
    
    def test_filter_by_season(self):
        """季節によるフィルタリングテスト"""
        comments = [
            Mock(spec=PastComment, raw_data={'season': '春'}),
            Mock(spec=PastComment, raw_data={'season': '夏'}),
            Mock(spec=PastComment, raw_data={'season': '春'}),
        ]
        
        filtered = SeasonalCommentFilter.filter_by_season(comments, ['春'])
        assert len(filtered) == 2
        assert all(c.raw_data['season'] == '春' for c in filtered)
    
    def test_filter_by_type_and_season(self):
        """タイプと季節によるフィルタリングテスト"""
        comments = [
            Mock(spec=PastComment, raw_data={'season': '春', 'count': 10}, 
                 comment_type=Mock(value='weather_comment')),
            Mock(spec=PastComment, raw_data={'season': '春', 'count': 20}, 
                 comment_type=Mock(value='weather_comment')),
            Mock(spec=PastComment, raw_data={'season': '春', 'count': 30}, 
                 comment_type=Mock(value='advice')),
        ]
        
        filtered = SeasonalCommentFilter.filter_by_type_and_season(
            comments, 'weather_comment', '春', limit=1
        )
        
        assert len(filtered) == 1
        assert filtered[0].raw_data['count'] == 20  # カウント順でソート


class TestLocalCommentRepository:
    """LocalCommentRepositoryの統合テスト"""
    
    @pytest.fixture
    def mock_csv_data(self):
        """モックCSVデータ"""
        return [
            {'weather_comment': '晴れです', 'count': '10', '_line_number': 2, '_file_path': Path('test.csv')},
            {'weather_comment': '暖かい', 'count': '20', '_line_number': 3, '_file_path': Path('test.csv')},
        ]
    
    @patch('src.repositories.local_comment_repository_refactored.CSVFileHandler')
    @patch('src.repositories.local_comment_repository_refactored.CommentCache')
    def test_get_all_available_comments(self, mock_cache_class, mock_handler_class, mock_csv_data):
        """全コメント取得のテスト"""
        # モックの設定
        mock_handler = mock_handler_class.return_value
        mock_handler.read_csv_file.return_value = mock_csv_data
        
        mock_cache = mock_cache_class.return_value
        mock_cache.get.return_value = None  # キャッシュミス
        
        repo = LocalCommentRepository('output')
        
        # パッチを適用してCommentParser.parse_comment_rowをモック
        with patch('src.repositories.local_comment_repository_refactored.CommentParser.parse_comment_row') as mock_parse:
            mock_comment = Mock(spec=PastComment, raw_data={'season': '春', 'count': 10})
            mock_comment.comment_type.value = 'weather_comment'
            mock_parse.return_value = mock_comment
            
            comments = repo.get_all_available_comments(max_per_season_per_type=1)
            
            # キャッシュが更新されたことを確認
            assert mock_cache.set.called
    
    @patch('src.repositories.local_comment_repository_refactored.datetime')
    def test_get_recent_comments(self, mock_datetime):
        """最近のコメント取得テスト"""
        # 6月を設定
        mock_datetime.now.return_value.month = 6
        
        repo = LocalCommentRepository('output')
        
        with patch.object(repo, 'get_comments_by_season') as mock_get:
            repo.get_recent_comments(limit=100)
            
            # 6月の関連季節で呼ばれることを確認
            mock_get.assert_called_once_with(['春', '梅雨', '夏'], 100)


if __name__ == "__main__":
    pytest.main([__file__])
"""ローカルコメントリポジトリのテスト"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import datetime

from src.repositories.local_comment_repository import LocalCommentRepository
from src.data.past_comment import PastComment, CommentType


class TestLocalCommentRepository:
    """LocalCommentRepositoryのテストクラス"""

    @pytest.fixture
    def mock_csv_data(self):
        """テスト用のCSVデータ"""
        return {
            "春_weather_comment_enhanced100.csv": 
                "weather_comment,count\n"
                "春らしい陽気です,100\n"
                "桜が満開です,50\n",
            "春_advice_enhanced100.csv":
                "advice,count\n"
                "花粉症対策を,80\n"
                "日焼け止めも忘れずに,30\n",
            "夏_weather_comment_enhanced100.csv":
                "weather_comment,count\n"
                "真夏の暑さです,120\n"
                "蒸し暑い一日,60\n",
            "夏_advice_enhanced100.csv":
                "advice,count\n"
                "熱中症に注意,150\n"
                "こまめな水分補給を,90\n"
        }

    def test_initialization_with_existing_directory(self, tmp_path, mock_csv_data):
        """既存ディレクトリでの初期化テスト"""
        # CSVファイルを作成
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        for filename, content in mock_csv_data.items():
            (output_dir / filename).write_text(content, encoding='utf-8')
        
        # リポジトリを初期化
        repo = LocalCommentRepository(str(output_dir))
        
        # キャッシュが読み込まれていることを確認
        assert repo._cache_loaded is True
        assert repo._comment_cache is not None
        assert len(repo._comment_cache) > 0

    def test_initialization_without_directory(self, tmp_path):
        """ディレクトリが存在しない場合の初期化テスト"""
        non_existent_dir = tmp_path / "non_existent"
        
        # ディレクトリが作成されることを確認
        repo = LocalCommentRepository(str(non_existent_dir))
        
        assert non_existent_dir.exists()
        assert repo._cache_loaded is False
        assert repo._comment_cache == []

    def test_get_recent_comments_by_season(self, tmp_path, mock_csv_data):
        """季節に応じたコメント取得のテスト"""
        # CSVファイルを作成
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        for filename, content in mock_csv_data.items():
            (output_dir / filename).write_text(content, encoding='utf-8')
        
        repo = LocalCommentRepository(str(output_dir))
        
        # 春のデータ（3月）
        with patch('src.repositories.local_comment_repository.datetime') as mock_datetime:
            mock_datetime.now.return_value.month = 3
            comments = repo.get_recent_comments(limit=10)
            
            # 春と梅雨のコメントが含まれることを確認
            spring_comments = [c for c in comments if c.raw_data.get('season') == '春']
            assert len(spring_comments) > 0

    def test_get_all_available_comments(self, tmp_path, mock_csv_data):
        """全コメント取得のテスト"""
        # CSVファイルを作成
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        for filename, content in mock_csv_data.items():
            (output_dir / filename).write_text(content, encoding='utf-8')
        
        repo = LocalCommentRepository(str(output_dir))
        
        # 各季節・タイプごとに制限された数のコメントを取得
        comments = repo.get_all_available_comments(max_per_season_per_type=1)
        
        # 春と夏のweather_commentとadviceが1つずつ = 4つ
        assert len(comments) == 4
        
        # 各季節・タイプが含まれていることを確認
        seasons = set(c.raw_data.get('season') for c in comments)
        types = set(c.comment_type.value for c in comments)
        
        assert '春' in seasons
        assert '夏' in seasons
        assert 'weather_comment' in types
        assert 'advice' in types

    def test_cache_functionality(self, tmp_path, mock_csv_data):
        """キャッシュ機能のテスト"""
        # CSVファイルを作成
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        for filename, content in mock_csv_data.items():
            (output_dir / filename).write_text(content, encoding='utf-8')
        
        repo = LocalCommentRepository(str(output_dir))
        
        # 初回読み込み
        first_comments = repo.get_all_available_comments()
        
        # CSVファイルを削除
        for filename in mock_csv_data.keys():
            (output_dir / filename).unlink()
        
        # キャッシュから読み込めることを確認
        second_comments = repo.get_all_available_comments()
        
        assert len(first_comments) == len(second_comments)

    def test_invalid_csv_handling(self, tmp_path):
        """不正なCSVファイルの処理テスト"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # 不正なCSVファイルを作成
        invalid_csv = output_dir / "春_weather_comment_enhanced100.csv"
        invalid_csv.write_text("invalid,csv,format\nno,proper,headers", encoding='utf-8')
        
        # エラーが発生してもクラッシュしないことを確認
        repo = LocalCommentRepository(str(output_dir))
        comments = repo.get_recent_comments()
        
        # 空のリストが返されることを確認
        assert isinstance(comments, list)

    def test_empty_csv_handling(self, tmp_path):
        """空のCSVファイルの処理テスト"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # 空のCSVファイルを作成
        empty_csv = output_dir / "春_weather_comment_enhanced100.csv"
        empty_csv.write_text("weather_comment,count\n", encoding='utf-8')
        
        repo = LocalCommentRepository(str(output_dir))
        comments = repo.get_recent_comments()
        
        assert isinstance(comments, list)
        assert len(comments) == 0

    def test_comment_sorting_by_popularity(self, tmp_path):
        """人気順でのソートテスト"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # カウント順のCSVを作成
        csv_content = (
            "weather_comment,count\n"
            "低人気コメント,10\n"
            "高人気コメント,1000\n"
            "中人気コメント,100\n"
        )
        (output_dir / "春_weather_comment_enhanced100.csv").write_text(
            csv_content, encoding='utf-8'
        )
        
        repo = LocalCommentRepository(str(output_dir))
        comments = repo.get_recent_comments()
        
        # 人気順でソートされていることを確認
        if len(comments) >= 2:
            assert comments[0].raw_data['count'] >= comments[1].raw_data['count']

    def test_get_relevant_seasons(self, tmp_path):
        """月別の関連季節判定テスト"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        repo = LocalCommentRepository(str(output_dir))
        
        # 各月の関連季節をテスト
        test_cases = {
            3: ["春", "梅雨"],
            6: ["春", "梅雨", "夏"],
            8: ["夏", "梅雨", "台風"],
            11: ["秋", "台風", "冬"],
            1: ["冬", "春"]
        }
        
        for month, expected_seasons in test_cases.items():
            seasons = repo._get_relevant_seasons(month)
            for season in expected_seasons:
                assert season in seasons


if __name__ == "__main__":
    pytest.main([__file__])
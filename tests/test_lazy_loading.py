"""遅延読み込みコメントリポジトリのテスト"""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import csv

from src.repositories.lazy_comment_repository import LazyCommentRepository
from src.data.past_comment import PastComment, CommentType


class TestLazyCommentRepository:
    """LazyCommentRepositoryのテスト"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """一時的な出力ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def create_test_csv(self, temp_output_dir):
        """テスト用CSVファイルを作成するフィクスチャ"""
        def _create_csv(season, comment_type, num_comments=10):
            filename = f"{season}_{comment_type}_enhanced100.csv"
            file_path = temp_output_dir / filename
            
            # ヘッダーを決定
            if comment_type == "weather_comment":
                headers = ["weather_comment"]
            else:
                headers = ["advice"]
            
            # CSVファイルを作成
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                for i in range(num_comments):
                    row = {headers[0]: f"{season}の{comment_type}テストコメント{i+1}"}
                    writer.writerow(row)
            
            return file_path
        
        return _create_csv
    
    def test_initialization_no_loading(self, temp_output_dir):
        """初期化時にファイルを読み込まないことを確認"""
        # CSVファイルを作成
        for season in ["春", "夏"]:
            for comment_type in ["weather_comment", "advice"]:
                filename = f"{season}_{comment_type}_enhanced100.csv"
                (temp_output_dir / filename).touch()
        
        # リポジトリを初期化
        start_time = time.time()
        repo = LazyCommentRepository(output_dir=str(temp_output_dir))
        init_time = time.time() - start_time
        
        # 初期化が高速であることを確認（0.1秒以内）
        assert init_time < 0.1
        
        # ファイルがまだ読み込まれていないことを確認
        assert len(repo._loaded_files) == 0
        stats = repo.get_statistics()
        assert stats["loaded_files"] == 0
    
    def test_lazy_loading_on_demand(self, temp_output_dir, create_test_csv):
        """必要な時にだけファイルを読み込むことを確認"""
        # テストCSVを作成
        create_test_csv("春", "weather_comment", 5)
        create_test_csv("春", "advice", 3)
        create_test_csv("夏", "weather_comment", 4)
        
        repo = LazyCommentRepository(output_dir=str(temp_output_dir))
        
        # 春の天気コメントのみを取得
        spring_weather = repo.get_weather_comments_by_season("春")
        assert len(spring_weather) == 5
        
        # 春の天気コメントのみが読み込まれたことを確認
        assert len(repo._loaded_files) == 1
        assert "春_weather_comment" in repo._loaded_files
        
        # 春のアドバイスを取得
        spring_advice = repo.get_advice_by_season("春")
        assert len(spring_advice) == 3
        
        # 2つのファイルが読み込まれたことを確認
        assert len(repo._loaded_files) == 2
        
        # 夏のデータはまだ読み込まれていない
        assert "夏_weather_comment" not in repo._loaded_files
    
    def test_cache_functionality(self, temp_output_dir, create_test_csv):
        """キャッシュが正しく機能することを確認"""
        create_test_csv("春", "weather_comment", 10)
        
        repo = LazyCommentRepository(output_dir=str(temp_output_dir), cache_ttl_minutes=1)
        
        # 初回読み込み
        comments1 = repo.get_weather_comments_by_season("春")
        assert len(comments1) == 10
        
        # キャッシュから取得（高速）
        start_time = time.time()
        comments2 = repo.get_weather_comments_by_season("春")
        cache_time = time.time() - start_time
        
        assert len(comments2) == 10
        assert cache_time < 0.01  # キャッシュからの取得は非常に高速
        
        # キャッシュ統計を確認
        stats = repo.get_statistics()
        assert stats["cache_stats"]["hits"] > 0
    
    def test_search_with_selective_loading(self, temp_output_dir, create_test_csv):
        """検索時に必要なファイルのみを読み込むことを確認"""
        # 複数の季節のCSVを作成
        for season in ["春", "夏", "秋", "冬"]:
            create_test_csv(season, "weather_comment", 5)
            create_test_csv(season, "advice", 3)
        
        repo = LazyCommentRepository(output_dir=str(temp_output_dir))
        
        # 春の天気コメントのみを検索
        results = repo.search_comments(
            season="春",
            comment_type=CommentType.WEATHER_COMMENT
        )
        
        assert len(results) == 5
        # 春の天気コメントファイルのみが読み込まれた
        assert len(repo._loaded_files) == 1
        assert "春_weather_comment" in repo._loaded_files
    
    def test_lazy_loading_performance(self, temp_output_dir, create_test_csv):
        """遅延読み込みリポジトリのパフォーマンステスト"""
        # 大量のCSVファイルを作成
        for season in ["春", "夏", "秋", "冬", "梅雨", "台風"]:
            create_test_csv(season, "weather_comment", 100)
            create_test_csv(season, "advice", 50)
        
        # 遅延読み込みリポジトリの初期化時間を測定
        start_time = time.time()
        lazy_repo = LazyCommentRepository(output_dir=str(temp_output_dir))
        init_time = time.time() - start_time
        
        # 初期化が高速であることを確認（0.1秒以内）
        assert init_time < 0.1
        
        # 特定の季節のデータ取得時間を測定
        start_time = time.time()
        spring_comments = lazy_repo.get_comments_by_season("春")
        fetch_time = time.time() - start_time
        
        # 必要な分だけ読み込まれていることを確認
        assert len(lazy_repo._loaded_files) == 2  # 春のweather_commentとadviceのみ
        
        print(f"\n遅延読み込みパフォーマンス:")
        print(f"  初期化時間: {init_time:.3f}秒")
        print(f"  春データ取得時間: {fetch_time:.3f}秒")
        print(f"  読み込まれたファイル数: {len(lazy_repo._loaded_files)}/12")
    
    def test_preload_functionality(self, temp_output_dir, create_test_csv):
        """事前読み込み機能のテスト"""
        create_test_csv("春", "weather_comment", 10)
        create_test_csv("春", "advice", 5)
        create_test_csv("夏", "weather_comment", 8)
        
        repo = LazyCommentRepository(output_dir=str(temp_output_dir))
        
        # 春のデータを事前読み込み
        repo.preload_season("春")
        
        # 春の両方のファイルが読み込まれた
        assert len(repo._loaded_files) == 2
        assert "春_weather_comment" in repo._loaded_files
        assert "春_advice" in repo._loaded_files
        
        # 夏のデータはまだ読み込まれていない
        assert "夏_weather_comment" not in repo._loaded_files
    
    def test_clear_cache(self, temp_output_dir, create_test_csv):
        """キャッシュクリア機能のテスト"""
        create_test_csv("春", "weather_comment", 5)
        
        repo = LazyCommentRepository(output_dir=str(temp_output_dir))
        
        # データを読み込む
        comments = repo.get_weather_comments_by_season("春")
        assert len(comments) == 5
        assert len(repo._loaded_files) == 1
        
        # キャッシュをクリア
        repo.clear_cache()
        
        # キャッシュがクリアされた
        assert len(repo._loaded_files) == 0
        stats = repo.get_statistics()
        assert stats["loaded_files"] == 0
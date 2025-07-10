"""IndexedCSVHandlerのシリアライゼーションテスト"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
import csv

from src.repositories.indexed_csv_handler import IndexedCSVHandler
from src.data.past_comment import PastComment, CommentType


class TestIndexedCSVHandlerSerialization:
    """IndexedCSVHandlerのシリアライゼーション機能のテスト"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """一時的なキャッシュディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def sample_comment(self):
        """テスト用のPastCommentオブジェクト"""
        return PastComment(
            comment_id="test_001",
            comment_text="今日は晴れです",
            comment_type=CommentType.WEATHER_COMMENT,
            created_at=datetime(2025, 7, 10, 12, 0, 0),
            location="東京",
            weather_condition="晴れ",
            temperature=25.0,
            season="夏",
            usage_count=3,
            comment1="天気コメント",
            comment2="アドバイス"
        )
    
    def test_comment_to_dict_conversion(self, temp_cache_dir, sample_comment):
        """PastCommentオブジェクトから辞書への変換テスト"""
        handler = IndexedCSVHandler(cache_dir=temp_cache_dir)
        
        comment_dict = handler._comment_to_dict(sample_comment)
        
        assert comment_dict["comment_id"] == "test_001"
        assert comment_dict["comment_text"] == "今日は晴れです"
        assert comment_dict["comment_type"] == "weather_comment"
        assert comment_dict["created_at"] == "2025-07-10T12:00:00"
        assert comment_dict["location"] == "東京"
        assert comment_dict["weather_condition"] == "晴れ"
        assert comment_dict["temperature"] == 25.0
        assert comment_dict["season"] == "夏"
        assert comment_dict["usage_count"] == 3
        assert comment_dict["comment1"] == "天気コメント"
        assert comment_dict["comment2"] == "アドバイス"
    
    def test_dict_to_comment_conversion(self, temp_cache_dir):
        """辞書からPastCommentオブジェクトへの変換テスト"""
        handler = IndexedCSVHandler(cache_dir=temp_cache_dir)
        
        comment_dict = {
            "comment_id": "test_002",
            "comment_text": "今日は雨です",
            "comment_type": "advice",
            "created_at": "2025-07-10T13:00:00",
            "location": "大阪",
            "weather_condition": "雨",
            "temperature": 20.0,
            "season": "梅雨",
            "usage_count": 1,
            "comment1": "天気",
            "comment2": "傘を持参"
        }
        
        comment = handler._dict_to_comment(comment_dict)
        
        assert comment.comment_id == "test_002"
        assert comment.comment_text == "今日は雨です"
        assert comment.comment_type == CommentType.ADVICE
        assert comment.created_at == datetime(2025, 7, 10, 13, 0, 0)
        assert comment.location == "大阪"
        assert comment.weather_condition == "雨"
        assert comment.temperature == 20.0
        assert comment.season == "梅雨"
        assert comment.usage_count == 1
        assert comment.comment1 == "天気"
        assert comment.comment2 == "傘を持参"
    
    def test_index_serialization_roundtrip(self, temp_cache_dir, sample_comment):
        """インデックス全体のシリアライゼーション往復テスト"""
        handler = IndexedCSVHandler(cache_dir=temp_cache_dir)
        
        # オリジナルのインデックスを作成
        original_index = {
            "all_comments": [sample_comment],
            "by_weather": {"晴れ": [sample_comment]},
            "by_count": {"3": [sample_comment]},
            "by_season": {"夏": [sample_comment]}
        }
        
        # シリアライズ
        serializable = handler._convert_index_to_serializable(original_index)
        
        # JSONに変換可能か確認
        json_str = json.dumps(serializable, ensure_ascii=False)
        assert json_str
        
        # デシリアライズ
        deserialized_data = json.loads(json_str)
        restored_index = handler._convert_index_from_serializable(deserialized_data)
        
        # 復元されたデータの検証
        assert len(restored_index["all_comments"]) == 1
        restored_comment = restored_index["all_comments"][0]
        assert restored_comment.comment_id == sample_comment.comment_id
        assert restored_comment.comment_text == sample_comment.comment_text
        assert restored_comment.temperature == sample_comment.temperature
    
    def test_save_and_load_index_with_retry(self, temp_cache_dir):
        """リトライ機構を含むインデックスの保存と読み込みテスト"""
        handler = IndexedCSVHandler(cache_dir=temp_cache_dir)
        
        # テスト用のCSVファイルを作成
        csv_path = temp_cache_dir / "test.csv"
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['weather_comment', 'advice', 'weather_condition', 'temperature', 'usage_count'])
            writer.writeheader()
            writer.writerow({
                'weather_comment': '晴れています',
                'advice': '日焼け止めを',
                'weather_condition': '晴れ',
                'temperature': '28',
                'usage_count': '2'
            })
        
        # インデックスを構築して保存
        handler._build_index(csv_path, CommentType.WEATHER_COMMENT, "夏")
        
        # インデックスファイルが作成されたことを確認
        index_path = handler._get_index_path(csv_path)
        assert index_path.exists()
        assert index_path.suffix == '.json'
        
        # JSONファイルの内容を確認
        with open(index_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert "all_comments" in saved_data
        assert len(saved_data["all_comments"]) == 1
        assert saved_data["all_comments"][0]["comment_text"] == "晴れています"
    
    def test_atomic_write_with_temp_file(self, temp_cache_dir):
        """アトミックな書き込み（一時ファイル使用）のテスト"""
        handler = IndexedCSVHandler(cache_dir=temp_cache_dir)
        
        # ダミーのインデックスを作成
        test_index = {
            "all_comments": [],
            "by_weather": {},
            "by_count": {},
            "by_season": {}
        }
        
        csv_path = temp_cache_dir / "dummy.csv"
        csv_path.touch()  # ダミーファイルを作成
        
        # 保存処理を実行
        handler._save_index_to_disk(csv_path, test_index)
        
        # 一時ファイルが残っていないことを確認
        temp_files = list(temp_cache_dir.glob("*.tmp"))
        assert len(temp_files) == 0
        
        # 正式なインデックスファイルが存在することを確認
        index_path = handler._get_index_path(csv_path)
        assert index_path.exists()
        
        # 内容が正しく保存されていることを確認
        with open(index_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        assert "all_comments" in loaded_data
        assert isinstance(loaded_data["all_comments"], list)
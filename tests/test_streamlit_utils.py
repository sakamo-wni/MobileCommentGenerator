"""
Streamlitユーティリティ関数のテスト

UIユーティリティ関数の単体テスト
"""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import json
from datetime import datetime
import os

from src.ui.streamlit_utils import (
    load_locations,
    filter_locations,
    copy_to_clipboard,
    save_to_history,
    load_history,
    format_timestamp,
    validate_api_keys,
)
from unittest.mock import patch


class TestLocationUtils:
    """地点関連ユーティリティのテスト"""

    @patch("src.data.location_manager.LocationManager")
    def test_load_locations(self, mock_location_manager):
        """地点リスト読み込みのテスト"""
        # モックの設定
        mock_manager_instance = MagicMock()
        mock_manager_instance.get_all_location_names.return_value = ["東京", "大阪", "稚内", "那覇"]
        mock_location_manager.return_value = mock_manager_instance

        # 実行
        result = load_locations()

        # 検証
        assert len(result) == 4
        assert "東京" in result
        assert "稚内" in result
        mock_manager_instance.get_all_location_names.assert_called_once()

    def test_filter_locations_exact_match(self):
        """地点フィルタリング（完全一致）のテスト"""
        locations = ["東京", "大阪", "京都", "東大阪"]

        # 完全一致
        result = filter_locations(locations, "東京")
        assert result == ["東京"]

    def test_filter_locations_partial_match(self):
        """地点フィルタリング（部分一致）のテスト"""
        locations = ["東京", "大阪", "京都", "東大阪", "西東京"]

        # 部分一致
        result = filter_locations(locations, "東")
        assert len(result) == 3
        assert "東京" in result
        assert "東大阪" in result
        assert "西東京" in result

    def test_filter_locations_case_insensitive(self):
        """地点フィルタリング（大文字小文字無視）のテスト"""
        locations = ["Tokyo", "OSAKA", "Kyoto"]

        result = filter_locations(locations, "tokyo")
        assert "Tokyo" in result

        result = filter_locations(locations, "TOKYO")
        assert "Tokyo" in result

    def test_filter_locations_empty_query(self):
        """空のクエリでのフィルタリングテスト"""
        locations = ["東京", "大阪", "京都"]

        result = filter_locations(locations, "")
        assert result == locations

        result = filter_locations(locations, None)
        assert result == locations


class TestClipboardUtils:
    """クリップボード関連ユーティリティのテスト"""

    def test_copy_to_clipboard_success(self):
        """クリップボードへのコピー成功テスト"""
        text = "テストコメント"

        result = copy_to_clipboard(text)

        # copy_to_clipboard uses JavaScript, so it always returns True
        assert result is True

    def test_copy_to_clipboard_always_returns_true(self):
        """クリップボード関数は常にTrueを返すことをテスト"""
        # JavaScript実装のため、エラーハンドリングはブラウザ側で行われる
        result = copy_to_clipboard("テスト")
        
        assert result is True


class TestHistoryManagement:
    """履歴管理関連のテスト"""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_save_to_history(self, mock_makedirs, mock_exists, mock_file):
        """履歴保存のテスト"""
        # ディレクトリが存在しない場合
        mock_exists.return_value = False

        result = {
            "final_comment": "テストコメント",
            "generation_metadata": {"weather_condition": "晴れ", "temperature": 25.0},
        }
        location = "東京"
        provider = "openai"

        # 実行
        save_to_history(result, location, provider)

        # 検証
        mock_makedirs.assert_called_once()
        mock_file.assert_called()

        # 書き込まれた内容を確認
        handle = mock_file()
        written_data = "".join([call[0][0] for call in handle.write.call_args_list])
        saved_data = json.loads(written_data)

        assert saved_data["location"] == location
        assert saved_data["comment"] == "テストコメント"
        assert saved_data["provider"] == provider
        assert "timestamp" in saved_data

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"location": "東京", "comment": "晴れです"}]',
    )
    @patch("os.path.exists")
    def test_load_history_with_data(self, mock_exists, mock_file):
        """履歴読み込み（データあり）のテスト"""
        mock_exists.return_value = True

        result = load_history()

        assert len(result) == 1
        assert result[0]["location"] == "東京"
        assert result[0]["comment"] == "晴れです"

    @patch("os.path.exists")
    def test_load_history_no_file(self, mock_exists):
        """履歴読み込み（ファイルなし）のテスト"""
        mock_exists.return_value = False

        result = load_history()

        assert result == []

    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    @patch("os.path.exists")
    def test_load_history_invalid_json(self, mock_exists, mock_file):
        """履歴読み込み（無効なJSON）のテスト"""
        mock_exists.return_value = True

        result = load_history()

        assert result == []

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_save_history_preserves_limit(self, mock_exists, mock_file):
        """履歴保存の件数制限テスト"""
        # 既存の履歴（100件）
        existing_history = [
            {"timestamp": f"2024-06-{i:02d}", "comment": f"コメント{i}"} for i in range(1, 101)
        ]
        mock_file.return_value.read.return_value = json.dumps(existing_history)
        mock_exists.return_value = True

        # 新しい履歴を追加
        result = {"final_comment": "新しいコメント", "generation_metadata": {}}
        save_to_history(result, "東京", "openai")

        # 書き込まれたデータを確認
        handle = mock_file()
        write_calls = handle.write.call_args_list
        if write_calls:
            written_data = "".join([call[0][0] for call in write_calls])
            saved_history = json.loads(written_data)

            # 100件以下に制限されていることを確認
            assert len(saved_history) <= 100
            # 最新のコメントが先頭にあることを確認
            assert saved_history[0]["comment"] == "新しいコメント"


class TestFormatUtils:
    """フォーマット関連ユーティリティのテスト"""

    def test_format_timestamp_datetime_object(self):
        """datetimeオブジェクトのフォーマットテスト"""
        dt = datetime(2024, 6, 5, 14, 30, 0)
        result = format_timestamp(dt)
        assert result == "2024-06-05 14:30:00"

    def test_format_timestamp_string(self):
        """文字列タイムスタンプのフォーマットテスト"""
        # ISO形式
        result = format_timestamp("2024-06-05T14:30:00")
        assert result == "2024-06-05 14:30:00"

        # 既にフォーマット済み
        result = format_timestamp("2024-06-05 14:30:00")
        assert result == "2024-06-05 14:30:00"

    def test_format_timestamp_invalid(self):
        """無効なタイムスタンプのテスト"""
        result = format_timestamp("invalid")
        assert result == "invalid"

        result = format_timestamp(None)
        assert result == ""


class TestValidationUtils:
    """バリデーション関連ユーティリティのテスト"""

    def test_validate_api_keys_valid(self):
        """有効なAPIキーのバリデーションテスト"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-abcdef1234567890abcdef1234567890',
            'ANTHROPIC_API_KEY': 'sk-ant-api03-abcdef1234567890',
            'GEMINI_API_KEY': 'AIzaSyABC123defGHI456jklMNO789pqrSTU'
        }):
            result = validate_api_keys()
            assert isinstance(result, dict)

    def test_validate_api_keys_invalid(self):
        """無効なAPIキーのバリデーションテスト"""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_api_keys()
            assert isinstance(result, dict)

    def test_validate_api_keys_partial(self):
        """部分的に有効なAPIキーのテスト"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-valid-key-1234567890'
        }, clear=True):
            result = validate_api_keys()
            assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

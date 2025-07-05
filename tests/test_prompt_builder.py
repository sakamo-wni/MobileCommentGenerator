"""prompt_builder.pyのテスト"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.llm.prompt_builder import (
    EXAMPLE_TEMPLATES,
    CommentPromptBuilder,
    TemplateLoader,
    create_simple_prompt,
)


class TestTemplateLoader:
    """TemplateLoaderのテスト"""

    def test_load_text_file(self, tmp_path):
        """テキストファイルの読み込みテスト"""
        # テストファイルを作成
        test_dir = tmp_path / "templates"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("テストテンプレート")

        loader = TemplateLoader(test_dir)
        result = loader.load_text_file("test.txt")

        assert result == "テストテンプレート"

    def test_load_json_file(self, tmp_path):
        """JSONファイルの読み込みテスト"""
        # テストファイルを作成
        test_dir = tmp_path / "templates"
        test_dir.mkdir()
        test_file = test_dir / "test.json"
        test_file.write_text('{"key": "value"}')

        loader = TemplateLoader(test_dir)
        result = loader.load_json_file("test.json")

        assert result == {"key": "value"}

    def test_load_missing_file(self, tmp_path):
        """存在しないファイルの読み込みテスト"""
        loader = TemplateLoader(tmp_path)

        # テキストファイルの場合は例外
        with pytest.raises(FileNotFoundError):
            loader.load_text_file("missing.txt")

        # JSONファイルの場合は空の辞書
        result = loader.load_json_file("missing.json")
        assert result == {}


class TestCommentPromptBuilder:
    """CommentPromptBuilderのテスト"""

    @pytest.fixture
    def builder(self):
        """テスト用のビルダーインスタンス"""
        return CommentPromptBuilder()

    @pytest.fixture
    def mock_weather_data(self):
        """モックの天気データ"""
        mock = Mock()
        mock.location = "東京"
        mock.weather_description = "晴れ"
        mock.temperature = 25
        mock.humidity = 60
        mock.wind_speed = 3
        mock.datetime = datetime(2024, 1, 1, 12, 0)
        return mock

    def test_build_prompt_basic(self, builder, mock_weather_data):
        """基本的なプロンプト構築テスト"""
        prompt = builder.build_prompt(
            weather_data=mock_weather_data,
            location="東京"
        )

        assert "東京" in prompt
        assert "晴れ" in prompt
        assert "25" in prompt
        assert "60" in prompt
        assert "3" in prompt

    def test_build_prompt_with_past_comments(self, builder, mock_weather_data):
        """過去コメント付きプロンプト構築テスト"""
        mock_comment = Mock()
        mock_comment.comment_text = "爽やかな朝です"
        mock_comment.location = "東京"
        mock_comment.comment_type = "天気"

        prompt = builder.build_prompt(
            weather_data=mock_weather_data,
            past_comments=[mock_comment],
            location="東京"
        )

        assert "爽やかな朝です" in prompt
        assert "過去のコメント" in prompt

    def test_build_prompt_no_weather_data(self, builder):
        """天気データなしのプロンプト構築テスト"""
        prompt = builder.build_prompt(
            weather_data=None,
            location="東京"
        )

        assert "東京" in prompt
        assert "不明" in prompt

    def test_create_custom_prompt(self, builder, mock_weather_data):
        """カスタムプロンプト生成テスト"""
        template = "地点:{location}, 天気:{weather_description}"
        prompt = builder.create_custom_prompt(
            template=template,
            weather_data=mock_weather_data,
            location="東京"
        )

        assert prompt == "地点:東京, 天気:晴れ"

    def test_get_example_template(self, builder):
        """例示テンプレート取得テスト"""
        # 存在するテンプレート
        template = builder.get_example_template("basic")
        assert template is not None

        # 存在しないテンプレート
        template = builder.get_example_template("nonexistent")
        assert template is None

    def test_reload_templates(self, builder):
        """テンプレート再読み込みテスト"""
        # エラーが発生しないことを確認
        builder.reload_templates()


class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    def test_create_simple_prompt(self):
        """シンプルプロンプト生成テスト"""
        prompt = create_simple_prompt("晴れ", "25", "東京")

        assert "晴れ" in prompt
        assert "25" in prompt
        assert "東京" in prompt
        assert "15文字以内" in prompt

    def test_example_templates(self):
        """例示テンプレートの確認"""
        assert "basic" in EXAMPLE_TEMPLATES
        assert "detailed" in EXAMPLE_TEMPLATES
        assert "friendly" in EXAMPLE_TEMPLATES

        # 各テンプレートが適切なプレースホルダーを含むか確認
        for _, template in EXAMPLE_TEMPLATES.items():
            assert "{" in template  # プレースホルダーが存在する


"""prompt_builder.pyのテスト"""

import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

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

    def test_strict_validation_mode(self, tmp_path):
        """厳格な検証モードのテスト"""
        # テストテンプレートディレクトリを作成
        test_dir = tmp_path / "templates"
        test_dir.mkdir()

        # 不完全なbase.txtファイルを作成（必須プレースホルダーが不足）
        base_file = test_dir / "base.txt"
        base_file.write_text("地点: {location}\n天気: {weather_description}")

        # 不完全なJSONファイルを作成
        weather_file = test_dir / "weather_specific.json"
        weather_file.write_text('{"晴れ": "晴れの日です"}')

        seasonal_file = test_dir / "seasonal_adjustments.json"
        seasonal_file.write_text('{"春": "春らしい"}')

        time_file = test_dir / "time_specific.json"
        time_file.write_text('{"朝": "朝の挨拶"}')

        fallback_file = test_dir / "fallback.txt"
        fallback_file.write_text("天気コメント:")

        examples_file = test_dir / "examples.json"
        examples_file.write_text('{}')

        # 厳格モードでエラーが発生することを確認
        loader = TemplateLoader(test_dir, strict_validation=True)
        with pytest.raises(ValueError) as exc_info:
            loader.load_all_templates()
        
        assert "テンプレート検証エラー" in str(exc_info.value)
        assert "temperature" in str(exc_info.value)

        # 通常モードではエラーが発生しないことを確認
        loader_normal = TemplateLoader(test_dir, strict_validation=False)
        templates = loader_normal.load_all_templates()
        assert templates is not None

    def test_template_validation_warnings(self, tmp_path, caplog):
        """テンプレート検証の警告テスト"""
        # テストテンプレートディレクトリを作成
        test_dir = tmp_path / "templates"
        test_dir.mkdir()

        # 完全なテンプレートファイルを作成
        base_file = test_dir / "base.txt"
        base_file.write_text(
            "地点: {location}\n"
            "天気: {weather_description}\n"
            "気温: {temperature}\n"
            "湿度: {humidity}\n"
            "風速: {wind_speed}\n"
            "時刻: {current_time}\n"
            "過去のコメント:\n{past_comments_examples}"
        )

        # 完全なJSONファイルを作成
        weather_file = test_dir / "weather_specific.json"
        weather_file.write_text(json.dumps({
            "晴": "晴れの表現",
            "雨": "雨の表現",
            "雪": "雪の表現",
            "曇": "曇りの表現"
        }, ensure_ascii=False))

        seasonal_file = test_dir / "seasonal_adjustments.json"
        seasonal_file.write_text(json.dumps({
            "春": "春の調整",
            "夏": "夏の調整",
            "秋": "秋の調整",
            "冬": "冬の調整"
        }, ensure_ascii=False))

        time_file = test_dir / "time_specific.json"
        time_file.write_text(json.dumps({
            "朝": "朝の表現",
            "昼": "昼の表現",
            "夕方": "夕方の表現",
            "夜": "夜の表現"
        }, ensure_ascii=False))

        fallback_file = test_dir / "fallback.txt"
        fallback_file.write_text("天気コメント: {location}")

        examples_file = test_dir / "examples.json"
        examples_file.write_text('{}')

        # 警告が出ないことを確認
        loader = TemplateLoader(test_dir)
        templates = loader.load_all_templates()
        
        # 警告メッセージがログに記録されていないことを確認
        warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
        validation_warnings = [r for r in warning_records if "必須" in r.message or "天気条件" in r.message or "季節" in r.message or "時間帯" in r.message]
        assert len(validation_warnings) == 0


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

    def test_cache_functionality(self, tmp_path):
        """キャッシュ機能のテスト"""
        # テストテンプレートディレクトリを作成
        test_dir = tmp_path / "templates"
        test_dir.mkdir()

        # 基本的なテンプレートファイルを作成
        self._create_valid_templates(test_dir)

        # 短いキャッシュ期間でビルダーを作成
        builder = CommentPromptBuilder(template_dir=test_dir, cache_duration=0.5)

        # 初回アクセス
        templates1 = builder.templates
        assert templates1 is not None

        # キャッシュが有効な間は同じインスタンスが返される
        templates2 = builder.templates
        assert templates1 is templates2

        # キャッシュ期間を過ぎるまで待つ
        time.sleep(0.6)

        # キャッシュが無効になった後は新しいインスタンスが返される
        templates3 = builder.templates
        assert templates3 is not None
        # 内容は同じだが、インスタンスは異なる
        assert templates3.base_template == templates1.base_template

    def test_cache_duration_parameter(self):
        """キャッシュ期間パラメータのテスト"""
        # デフォルトのキャッシュ期間
        builder1 = CommentPromptBuilder()
        assert builder1._cache_duration == 3600

        # カスタムキャッシュ期間
        builder2 = CommentPromptBuilder(cache_duration=7200)
        assert builder2._cache_duration == 7200

    def test_strict_validation_parameter(self, tmp_path):
        """厳格検証パラメータのテスト"""
        # テストテンプレートディレクトリを作成
        test_dir = tmp_path / "templates"
        test_dir.mkdir()

        # 不完全なテンプレートを作成
        base_file = test_dir / "base.txt"
        base_file.write_text("地点: {location}")

        # その他の必須ファイルを作成
        for filename in ["weather_specific.json", "seasonal_adjustments.json", 
                        "time_specific.json", "examples.json"]:
            (test_dir / filename).write_text('{}')
        
        (test_dir / "fallback.txt").write_text("天気コメント:")

        # 厳格モードでエラーが発生することを確認
        builder_strict = CommentPromptBuilder(template_dir=test_dir, strict_validation=True)
        with pytest.raises(ValueError):
            _ = builder_strict.templates

        # 通常モードではエラーが発生しないことを確認
        builder_normal = CommentPromptBuilder(template_dir=test_dir, strict_validation=False)
        templates = builder_normal.templates
        assert templates is not None

    def test_force_reload_templates(self, tmp_path):
        """強制再読み込みのテスト"""
        # テストテンプレートディレクトリを作成
        test_dir = tmp_path / "templates"
        test_dir.mkdir()
        self._create_valid_templates(test_dir)

        builder = CommentPromptBuilder(template_dir=test_dir, cache_duration=3600)

        # 初回アクセス
        templates1 = builder.templates
        original_cache_time = builder._cache_time

        # 通常の再読み込み（キャッシュが有効なので変わらない）
        builder.reload_templates(force=False)
        assert builder._cache_time == original_cache_time

        # 強制再読み込み
        builder.reload_templates(force=True)
        # reload_templatesメソッドの最後でtemplatesプロパティにアクセスするため、
        # キャッシュはすぐに再作成される
        assert builder._templates_cache is not None
        assert builder._cache_time > original_cache_time

    def _create_valid_templates(self, test_dir: Path):
        """有効なテンプレートファイルを作成するヘルパーメソッド"""
        # base.txt
        base_file = test_dir / "base.txt"
        base_file.write_text(
            "地点: {location}\n"
            "天気: {weather_description}\n"
            "気温: {temperature}\n"
            "湿度: {humidity}\n"
            "風速: {wind_speed}\n"
            "時刻: {current_time}\n"
            "過去のコメント:\n{past_comments_examples}"
        )

        # weather_specific.json
        weather_file = test_dir / "weather_specific.json"
        weather_file.write_text(json.dumps({
            "晴": "晴れの表現",
            "雨": "雨の表現",
            "雪": "雪の表現",
            "曇": "曇りの表現"
        }, ensure_ascii=False))

        # seasonal_adjustments.json
        seasonal_file = test_dir / "seasonal_adjustments.json"
        seasonal_file.write_text(json.dumps({
            "春": "春の調整",
            "夏": "夏の調整",
            "秋": "秋の調整",
            "冬": "冬の調整"
        }, ensure_ascii=False))

        # time_specific.json
        time_file = test_dir / "time_specific.json"
        time_file.write_text(json.dumps({
            "朝": "朝の表現",
            "昼": "昼の表現",
            "夕方": "夕方の表現",
            "夜": "夜の表現"
        }, ensure_ascii=False))

        # fallback.txt
        fallback_file = test_dir / "fallback.txt"
        fallback_file.write_text("天気コメント: {location}")

        # examples.json
        examples_file = test_dir / "examples.json"
        examples_file.write_text('{}')


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


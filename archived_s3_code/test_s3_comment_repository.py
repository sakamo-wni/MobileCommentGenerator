"""
S3コメントリポジトリのテスト - DEPRECATED

注意: このテストは古い実装に関するものです。
現在、システムはS3の代わりにローカルCSVファイルを使用するように変更されました。
新しい実装のテストについては、local_comment_repositoryのテストを参照してください。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
from botocore.exceptions import ClientError

from src.repositories.s3_comment_repository import (
    S3CommentRepository,
    S3CommentRepositoryError,
    S3CommentRepositoryConfig,
)
from src.data.past_comment import PastComment, CommentType


class TestS3CommentRepository:
    """S3CommentRepository クラスのテスト"""

    def test_repository_initialization(self):
        """リポジトリ初期化のテスト"""
        with patch("boto3.client") as mock_boto3:
            repo = S3CommentRepository(
                bucket_name="test-bucket",
                aws_access_key_id="test-key",
                aws_secret_access_key="test-secret",
            )

            assert repo.bucket_name == "test-bucket"
            assert repo.region_name == "ap-northeast-1"
            mock_boto3.assert_called_once()

    def test_initialization_with_invalid_credentials(self):
        """無効な認証情報での初期化テスト"""
        with patch("boto3.client") as mock_boto3:
            from botocore.exceptions import NoCredentialsError

            mock_boto3.side_effect = NoCredentialsError()

            with pytest.raises(S3CommentRepositoryError, match="AWS認証情報が設定されていません"):
                S3CommentRepository()

    @patch("boto3.client")
    def test_test_connection_success(self, mock_boto3):
        """接続テスト成功のテスト"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        repo = S3CommentRepository()
        result = repo.test_connection()

        assert result == True
        mock_client.head_bucket.assert_called_once_with(Bucket=repo.bucket_name)

    @patch("boto3.client")
    def test_test_connection_failure(self, mock_boto3):
        """接続テスト失敗のテスト"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        # 404エラーをシミュレート
        error_response = {"Error": {"Code": "404"}}
        mock_client.head_bucket.side_effect = ClientError(error_response, "head_bucket")

        repo = S3CommentRepository()
        result = repo.test_connection()

        assert result == False

    @patch("boto3.client")
    def test_list_available_periods(self, mock_boto3):
        """利用可能期間リスト取得のテスト"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        # モックレスポンス
        mock_client.list_objects_v2.return_value = {
            "CommonPrefixes": [
                {"Prefix": "downloaded_jsonl_files_archive/202406/"},
                {"Prefix": "downloaded_jsonl_files_archive/202405/"},
                {"Prefix": "downloaded_jsonl_files_archive/202404/"},
            ]
        }

        repo = S3CommentRepository()
        periods = repo.list_available_periods()

        assert periods == ["202406", "202405", "202404"]
        mock_client.list_objects_v2.assert_called_once()

    @patch("boto3.client")
    def test_fetch_comments_by_period_success(self, mock_boto3):
        """期間指定コメント取得成功のテスト"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        # モックJSONLデータ
        jsonl_content = "\n".join(
            [
                json.dumps(
                    {
                        "location": "東京",
                        "datetime": "2024-06-05T12:00:00+09:00",
                        "weather_condition": "晴れ",
                        "comment_text": "いい天気",
                        "comment_type": "weather_comment",
                        "temperature": 25.0,
                    }
                ),
                json.dumps(
                    {
                        "location": "東京",
                        "datetime": "2024-06-05T12:00:00+09:00",
                        "weather_condition": "晴れ",
                        "comment_text": "日焼け注意",
                        "comment_type": "advice",
                        "temperature": 25.0,
                    }
                ),
            ]
        )

        # S3レスポンスのモック
        mock_response = {"Body": Mock()}
        mock_response["Body"].read.return_value = jsonl_content.encode("utf-8")
        mock_client.get_object.return_value = mock_response

        repo = S3CommentRepository()
        collection = repo.fetch_comments_by_period("202406")

        assert len(collection.comments) == 2
        assert collection.source_period == "202406"
        assert collection.comments[0].location == "東京"
        assert collection.comments[0].comment_type == CommentType.WEATHER_COMMENT
        assert collection.comments[1].comment_type == CommentType.ADVICE

    @patch("boto3.client")
    def test_fetch_comments_by_period_file_not_found(self, mock_boto3):
        """ファイル未発見時のテスト"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        # NoSuchKeyエラーをシミュレート
        error_response = {"Error": {"Code": "NoSuchKey"}}
        mock_client.get_object.side_effect = ClientError(error_response, "get_object")

        repo = S3CommentRepository()
        collection = repo.fetch_comments_by_period("202406")

        assert len(collection.comments) == 0
        assert collection.source_period == "202406"

    @patch("boto3.client")
    def test_fetch_comments_with_location_filter(self, mock_boto3):
        """地点フィルタ付きコメント取得のテスト"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        # 複数地点のJSONLデータ
        jsonl_content = "\n".join(
            [
                json.dumps(
                    {
                        "location": "東京",
                        "datetime": "2024-06-05T12:00:00+09:00",
                        "weather_condition": "晴れ",
                        "comment_text": "東京は晴れ",
                        "comment_type": "weather_comment",
                    }
                ),
                json.dumps(
                    {
                        "location": "大阪",
                        "datetime": "2024-06-05T12:00:00+09:00",
                        "weather_condition": "曇り",
                        "comment_text": "大阪は曇り",
                        "comment_type": "weather_comment",
                    }
                ),
            ]
        )

        mock_response = {"Body": Mock()}
        mock_response["Body"].read.return_value = jsonl_content.encode("utf-8")
        mock_client.get_object.return_value = mock_response

        repo = S3CommentRepository()
        collection = repo.fetch_comments_by_period("202406", location="東京")

        # 東京のコメントのみフィルタリングされる
        assert len(collection.comments) == 1
        assert collection.comments[0].location == "東京"

    @patch("boto3.client")
    def test_parse_jsonl_content_with_invalid_lines(self, mock_boto3):
        """不正行を含むJSONL解析のテスト"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        # 不正なJSONを含むデータ
        jsonl_content = "\n".join(
            [
                json.dumps(
                    {
                        "location": "東京",
                        "datetime": "2024-06-05T12:00:00+09:00",
                        "weather_condition": "晴れ",
                        "comment_text": "正常なコメント",
                        "comment_type": "weather_comment",
                    }
                ),
                '{"invalid": json}',  # 不正なJSON
                "",  # 空行
                json.dumps(
                    {
                        "location": "",  # 空地点名（バリデーションエラー）
                        "datetime": "2024-06-05T12:00:00+09:00",
                        "weather_condition": "曇り",
                        "comment_text": "無効なコメント",
                        "comment_type": "weather_comment",
                    }
                ),
            ]
        )

        mock_response = {"Body": Mock()}
        mock_response["Body"].read.return_value = jsonl_content.encode("utf-8")
        mock_client.get_object.return_value = mock_response

        repo = S3CommentRepository()
        collection = repo.fetch_comments_by_period("202406")

        # 正常なコメントのみが取得される
        assert len(collection.comments) == 1
        assert collection.comments[0].comment_text == "正常なコメント"

    def test_invalid_period_format(self):
        """不正期間フォーマットのテスト"""
        repo = S3CommentRepository()

        with pytest.raises(ValueError, match="期間は YYYYMM 形式で指定してください"):
            repo.fetch_comments_by_period("2024-06")  # 不正フォーマット

    @patch("boto3.client")
    def test_fetch_comments_by_date_range(self, mock_boto3):
        """日付範囲指定コメント取得のテスト"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        # 複数期間のファイルを模擬
        def mock_get_object(Bucket, Key):
            if "202406" in Key:
                content = json.dumps(
                    {
                        "location": "東京",
                        "datetime": "2024-06-15T12:00:00+09:00",
                        "weather_condition": "晴れ",
                        "comment_text": "6月のコメント",
                        "comment_type": "weather_comment",
                    }
                )
            elif "202405" in Key:
                content = json.dumps(
                    {
                        "location": "東京",
                        "datetime": "2024-05-15T12:00:00+09:00",
                        "weather_condition": "曇り",
                        "comment_text": "5月のコメント",
                        "comment_type": "weather_comment",
                    }
                )
            else:
                raise ClientError({"Error": {"Code": "NoSuchKey"}}, "get_object")

            mock_response = {"Body": Mock()}
            mock_response["Body"].read.return_value = content.encode("utf-8")
            return mock_response

        mock_client.get_object.side_effect = mock_get_object

        repo = S3CommentRepository()
        collection = repo.fetch_comments_by_date_range(
            start_date=datetime(2024, 5, 1), end_date=datetime(2024, 6, 30)
        )

        assert len(collection.comments) == 2
        assert collection.source_period == "202405-202406"

    @patch("boto3.client")
    def test_search_similar_comments(self, mock_boto3):
        """類似コメント検索のテスト"""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        # 類似度テスト用のJSONLデータ
        jsonl_content = "\n".join(
            [
                json.dumps(
                    {
                        "location": "東京",
                        "datetime": "2024-06-05T12:00:00+09:00",
                        "weather_condition": "晴れ",
                        "comment_text": "類似コメント1",
                        "comment_type": "weather_comment",
                        "temperature": 22.0,
                    }
                ),
                json.dumps(
                    {
                        "location": "大阪",
                        "datetime": "2024-06-05T12:00:00+09:00",
                        "weather_condition": "雨",
                        "comment_text": "非類似コメント",
                        "comment_type": "weather_comment",
                        "temperature": 15.0,
                    }
                ),
            ]
        )

        mock_response = {"Body": Mock()}
        mock_response["Body"].read.return_value = jsonl_content.encode("utf-8")
        mock_client.get_object.return_value = mock_response

        repo = S3CommentRepository()
        similar_comments = repo.search_similar_comments(
            target_weather_condition="晴れ", target_temperature=20.0, target_location="東京"
        )

        # 類似コメントのみが返される
        assert len(similar_comments) >= 1
        assert similar_comments[0].weather_condition == "晴れ"


class TestS3CommentRepositoryConfig:
    """S3CommentRepositoryConfig クラスのテスト"""

    @patch.dict(
        "os.environ",
        {
            "S3_COMMENT_BUCKET": "test-bucket",
            "AWS_DEFAULT_REGION": "us-west-2",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        },
    )
    def test_config_from_environment(self):
        """環境変数からの設定読み込みテスト"""
        config = S3CommentRepositoryConfig()

        assert config.bucket_name == "test-bucket"
        assert config.region_name == "us-west-2"
        assert config.aws_access_key_id == "test-key"
        assert config.aws_secret_access_key == "test-secret"

    @patch("boto3.client")
    def test_create_repository_from_config(self, mock_boto3):
        """設定からリポジトリ作成のテスト"""
        config = S3CommentRepositoryConfig()
        repo = config.create_repository()

        assert isinstance(repo, S3CommentRepository)
        mock_boto3.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])

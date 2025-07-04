"""
過去コメント取得ノードのテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.nodes.retrieve_past_comments_node import (
    RetrievePastCommentsNode,
    retrieve_past_comments_node,
    retrieve_past_comments_for_condition,
)
from src.data.past_comment import PastComment, PastCommentCollection, CommentType


class TestRetrievePastCommentsNode:
    """RetrievePastCommentsNode クラスのテスト"""

    def test_node_initialization(self):
        """ノード初期化のテスト"""
        mock_repository = Mock()
        node = RetrievePastCommentsNode(repository=mock_repository)

        assert node.repository == mock_repository
        assert node.default_months_back == 6
        assert node.max_comments_per_type == 10
        assert node.min_similarity_threshold == 0.3

    def test_node_initialization_without_repository(self):
        """リポジトリなしでの初期化テスト"""
        with patch(
            "src.nodes.retrieve_past_comments_node.LocalCommentRepository"
        ) as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            node = RetrievePastCommentsNode()

            assert node.repository == mock_repo

    def test_extract_weather_condition(self):
        """天気状況抽出のテスト"""
        node = RetrievePastCommentsNode(repository=Mock())

        # 直接的なキー
        weather_data1 = {"weather_description": "晴れ"}
        result1 = node._extract_weather_condition(weather_data1)
        assert result1 == "晴れ"

        # ネストされた構造
        weather_data2 = {"current_weather": {"condition": "曇り"}}
        result2 = node._extract_weather_condition(weather_data2)
        assert result2 == "曇り"

        # データなし
        weather_data3 = {}
        result3 = node._extract_weather_condition(weather_data3)
        assert result3 is None

    def test_extract_temperature(self):
        """気温抽出のテスト"""
        node = RetrievePastCommentsNode(repository=Mock())

        # 直接的なキー
        weather_data1 = {"temperature": 25.5}
        result1 = node._extract_temperature(weather_data1)
        assert result1 == 25.5

        # ネストされた構造
        weather_data2 = {"current_weather": {"temp": 18.0}}
        result2 = node._extract_temperature(weather_data2)
        assert result2 == 18.0

        # 不正な値
        weather_data3 = {"temperature": "invalid"}
        result3 = node._extract_temperature(weather_data3)
        assert result3 is None

    def test_balance_comment_types(self):
        """コメントタイプバランス調整のテスト"""
        node = RetrievePastCommentsNode(repository=Mock())
        node.max_comments_per_type = 4  # テスト用に小さく設定

        # 各タイプのコメントを作成
        weather_comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text=f"天気コメント{i}",
                comment_type=CommentType.WEATHER_COMMENT,
            )
            for i in range(5)
        ]

        advice_comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text=f"アドバイス{i}",
                comment_type=CommentType.ADVICE,
            )
            for i in range(3)
        ]

        other_comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="その他コメント",
                comment_type=CommentType.UNKNOWN,
            )
        ]

        all_comments = weather_comments + advice_comments + other_comments
        balanced = node._balance_comment_types(all_comments)

        # バランス調整後の結果確認
        assert len(balanced) == 4  # max_comments_per_type

        # タイプ別カウント
        weather_count = sum(1 for c in balanced if c.comment_type == CommentType.WEATHER_COMMENT)
        advice_count = sum(1 for c in balanced if c.comment_type == CommentType.ADVICE)

        assert weather_count == 2  # max_per_type = max_comments_per_type // 2
        assert advice_count == 2

    def test_generate_metadata(self):
        """メタデータ生成のテスト"""
        node = RetrievePastCommentsNode(repository=Mock())

        comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="短い",  # 3文字
                comment_type=CommentType.WEATHER_COMMENT,
            ),
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="これは15文字ちょうどです",  # 15文字
                comment_type=CommentType.ADVICE,
            ),
        ]

        metadata = node._generate_metadata(comments, "東京", "晴れ")

        assert metadata["total_comments"] == 2
        assert metadata["search_location"] == "東京"
        assert metadata["search_weather_condition"] == "晴れ"
        assert metadata["type_distribution"]["weather_comment"] == 1
        assert metadata["type_distribution"]["advice"] == 1
        assert metadata["character_stats"]["min_length"] == 3
        assert metadata["character_stats"]["max_length"] == 15
        assert metadata["character_stats"]["within_15_chars"] == 2
        assert metadata["retrieval_successful"] == True

    def test_node_call_success(self):
        """ノード呼び出し成功のテスト"""
        # モックリポジトリの設定
        mock_repository = Mock()
        mock_comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="いい天気",
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=25.0,
            )
        ]
        mock_repository.search_similar_comments.return_value = mock_comments

        node = RetrievePastCommentsNode(repository=mock_repository)

        # 入力状態
        input_state = {
            "location_name": "東京",
            "weather_data": {"weather_condition": "晴れ", "temperature": 25.0},
            "target_datetime": datetime.now(),
        }

        # ノード実行
        result = node(input_state)

        # 結果確認
        assert "past_comments" in result
        assert len(result["past_comments"]) == 1
        assert result["past_comments"][0]["comment_text"] == "いい天気"
        assert "comment_retrieval_metadata" in result
        assert result["comment_retrieval_metadata"]["total_comments"] == 1

    def test_node_call_missing_location(self):
        """地点名なしでのノード呼び出しテスト"""
        node = RetrievePastCommentsNode(repository=Mock())

        # 地点名なしの状態
        input_state = {"weather_data": {"weather_condition": "晴れ"}}

        # ノード実行
        result = node(input_state)

        # エラー処理確認
        assert result["past_comments"] == []
        assert "error" in result["comment_retrieval_metadata"]

    def test_node_call_repository_error(self):
        """リポジトリエラー時のテスト"""
        # エラーを発生させるモックリポジトリ
        mock_repository = Mock()
        mock_repository.search_similar_comments.side_effect = Exception("S3エラー")

        node = RetrievePastCommentsNode(repository=mock_repository)

        input_state = {"location_name": "東京", "weather_data": {"weather_condition": "晴れ"}}

        # ノード実行
        result = node(input_state)

        # エラー処理確認
        assert result["past_comments"] == []
        assert result["comment_retrieval_metadata"]["retrieval_successful"] == False

    def test_retrieve_with_fallback_strategy(self):
        """フォールバック戦略のテスト"""
        mock_repository = Mock()

        # 最初の検索は空を返し、フォールバック検索で結果を返す
        mock_repository.search_similar_comments.return_value = []

        mock_collection = Mock()
        mock_collection.comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="曇り",
                comment_text="フォールバックコメント",
                comment_type=CommentType.WEATHER_COMMENT,
            )
        ]
        mock_repository.get_recent_comments.return_value = mock_collection

        node = RetrievePastCommentsNode(repository=mock_repository)

        input_state = {"location_name": "東京", "weather_data": {"weather_condition": "晴れ"}}

        result = node(input_state)

        # フォールバック結果の確認
        assert len(result["past_comments"]) == 1
        assert result["past_comments"][0]["comment_text"] == "フォールバックコメント"


class TestNodeFunctions:
    """ノード関数のテスト"""

    @patch("src.nodes.retrieve_past_comments_node.RetrievePastCommentsNode")
    def test_retrieve_past_comments_node_function(self, mock_node_class):
        """retrieve_past_comments_node関数のテスト"""
        mock_node = Mock()
        mock_node_class.return_value = mock_node
        mock_node.return_value = {"result": "test"}

        input_state = {"location_name": "東京"}
        result = retrieve_past_comments_node(input_state)

        assert result == {"result": "test"}
        mock_node.assert_called_once_with(input_state)

    @pytest.mark.asyncio
    @patch("src.nodes.retrieve_past_comments_node.RetrievePastCommentsNode")
    async def test_retrieve_past_comments_for_condition(self, mock_node_class):
        """retrieve_past_comments_for_condition関数のテスト"""
        mock_node = Mock()
        mock_node_class.return_value = mock_node
        mock_node.return_value = {
            "past_comments": [{"comment_text": "テストコメント", "location": "東京"}]
        }

        result = await retrieve_past_comments_for_condition(
            location_name="東京", weather_condition="晴れ", temperature=25.0, max_comments=5
        )

        assert len(result) == 1
        assert result[0]["comment_text"] == "テストコメント"

        # ノードの設定確認
        called_node = mock_node_class.return_value
        assert called_node.max_comments_per_type == 5


if __name__ == "__main__":
    pytest.main([__file__])

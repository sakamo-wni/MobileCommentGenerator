"""
過去コメントデータクラスのテスト
"""

from datetime import datetime

import pytest

from src.data.past_comment import CommentType, PastComment, PastCommentCollection


@pytest.fixture
def base_comment_data():
    """基本的なコメントデータ"""
    return {
        "location": "東京",
        "datetime": datetime(2024, 6, 5, 12, 0),
        "weather_condition": "晴れ",
        "comment_text": "爽やかな朝ですね",
        "comment_type": CommentType.WEATHER_COMMENT,
        "temperature": 22.5,
        "weather_code": "100"
    }


@pytest.fixture
def sample_comments():
    """テスト用のコメントリスト"""
    return [
        PastComment(
            location="東京",
            datetime=datetime(2024, 6, 5, 12, 0),
            weather_condition="晴れ",
            comment_text="良い天気",
            comment_type=CommentType.WEATHER_COMMENT,
            temperature=25.0
        ),
        PastComment(
            location="大阪",
            datetime=datetime(2024, 6, 5, 12, 0),
            weather_condition="曇り",
            comment_text="過ごしやすい",
            comment_type=CommentType.WEATHER_COMMENT,
            temperature=20.0
        ),
        PastComment(
            location="東京",
            datetime=datetime(2024, 6, 5, 12, 0),
            weather_condition="晴れ",
            comment_text="日焼け注意",
            comment_type=CommentType.ADVICE,
            temperature=25.0
        )
    ]


class TestPastComment:
    """PastComment クラスのテスト"""

    def test_valid_past_comment_creation(self, base_comment_data):
        """正常な過去コメントデータの作成テスト"""
        comment = PastComment(**base_comment_data)

        assert comment.location == "東京"
        assert comment.comment_text == "爽やかな朝ですね"
        assert comment.comment_type == CommentType.WEATHER_COMMENT
        assert comment.temperature == 22.5
        assert comment.get_character_count() == 8
        assert comment.is_within_length_limit()

    @pytest.mark.parametrize("field,value,expected_message", [
        ("comment_text", "", "コメント本文が空です"),
        ("location", "", "地点名が空です"),
        ("temperature", -100.0, "異常な気温値"),
        ("temperature", 100.0, "異常な気温値"),  # 60度から100度に変更（より極端な値）
    ])
    def test_invalid_input_validation(self, base_comment_data, field, value, expected_message):
        """無効な入力値のバリデーションテスト"""
        test_data = base_comment_data.copy()
        test_data[field] = value

        with pytest.raises(ValueError, match=expected_message):
            PastComment(**test_data)

    @pytest.mark.parametrize("target_condition,fuzzy,expected_match", [
        ("晴れ", False, True),  # 完全一致
        ("曇り", False, False),  # 完全一致せず
        ("快晴", True, True),  # あいまい検索で一致
        ("sunny", True, True),  # 英語であいまい検索
        ("雨", True, False),  # あいまい検索でも一致せず
    ])
    def test_weather_condition_matching(self, base_comment_data, target_condition, fuzzy, expected_match):
        """天気状況マッチングのテスト"""
        comment = PastComment(**base_comment_data)
        assert comment.matches_weather_condition(target_condition, fuzzy=fuzzy) == expected_match

    @pytest.mark.parametrize("weather,temp,location,expected_range", [
        ("晴れ", 22.5, "東京", (0.99, 1.0)),  # 完全一致
        ("晴れ", 25.0, "大阪", (0.5, 0.8)),  # 部分的一致
        ("雨", 5.0, "札幌", (0.0, 0.5)),  # 一致しない条件
    ])
    def test_similarity_calculation_with_range(self, base_comment_data, weather, temp, location, expected_range):
        """類似度計算のテスト（範囲指定）"""
        comment = PastComment(**base_comment_data)
        score = comment.calculate_similarity_score(weather, temp, location)
        assert expected_range[0] <= score <= expected_range[1]

    @pytest.mark.parametrize("weather,temp,location,expected_score", [
        ("晴れ", 22.5, "東京", 1.0),  # 完全一致: 天気1.0 * 温度1.0 * 地点1.0 = 1.0
        ("晴れ", 22.5, "大阪", 0.8),  # 天気一致(0.5)、温度一致(0.3)、地点不一致(0.0) = 0.8
        ("曇り", 22.5, "東京", 0.5),  # 天気不一致(0.0)、温度一致(0.3)、地点一致(0.2) = 0.5
        ("晴れ", 17.5, "東京", 0.85),  # 天気一致(0.5)、温度5度差(0.3*0.5=0.15)、地点一致(0.2) = 0.85
        ("晴れ", 12.5, "東京", 0.7),  # 天気一致(0.5)、温度10度差(0.3*0=0)、地点一致(0.2) = 0.7
    ])
    def test_similarity_calculation_exact_values(self, base_comment_data, weather, temp, location, expected_score):
        """類似度計算のテスト（具体的な期待値）"""
        comment = PastComment(**base_comment_data)
        score = comment.calculate_similarity_score(weather, temp, location)
        assert abs(score - expected_score) < 0.01  # 浮動小数点の誤差を考慮

    def test_to_dict_conversion(self):
        """辞書変換のテスト"""
        comment = PastComment(
            location="福岡",
            datetime=datetime(2024, 6, 5, 15, 0),
            weather_condition="曇り",
            comment_text="少し肌寒いです",
            comment_type=CommentType.ADVICE,
            temperature=18.0,
        )

        comment_dict = comment.to_dict()

        assert comment_dict["location"] == "福岡"
        assert comment_dict["comment_text"] == "少し肌寒いです"
        assert comment_dict["comment_type"] == "advice"
        assert comment_dict["temperature"] == 18.0

    def test_from_dict_creation(self):
        """辞書からの生成テスト"""
        data = {
            "location": "札幌",
            "datetime": "2024-06-05T09:00:00+09:00",
            "weather_condition": "雪",
            "comment_text": "防寒対策必須",
            "comment_type": "advice",
            "temperature": -2.0,
        }

        comment = PastComment.from_dict(data)

        assert comment.location == "札幌"
        assert comment.weather_condition == "雪"
        assert comment.comment_type == CommentType.ADVICE
        assert comment.temperature == -2.0


class TestPastCommentCollection:
    """PastCommentCollection クラスのテスト"""

    def test_collection_creation(self, sample_comments):
        """コレクション作成のテスト"""
        collection = PastCommentCollection(comments=sample_comments[:2], source_period="202406")

        assert len(collection.comments) == 2
        assert collection.source_period == "202406"

    @pytest.mark.parametrize("filter_value,exact_match,expected_count,expected_location", [
        ("東京", True, 2, "東京"),  # 完全一致で2件
        ("大阪", True, 1, "大阪"),  # 完全一致で1件
        ("東", False, 2, "東京"),  # 部分一致で2件（東京のみ）
        ("京", False, 2, None),  # 部分一致で2件（東京のみ、大阪は含まれない）
    ])
    def test_filter_by_location(self, sample_comments, filter_value, exact_match, expected_count, expected_location):
        """地点フィルタリングのテスト"""
        collection = PastCommentCollection(comments=sample_comments)
        filtered = collection.filter_by_location(filter_value, exact_match=exact_match)

        assert len(filtered.comments) == expected_count
        if expected_location:
            assert all(c.location == expected_location for c in filtered.comments)

    @pytest.mark.parametrize("weather_condition,fuzzy,expected_count", [
        ("晴れ", False, 2),  # 完全一致で2件
        ("曇り", False, 1),  # 完全一致で1件
        ("晴", True, 2),  # あいまい検索で2件
        ("雨", True, 0),  # あいまい検索で0件
    ])
    def test_filter_by_weather_condition(self, sample_comments, weather_condition, fuzzy, expected_count):
        """天気状況フィルタリングのテスト"""
        collection = PastCommentCollection(comments=sample_comments)
        filtered = collection.filter_by_weather_condition(weather_condition, fuzzy=fuzzy)

        assert len(filtered.comments) == expected_count

    @pytest.mark.parametrize("comment_type,expected_count,expected_text", [
        (CommentType.WEATHER_COMMENT, 2, ["良い天気", "過ごしやすい"]),
        (CommentType.ADVICE, 1, ["日焼け注意"]),
        (CommentType.UNKNOWN, 0, []),
    ])
    def test_filter_by_comment_type(self, sample_comments, comment_type, expected_count, expected_text):
        """コメントタイプフィルタリングのテスト"""
        collection = PastCommentCollection(comments=sample_comments)
        filtered = collection.filter_by_comment_type(comment_type)

        assert len(filtered.comments) == expected_count
        if expected_text:
            actual_texts = [c.comment_text for c in filtered.comments]
            assert sorted(actual_texts) == sorted(expected_text)

    def test_get_similar_comments(self):
        """類似コメント取得のテスト"""
        comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="暖かい",
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=25.0,
            ),
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="暑い",
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=30.0,
            ),
            PastComment(
                location="大阪",
                datetime=datetime.now(),
                weather_condition="雨",
                comment_text="濡れる",
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=20.0,
            ),
        ]

        collection = PastCommentCollection(comments=comments)

        # 晴れ、27度、東京に類似するコメント
        similar = collection.get_similar_comments(
            target_weather_condition="晴れ",
            target_temperature=27.0,
            target_location="東京",
            min_similarity=0.5,
            max_results=5,
        )

        # 2つの晴れコメントが類似として取得される
        assert len(similar) == 2
        # 類似度でソートされている（30度より25度の方が27度に近い）
        assert similar[0].temperature == 25.0
        assert similar[1].temperature == 30.0

    def test_get_statistics(self):
        """統計情報取得のテスト"""
        comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="短い",  # 2文字
                comment_type=CommentType.WEATHER_COMMENT,
            ),
            PastComment(
                location="大阪",
                datetime=datetime.now(),
                weather_condition="曇り",
                comment_text="これは少し長めのコメントです",  # 14文字
                comment_type=CommentType.ADVICE,
            ),
        ]

        collection = PastCommentCollection(comments=comments)
        stats = collection.get_statistics()

        assert stats["total_comments"] == 2
        assert stats["type_distribution"]["weather_comment"] == 1
        assert stats["type_distribution"]["advice"] == 1
        assert stats["character_stats"]["min_length"] == 2
        assert stats["character_stats"]["max_length"] == 14
        assert stats["character_stats"]["within_15_chars"] == 2


class TestCommentType:
    """CommentType 列挙型のテスト"""

    @pytest.mark.parametrize("comment_type,expected_str_value", [
        (CommentType.WEATHER_COMMENT, "weather_comment"),
        (CommentType.ADVICE, "advice"),
        (CommentType.UNKNOWN, "unknown"),
    ])
    def test_comment_type_values(self, comment_type, expected_str_value):
        """コメントタイプの値テスト"""
        assert comment_type.value == expected_str_value


if __name__ == "__main__":
    pytest.main([__file__])

"""
過去コメントデータ管理（リファクタリング版）

ローカルCSVファイルから取得する過去コメントデータの構造化と管理を行う
元の507行のファイルを責務ごとに分割し、後方互換性を維持
"""

# 分割されたモジュールから再エクスポート

from __future__ import annotations
from src.data.past_comment.models import PastComment, CommentType
from src.data.past_comment.collection import PastCommentCollection
from src.data.past_comment.similarity import matches_weather_condition, calculate_similarity_score

# 後方互換性のため、PastCommentクラスにメソッドを追加
# 注意: 循環インポートを避けるため、lambdaの使用は避け、通常の関数として定義
def _matches_weather_condition(self, target, fuzzy=True):
    return matches_weather_condition(self.weather_condition, target, fuzzy)

def _calculate_similarity_score(self, target_weather, target_temp=None, target_humidity=None):
    return calculate_similarity_score(
        self.weather_condition, self.temperature, self.humidity,
        target_weather, target_temp, target_humidity
    )

PastComment.matches_weather_condition = _matches_weather_condition
PastComment.calculate_similarity_score = _calculate_similarity_score

__all__ = [
    "PastComment",
    "CommentType", 
    "PastCommentCollection",
]


# テストデータ（後方互換性のため残す）
if __name__ == "__main__":
    import json
    from datetime import datetime

    # テストデータ作成
    test_data = [
        {
            "location": "東京",
            "datetime": "2024-06-05T09:00:00+09:00",
            "weather_condition": "晴れ",
            "comment_text": "今日は快適な一日になりそうです",
            "comment_type": "weather_comment",
            "temperature": 22.5,
            "humidity": 60,
        },
        {
            "location": "東京",
            "datetime": "2024-06-05T12:00:00+09:00",
            "weather_condition": "晴れ",
            "comment_text": "紫外線対策をお忘れなく",
            "comment_type": "advice",
            "temperature": 26.0,
            "humidity": 55,
        },
    ]

    # PastCommentの作成とテスト
    comments = []
    for data in test_data:
        comment = PastComment.from_dict(data)
        comments.append(comment)
        print(f"Created: {comment.location} - {comment.comment_text}")

    # PastCommentCollectionのテスト
    collection = PastCommentCollection(comments=comments)
    print(f"\nCollection size: {len(collection)}")

    # フィルタリングテスト
    weather_comments = collection.filter_by_comment_type(CommentType.WEATHER_COMMENT)
    print(f"Weather comments: {len(weather_comments)}")

    # 統計情報テスト
    stats = collection.get_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2, ensure_ascii=False)}")
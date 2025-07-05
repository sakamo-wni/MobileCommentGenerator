"""ローカルCSVファイルからコメントデータを遅延読み込みするリポジトリ（将来の改善案）"""

import csv
import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from src.data.past_comment import CommentType, PastComment

logger = logging.getLogger(__name__)


class LazyLocalCommentRepository:
    """遅延読み込み版のローカルコメントリポジトリ

    大規模なCSVファイルに対応するため、必要な時にのみファイルを読み込む実装。
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        if not self.output_dir.exists():
            logger.warning(f"Output directory not found: {output_dir}, creating it...")
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def _iter_csv_comments(self, file_path: Path, comment_type: str) -> Iterator[PastComment]:
        """CSVファイルからコメントを逐次読み込み（メモリ効率的）"""
        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return

        try:
            with open(file_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    comment_text = row.get("weather_comment") or row.get("advice", "")
                    count = int(row.get("count", 0))

                    if comment_text:
                        yield PastComment(
                            location="全国",
                            datetime=datetime.now(),
                            weather_condition="不明",
                            comment_text=comment_text,
                            comment_type=CommentType.WEATHER_COMMENT if comment_type == "weather_comment" else CommentType.ADVICE,
                            raw_data={
                                "count": count,
                                "source": "local_csv",
                                "file": file_path.name,
                            },
                        )

        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")

    def get_comments_paginated(self, season: str, comment_type: str, page: int = 1, page_size: int = 50) -> list[PastComment]:
        """ページネーション付きでコメントを取得"""
        file_name = f"{season}_{comment_type}_enhanced100.csv"
        file_path = self.output_dir / file_name

        comments = []
        start_idx = (page - 1) * page_size
        end_idx = page * page_size

        for idx, comment in enumerate(self._iter_csv_comments(file_path, comment_type)):
            if idx < start_idx:
                continue
            if idx >= end_idx:
                break
            comment.raw_data["season"] = season
            comments.append(comment)

        return comments

    def count_comments(self, season: str, comment_type: str) -> int:
        """コメントの総数をカウント（メタデータとして保存することも可能）"""
        file_name = f"{season}_{comment_type}_enhanced100.csv"
        file_path = self.output_dir / file_name

        count = 0
        for _ in self._iter_csv_comments(file_path, comment_type):
            count += 1

        return count

    def search_comments(self, keyword: str, limit: int = 100) -> list[PastComment]:
        """キーワード検索（逐次処理でメモリ効率的）"""
        results = []
        seasons = ["春", "夏", "秋", "冬", "梅雨", "台風"]
        types = ["weather_comment", "advice"]

        for season in seasons:
            for comment_type in types:
                file_name = f"{season}_{comment_type}_enhanced100.csv"
                file_path = self.output_dir / file_name

                for comment in self._iter_csv_comments(file_path, comment_type):
                    if keyword in comment.comment_text:
                        comment.raw_data["season"] = season
                        results.append(comment)

                        if len(results) >= limit:
                            return results

        return results

    def get_top_comments_by_season(self, season: str, top_n: int = 10) -> list[PastComment]:
        """指定季節の人気上位コメントを取得（count順でソート済みと仮定）"""
        weather_comments = []
        advice_comments = []

        # Weather comments
        weather_file = self.output_dir / f"{season}_weather_comment_enhanced100.csv"
        for idx, comment in enumerate(self._iter_csv_comments(weather_file, "weather_comment")):
            if idx >= top_n:
                break
            comment.raw_data["season"] = season
            weather_comments.append(comment)

        # Advice comments
        advice_file = self.output_dir / f"{season}_advice_enhanced100.csv"
        for idx, comment in enumerate(self._iter_csv_comments(advice_file, "advice")):
            if idx >= top_n:
                break
            comment.raw_data["season"] = season
            advice_comments.append(comment)

        return weather_comments + advice_comments

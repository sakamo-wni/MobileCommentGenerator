"""
S3過去コメントリポジトリ - DEPRECATED

注意: このモジュールは古い実装です。
現在、システムはS3の代わりにローカルCSVファイルを使用するように変更されました。
新しい実装については、local_comment_repository.pyを参照してください。

S3バケットから過去コメントJSONLファイルを取得・解析する
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import warnings
from io import StringIO

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from src.data.past_comment import PastComment, PastCommentCollection, CommentType


# ログ設定
logger = logging.getLogger(__name__)


class S3CommentRepositoryError(Exception):
    """S3コメントリポジトリ関連のエラー"""

    pass


class S3CommentRepository:
    """S3から過去コメントデータを取得するリポジトリクラス

    S3バケット: it-literacy-457604437098-ap-northeast-1
    パス構造: downloaded_jsonl_files_archive/YYYYMM/YYYYMM.jsonl
    """

    def __init__(
        self,
        bucket_name: str = "it-literacy-457604437098-ap-northeast-1",
        region_name: str = "ap-northeast-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_profile: Optional[str] = None,
    ):
        """S3コメントリポジトリを初期化

        Args:
            bucket_name: S3バケット名
            region_name: AWSリージョン
            aws_access_key_id: AWSアクセスキーID（Noneの場合は環境変数から取得）
            aws_secret_access_key: AWSシークレットアクセスキー
            aws_profile: AWSプロファイル名（Noneの場合は環境変数から取得）
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        
        # 現在の月に基づいて適切な期間を設定
        current_month = datetime.now().month
        
        # 季節に応じた期間選択（過去データは201807から202505まで）
        if current_month in [6, 7]:  # 6月、7月（梅雨〜初夏）
            self.ALLOWED_PERIODS = ["202306", "202406", "202506", "202307", "202407", 
                                   "202206", "202207", "202106", "202107", "201906", "201907"]
            logger.info(f"6月/7月の梅雨〜初夏期間を使用: {self.ALLOWED_PERIODS[:5]}...")
        elif current_month in [12, 1, 2]:  # 冬
            self.ALLOWED_PERIODS = ["202312", "202412", "202501", "202502", "202401", "202402",
                                   "202212", "202301", "202302", "202112", "202201", "202202"]
        elif current_month in [3, 4, 5]:  # 春
            self.ALLOWED_PERIODS = ["202303", "202304", "202305", "202403", "202404", "202405", 
                                   "202203", "202204", "202205", "202103", "202104", "202105"]
        elif current_month in [8, 9, 10, 11]:  # 夏〜秋
            self.ALLOWED_PERIODS = ["202308", "202309", "202310", "202311", "202408", "202409", 
                                   "202410", "202411", "202208", "202209", "202210", "202211"]
        else:
            # デフォルト（全期間から最近のもの）
            self.ALLOWED_PERIODS = ["202505", "202504", "202503", "202502", "202501", 
                                   "202412", "202411", "202410", "202409", "202408"]

        # S3クライアントの初期化
        try:
            # プロファイルが指定されている場合
            if aws_profile or os.getenv("AWS_PROFILE"):
                profile_name = aws_profile or os.getenv("AWS_PROFILE")
                logger.info(f"AWSプロファイル '{profile_name}' を使用してS3クライアントを初期化")
                try:
                    session = boto3.Session(profile_name=profile_name)
                    # セッションの認証情報を確認
                    credentials = session.get_credentials()
                    if credentials:
                        logger.info(f"プロファイル '{profile_name}' の認証情報を取得成功")
                        logger.info(f"  Access Key ID: {credentials.access_key[:8]}...")
                    else:
                        logger.error(f"プロファイル '{profile_name}' の認証情報を取得できません")
                    self.s3_client = session.client("s3", region_name=region_name)
                except Exception as e:
                    logger.error(
                        f"プロファイル '{profile_name}' でのセッション作成に失敗: {str(e)}"
                    )
                    raise
            elif aws_access_key_id and aws_secret_access_key:
                self.s3_client = boto3.client(
                    "s3",
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                )
            else:
                # 環境変数またはIAMロールから認証情報を取得
                self.s3_client = boto3.client("s3", region_name=region_name)

        except (NoCredentialsError, PartialCredentialsError) as e:
            raise S3CommentRepositoryError(f"AWS認証情報が設定されていません: {str(e)}")
        except Exception as e:
            raise S3CommentRepositoryError(f"S3クライアントの初期化に失敗: {str(e)}")

    def test_connection(self) -> bool:
        """S3接続をテスト

        Returns:
            接続成功の場合True
        """
        try:
            # バケットの存在確認
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3バケット '{self.bucket_name}' への接続成功")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                logger.error(f"S3バケット '{self.bucket_name}' が見つかりません")
            elif error_code == "403":
                logger.error(f"S3バケット '{self.bucket_name}' へのアクセス権限がありません")
            else:
                logger.error(f"S3接続エラー: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"S3接続テストでエラー: {str(e)}")
            return False

    def list_available_periods(self) -> List[str]:
        """利用可能な期間（YYYYMM）のリストを取得

        Returns:
            利用可能な期間のリスト（YYYYMM形式）
        """
        try:
            # downloaded_jsonl_files_archive/ 配下のフォルダ一覧を取得
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix="downloaded_jsonl_files_archive/", Delimiter="/"
            )

            periods = []
            for prefix in response.get("CommonPrefixes", []):
                # downloaded_jsonl_files_archive/YYYYMM/ から YYYYMM を抽出
                folder_path = prefix["Prefix"]
                match = re.search(r"downloaded_jsonl_files_archive/(\d{6})/", folder_path)
                if match:
                    period = match.group(1)
                    # ALLOWED_PERIODSに含まれる期間のみを使用
                    if period in self.ALLOWED_PERIODS:
                        periods.append(period)

            periods.sort(reverse=True)  # 新しい順でソート
            logger.info(
                f"利用可能な期間: {len(periods)}件 ({periods[:5]}...)"
                if len(periods) > 5
                else f"利用可能な期間: {periods}"
            )
            return periods

        except ClientError as e:
            logger.error(f"期間リスト取得エラー: {str(e)}")
            raise S3CommentRepositoryError(f"期間リストの取得に失敗: {str(e)}")

    def fetch_comments_by_period(
        self, period: str, location: Optional[str] = None, weather_condition: Optional[str] = None
    ) -> PastCommentCollection:
        """指定期間の過去コメントを取得

        Args:
            period: 期間（YYYYMM形式）
            location: 地点名でのフィルタリング（オプション）
            weather_condition: 天気状況でのフィルタリング（オプション）

        Returns:
            過去コメントコレクション

        Raises:
            S3CommentRepositoryError: データ取得に失敗した場合
        """
        # 期間フォーマットの検証
        if not re.match(r"^\d{6}$", period):
            raise ValueError(f"期間は YYYYMM 形式で指定してください: {period}")

        # ファイルパスの構築
        file_key = f"downloaded_jsonl_files_archive/{period}/{period}.jsonl"

        try:
            # S3からファイルを取得
            logger.info(f"S3ファイル取得開始: {file_key}")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)

            # JSONLファイルの内容を読み取り
            content = response["Body"].read().decode("utf-8")

            # JSONLデータの解析
            comments = self._parse_jsonl_content(content, file_key)

            # コレクション作成
            collection = PastCommentCollection(comments=comments, source_period=period)

            # フィルタリング適用
            if location:
                collection = collection.filter_by_location(location)

            if weather_condition:
                collection = collection.filter_by_weather_condition(weather_condition)

            logger.info(f"コメント取得完了: {len(collection.comments)}件 (期間: {period})")
            return collection

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                logger.warning(f"ファイルが見つかりません: {file_key}")
                return PastCommentCollection(comments=[], source_period=period)
            else:
                logger.error(f"S3ファイル取得エラー: {str(e)}")
                raise S3CommentRepositoryError(f"ファイル取得に失敗: {str(e)}")

    def fetch_comments_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        location: Optional[str] = None,
        weather_condition: Optional[str] = None,
        max_periods: int = 12,
    ) -> PastCommentCollection:
        """日付範囲指定で過去コメントを取得

        Args:
            start_date: 開始日
            end_date: 終了日
            location: 地点名でのフィルタリング
            weather_condition: 天気状況でのフィルタリング
            max_periods: 最大取得期間数（パフォーマンス制限）

        Returns:
            過去コメントコレクション
        """
        if start_date > end_date:
            raise ValueError("開始日は終了日より前である必要があります")

        # 対象期間のリストを生成
        periods = []
        current_date = start_date.replace(day=1)  # 月初に調整

        while current_date <= end_date and len(periods) < max_periods:
            period = current_date.strftime("%Y%m")
            # ALLOWED_PERIODSに含まれる期間のみを使用
            if period in self.ALLOWED_PERIODS:
                periods.append(period)

            # 次の月へ
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        logger.info(
            f"日付範囲での取得: {start_date.date()} - {end_date.date()} ({len(periods)}期間)"
        )

        # 複数期間のコメントを結合
        all_comments = []

        for period in periods:
            try:
                period_collection = self.fetch_comments_by_period(
                    period, location, weather_condition
                )

                # 日付範囲内のコメントのみを追加
                for comment in period_collection.comments:
                    if start_date <= comment.datetime <= end_date:
                        all_comments.append(comment)

            except S3CommentRepositoryError as e:
                logger.warning(f"期間 {period} のデータ取得に失敗: {str(e)}")
                continue

        return PastCommentCollection(
            comments=all_comments, source_period=f"{periods[0]}-{periods[-1]}" if periods else None
        )

    def get_recent_comments(
        self,
        months_back: int = 3,
        location: Optional[str] = None,
        weather_condition: Optional[str] = None,
        max_comments: int = 100,
    ) -> PastCommentCollection:
        """最近の過去コメントを取得

        Args:
            months_back: 何ヶ月前まで取得するか
            location: 地点名でのフィルタリング
            weather_condition: 天気状況でのフィルタリング
            max_comments: 最大コメント数

        Returns:
            過去コメントコレクション
        """
        # ALLOWED_PERIODSから直接データを取得
        all_comments = []
        periods_to_fetch = self.ALLOWED_PERIODS[:months_back] if months_back < len(self.ALLOWED_PERIODS) else self.ALLOWED_PERIODS
        
        logger.info(f"取得対象期間: {periods_to_fetch}")
        
        for period in periods_to_fetch:
            try:
                collection = self.fetch_comments_by_period(period, location, weather_condition)
                all_comments.extend(collection.comments)
                logger.info(f"期間 {period} から {len(collection.comments)} 件のコメントを取得")
            except Exception as e:
                logger.warning(f"期間 {period} のデータ取得に失敗: {str(e)}")
                continue
        
        # コレクション作成
        collection = PastCommentCollection(
            comments=all_comments,
            source_period=f"{periods_to_fetch[0]}-{periods_to_fetch[-1]}" if periods_to_fetch else None
        )
        
        # コメント数制限
        if len(collection.comments) > max_comments:
            # 日付が新しい順にソートして上位を取得
            collection.comments.sort(key=lambda c: c.datetime, reverse=True)
            collection.comments = collection.comments[:max_comments]
            logger.info(f"コメント数を {max_comments} 件に制限")

        return collection

    def search_similar_comments(
        self,
        target_weather_condition: str,
        target_temperature: Optional[float] = None,
        target_location: Optional[str] = None,
        months_back: int = 6,
        max_results: int = 20,
        min_similarity: float = 0.3,
    ) -> List[PastComment]:
        """類似コメントを検索

        Args:
            target_weather_condition: 対象の天気状況
            target_temperature: 対象の気温
            target_location: 対象の地点
            months_back: 検索対象期間（月数）
            max_results: 最大結果数
            min_similarity: 最小類似度

        Returns:
            類似度順にソートされたコメントリスト
        """
        # 最近のコメントを取得
        collection = self.get_recent_comments(
            months_back=months_back, max_comments=3000  # 検索対象をもっと多めに取得
        )

        # 類似度計算で絞り込み
        similar_comments = collection.get_similar_comments(
            target_weather_condition=target_weather_condition,
            target_temperature=target_temperature,
            target_location=target_location,
            min_similarity=min_similarity,
            max_results=max_results,
        )

        logger.info(f"類似コメント検索: {len(similar_comments)}件見つかりました")
        return similar_comments

    def _parse_jsonl_content(self, content: str, source_file: str) -> List[PastComment]:
        """JSONLファイルの内容を解析

        Args:
            content: JSONLファイルの内容
            source_file: ソースファイル名

        Returns:
            過去コメントのリスト
        """
        comments = []
        lines = content.strip().split("\n")

        # source_fileから期間(YYYYMM)を抽出
        period_match = re.search(r"/(\d{6})/\d{6}\.jsonl", source_file)
        period = period_match.group(1) if period_match else None

        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue

            try:
                data = json.loads(line)

                # JSONLファイルのフォーマットに合わせて変換
                # 1. weather_commentのコメントを作成
                if "weather_comment" in data and data["weather_comment"]:
                    weather_data = data.copy()
                    weather_data["comment_text"] = data["weather_comment"]
                    weather_data["comment_type"] = "weather_comment"

                    # 必須フィールドの追加
                    if "datetime" not in weather_data:
                        # 期間から適切な日時を生成（期間の中央日）
                        if period:
                            try:
                                year = int(period[:4])
                                month = int(period[4:6])
                                # 月の15日をデフォルトとする
                                weather_data["datetime"] = datetime(year, month, 15).isoformat()
                            except:
                                weather_data["datetime"] = datetime.now().isoformat()
                        else:
                            weather_data["datetime"] = datetime.now().isoformat()

                    if "weather_condition" not in weather_data:
                        # weather_commentから天気を推測
                        comment_text = data["weather_comment"]
                        if "晴" in comment_text:
                            weather_data["weather_condition"] = "晴れ"
                        elif "雨" in comment_text:
                            weather_data["weather_condition"] = "雨"
                        elif "曇" in comment_text:
                            weather_data["weather_condition"] = "曇り"
                        elif "雪" in comment_text:
                            weather_data["weather_condition"] = "雪"
                        else:
                            weather_data["weather_condition"] = "不明"

                    try:
                        weather_comment = PastComment.from_dict(weather_data, source_file)
                        comments.append(weather_comment)
                    except Exception as e:
                        logger.debug(f"Weather comment creation failed: {str(e)}")

                # 2. adviceのコメントを作成（adviceが存在し、空でない場合）
                if "advice" in data and data["advice"]:
                    advice_data = data.copy()
                    advice_data["comment_text"] = data["advice"]
                    advice_data["comment_type"] = "advice"

                    # 必須フィールドの追加
                    if "datetime" not in advice_data:
                        # 期間から適切な日時を生成（期間の中央日）
                        if period:
                            try:
                                year = int(period[:4])
                                month = int(period[4:6])
                                # 月の15日をデフォルトとする
                                advice_data["datetime"] = datetime(year, month, 15).isoformat()
                            except:
                                advice_data["datetime"] = datetime.now().isoformat()
                        else:
                            advice_data["datetime"] = datetime.now().isoformat()

                    if "weather_condition" not in advice_data:
                        advice_data["weather_condition"] = "不明"

                    try:
                        advice_comment = PastComment.from_dict(advice_data, source_file)
                        comments.append(advice_comment)
                    except Exception as e:
                        logger.debug(f"Advice comment creation failed: {str(e)}")

            except json.JSONDecodeError as e:
                logger.warning(f"JSONデコードエラー {source_file}:{line_num}: {str(e)}")
                continue
            except ValueError as e:
                logger.warning(f"データ検証エラー {source_file}:{line_num}: {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"コメント解析エラー {source_file}:{line_num}: {str(e)}")
                continue

        logger.info(f"JSONLファイル解析完了: {len(comments)}件 (総行数: {len(lines)})")
        return comments

    def get_repository_statistics(self) -> Dict[str, Any]:
        """リポジトリの統計情報を取得

        Returns:
            統計情報の辞書
        """
        try:
            available_periods = self.list_available_periods()

            # 最新期間のサンプルデータを取得
            sample_stats = {}
            if available_periods:
                latest_period = available_periods[0]
                try:
                    sample_collection = self.fetch_comments_by_period(latest_period)
                    sample_stats = sample_collection.get_statistics()
                except Exception as e:
                    logger.warning(f"サンプル統計取得エラー: {str(e)}")

            return {
                "bucket_name": self.bucket_name,
                "region_name": self.region_name,
                "available_periods_count": len(available_periods),
                "latest_period": available_periods[0] if available_periods else None,
                "oldest_period": available_periods[-1] if available_periods else None,
                "sample_statistics": sample_stats,
                "connection_status": "connected" if self.test_connection() else "disconnected",
            }

        except Exception as e:
            logger.error(f"統計情報取得エラー: {str(e)}")
            return {"error": str(e), "connection_status": "error"}


# 設定管理クラス
class S3CommentRepositoryConfig:
    """S3コメントリポジトリの設定管理"""

    def __init__(self):
        import os

        self.bucket_name = os.getenv("S3_COMMENT_BUCKET", "it-literacy-457604437098-ap-northeast-1")
        self.region_name = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_profile = os.getenv("AWS_PROFILE")

    def create_repository(self) -> S3CommentRepository:
        """設定からリポジトリインスタンスを作成

        Returns:
            S3CommentRepositoryインスタンス
        """
        return S3CommentRepository(
            bucket_name=self.bucket_name,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_profile=self.aws_profile,
        )


if __name__ == "__main__":
    # テスト用コード
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # リポジトリのテスト
    config = S3CommentRepositoryConfig()

    try:
        repo = config.create_repository()

        # 接続テスト
        if repo.test_connection():
            print("✅ S3接続成功")

            # 利用可能期間の取得
            periods = repo.list_available_periods()
            print(f"📅 利用可能期間: {len(periods)}件")

            if periods:
                # 最新期間のデータを少し取得
                latest_period = periods[0]
                collection = repo.fetch_comments_by_period(latest_period)
                print(f"📝 最新期間({latest_period})のコメント: {len(collection.comments)}件")

                # 統計情報
                stats = collection.get_statistics()
                print(f"📊 統計情報: {stats}")

        else:
            print("❌ S3接続失敗")

    except Exception as e:
        print(f"❌ エラー: {str(e)}")

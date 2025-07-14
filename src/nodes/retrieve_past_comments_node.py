"""過去コメント取得ノード - ローカルCSVファイルから過去コメントを取得"""

import logging
from datetime import datetime
from typing import Dict, Any

from src.data.past_comment import CommentType
from src.data.weather_data import WeatherForecast
from src.repositories.lazy_comment_repository import LazyCommentRepository

logger = logging.getLogger(__name__)


def retrieve_past_comments_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraphノード関数 - 過去コメントを取得
    
    Args:
        state: LangGraphの状態辞書
        
    Returns:
        更新された状態辞書
    """
    try:
        logger.info("過去コメント取得ノード開始")
        
        location_name = state.location_name
        weather_data = state.weather_data
        
        if not location_name:
            raise ValueError("location_name が指定されていません")
            
        # リポジトリ初期化（LazyCommentRepositoryのみを使用）
        logger.info("Using lazy-loading CSV repository")
        repository = LazyCommentRepository()
        
        # WeatherForecastチェック（並列実行対応）
        if weather_data is not None and not isinstance(weather_data, WeatherForecast):
            logger.warning("weather_data is not a WeatherForecast object")
            # 並列実行時はweather_dataがまだ設定されていない可能性があるため、処理を続行
            
        # コメント取得
        past_comments = repository.get_recent_comments(
            limit=180  # 各季節から最大15個ずつ取得 (15 * 2 types * 6 seasons = 180)
        )
        
        # メタデータ生成
        type_counts = {
            "weather_comment": sum(1 for c in past_comments if c.comment_type == CommentType.WEATHER_COMMENT),
            "advice": sum(1 for c in past_comments if c.comment_type == CommentType.ADVICE),
        }
        
        metadata = {
            "total_comments": len(past_comments),
            "search_location": location_name,
            "type_distribution": type_counts,
            "retrieval_successful": True,
            "retrieval_timestamp": datetime.now().isoformat(),
        }
        
        # weather_dataが利用可能な場合のみ天気情報を追加
        if weather_data is not None and isinstance(weather_data, WeatherForecast):
            metadata["weather_condition"] = weather_data.weather_description
            metadata["temperature"] = weather_data.temperature
        
        # 状態更新
        state.past_comments = past_comments
        state.update_metadata("comment_retrieval_metadata", metadata)
        
        logger.info(f"過去コメント取得完了: {len(past_comments)}件")
        return state
        
    except Exception as e:
        logger.error(f"過去コメント取得エラー: {str(e)}")
        
        # エラー時も処理を継続
        state.past_comments = []
        state.update_metadata("comment_retrieval_metadata", {
            "error": str(e),
            "error_type": type(e).__name__,
            "total_comments": 0,
            "retrieval_successful": False,
            "suggestion": "output/ディレクトリにCSVファイルが存在することを確認してください" if "FileNotFoundError" in str(e) else None
        })
        return state
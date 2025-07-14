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
            
        # 現在の月から関連する季節を決定
        target_datetime = state.target_datetime or datetime.now()
        month = target_datetime.month
        
        # 月ごとの関連季節マッピング
        season_mapping = {
            1: ["冬"],  # 1月
            2: ["冬"],  # 2月
            3: ["冬", "春"],  # 3月（季節の変わり目）
            4: ["春"],  # 4月
            5: ["春", "梅雨"],  # 5月（梅雨の始まり）
            6: ["梅雨", "夏"],  # 6月
            7: ["夏", "梅雨", "台風"],  # 7月
            8: ["夏", "台風"],  # 8月
            9: ["夏", "台風", "秋"],  # 9月
            10: ["秋", "台風"],  # 10月
            11: ["秋"],  # 11月
            12: ["冬"],  # 12月
        }
        
        relevant_seasons = season_mapping.get(month, ["春", "夏", "秋", "冬"])
        logger.info(f"{month}月のため、関連季節: {relevant_seasons}")
        
        # リポジトリ初期化（関連季節のみを読み込む）
        logger.info("Using lazy-loading CSV repository with seasonal filtering")
        repository = LazyCommentRepository(seasons=relevant_seasons)
        
        # WeatherForecastチェック（並列実行対応）
        if weather_data is not None and not isinstance(weather_data, WeatherForecast):
            logger.warning("weather_data is not a WeatherForecast object")
            # 並列実行時はweather_dataがまだ設定されていない可能性があるため、処理を続行
            
        # コメント取得（関連季節のみから取得）
        past_comments = repository.get_recent_comments(
            limit=100  # 季節を絞ったので件数を減らす
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
"""
Comment filters for unified comment generation

コメントのフィルタリング処理
"""

from __future__ import annotations

import logging
from src.data.past_comment import PastComment
from src.data.comment_generation_state import CommentGenerationState
from src.constants.content_constants import FORBIDDEN_PHRASES
from src.constants.weather_constants import COMMENT

logger = logging.getLogger(__name__)


def check_continuous_rain(state: CommentGenerationState) -> bool:
    """連続雨かどうかを判定
    
    Args:
        state: コメント生成状態
        
    Returns:
        連続雨の場合True
    """
    if not state.generation_metadata:
        return False
        
    period_forecasts = state.generation_metadata.get('period_forecasts', [])
    if not period_forecasts:
        return False
    
    # 天気が「雨」または降水量が0.1mm以上の時間をカウント
    rain_hours = sum(1 for f in period_forecasts 
                   if (hasattr(f, 'weather') and f.weather == "雨") or 
                      (hasattr(f, 'precipitation') and f.precipitation >= 0.1))
    
    is_continuous = rain_hours >= COMMENT.CONTINUOUS_RAIN_HOURS
    
    if is_continuous:
        logger.info(f"連続雨を検出: {rain_hours}時間の雨（9,12,15,18時）")
        # デバッグ用：各時間の天気情報をログ出力
        for f in period_forecasts:
            time_str = f.datetime.strftime('%H時') if hasattr(f, 'datetime') else '不明'
            weather = f.weather if hasattr(f, 'weather') else '不明'
            precip = f.precipitation if hasattr(f, 'precipitation') else 0
            logger.debug(f"  {time_str}: {weather}, 降水量{precip}mm")
    
    return is_continuous


def filter_shower_comments(comments: list[PastComment]) -> list[PastComment]:
    """にわか雨関連のコメントをフィルタリング（連続雨の場合）
    
    Args:
        comments: コメントリスト
        
    Returns:
        フィルタリング後のコメントリスト
    """
    shower_keywords = ["にわか雨", "一時的な雨", "急な雨", "突然の雨", "通り雨"]
    
    filtered = []
    for comment in comments:
        if not any(keyword in comment.comment_text for keyword in shower_keywords):
            filtered.append(comment)
        else:
            logger.debug(f"連続雨のため除外: {comment.comment_text}")
            
    return filtered if filtered else comments  # 空になった場合は元のリストを返す


def filter_mild_umbrella_comments(comments: list[PastComment]) -> list[PastComment]:
    """控えめな傘表現のコメントをフィルタリング（連続雨の場合）
    
    Args:
        comments: コメントリスト
        
    Returns:
        フィルタリング後のコメントリスト
    """
    mild_expressions = ["傘があると安心", "傘がお守り", "念のため傘", "折りたたみ傘"]
    
    filtered = []
    for comment in comments:
        if not any(expr in comment.comment_text for expr in mild_expressions):
            filtered.append(comment)
        else:
            logger.debug(f"連続雨には不適切な控えめ表現のため除外: {comment.comment_text}")
            
    return filtered if filtered else comments


def filter_forbidden_phrases(comments: list[PastComment]) -> list[PastComment]:
    """禁止フレーズを含むコメントをフィルタリング
    
    Args:
        comments: コメントリスト
        
    Returns:
        フィルタリング後のコメントリスト
    """
    filtered = []
    for comment in comments:
        if not any(phrase in comment.comment_text for phrase in FORBIDDEN_PHRASES):
            filtered.append(comment)
        else:
            logger.debug(f"禁止フレーズを含むため除外: {comment.comment_text}")
    
    return filtered if filtered else comments


def filter_seasonal_inappropriate_comments(comments: list[PastComment], month: int) -> list[PastComment]:
    """季節的に不適切なコメントをフィルタリング
    
    Args:
        comments: コメントリスト
        month: 対象月（1-12）
        
    Returns:
        フィルタリング後のコメントリスト
    """
    # 夏季（6-9月）に不適切な表現
    if 6 <= month <= 9:
        winter_keywords = ["防寒", "冷え込み", "暖房", "あったか", "ホット"]
        filtered = [c for c in comments 
                   if not any(keyword in c.comment_text for keyword in winter_keywords)]
    # 冬季（12-2月）に不適切な表現
    elif month in [12, 1, 2]:
        summer_keywords = ["熱中症", "クーラー", "冷房", "日焼け", "紫外線"]
        filtered = [c for c in comments 
                   if not any(keyword in c.comment_text for keyword in summer_keywords)]
    else:
        filtered = comments
    
    return filtered if filtered else comments
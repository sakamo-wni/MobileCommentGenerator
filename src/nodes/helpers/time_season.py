"""時間帯・季節判定モジュール"""

from typing import Optional
from datetime import datetime
from src.utils.common_utils import get_season_from_month, get_time_period_from_hour


def get_time_period(target_datetime: Optional[datetime]) -> str:
    """時間帯を判定"""
    if not target_datetime:
        target_datetime = datetime.now()
    return get_time_period_from_hour(target_datetime.hour)


def get_season(target_datetime: Optional[datetime]) -> str:
    """季節を判定"""
    if not target_datetime:
        target_datetime = datetime.now()
    return get_season_from_month(target_datetime.month)
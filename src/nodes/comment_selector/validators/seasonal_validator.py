"""季節の妥当性チェックバリデーター"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SeasonalValidator:
    """季節関連のバリデーション"""
    
    def is_inappropriate_seasonal_comment(self, comment_text: str, target_datetime) -> bool:
        """季節に不適切なコメントが含まれているか判定"""
        if not target_datetime:
            return False
        
        month = target_datetime.month
        inappropriate_patterns = self._get_inappropriate_seasonal_patterns(month)
        
        comment_lower = comment_text.lower()
        for pattern in inappropriate_patterns:
            if pattern in comment_lower:
                logger.debug(f"季節に不適切なパターンを検出: {pattern} (月: {month})")
                return True
        
        return False
    
    def _get_inappropriate_seasonal_patterns(self, month: int) -> list[str]:
        """月に応じた不適切な季節パターンを取得"""
        # 春（3-5月）
        if month in [3, 4, 5]:
            return ["紅葉", "落ち葉", "年末", "年始", "初詣", "雪だるま", "かき氷", "海水浴"]
        # 夏（6-8月）
        elif month in [6, 7, 8]:
            return ["紅葉", "落ち葉", "年末", "年始", "初詣", "雪だるま", "桜", "お花見"]
        # 秋（9-11月）
        elif month in [9, 10, 11]:
            return ["桜", "お花見", "海水浴", "かき氷", "年末", "年始", "初詣", "雪だるま"]
        # 冬（12-2月）
        else:
            return ["桜", "お花見", "海水浴", "かき氷", "紅葉", "落ち葉"]
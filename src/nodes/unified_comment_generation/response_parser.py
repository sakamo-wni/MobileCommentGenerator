"""
Response parser for unified comment generation

LLMレスポンスの解析処理
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def parse_unified_response(response: str) -> dict[str, Any]:
    """LLMのレスポンスを解析
    
    Args:
        response: LLMからのレスポンス文字列
        
    Returns:
        解析結果の辞書
        
    Raises:
        ValueError: レスポンスの解析に失敗した場合
    """
    try:
        # JSON部分の抽出（```json ... ``` の形式にも対応）
        json_match = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 単純なJSON形式を試す
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("JSONレスポンスが見つかりません")
        
        parsed = json.loads(json_str)
        
        # 必須フィールドの確認
        required_fields = ['selected_weather_index', 'selected_advice_index', 
                         'weather_comment', 'advice_comment']
        for field in required_fields:
            if field not in parsed:
                logger.warning(f"必須フィールド '{field}' が見つかりません")
                # デフォルト値を設定
                if field == 'selected_weather_index' or field == 'selected_advice_index':
                    parsed[field] = 1
                else:
                    parsed[field] = ""
                    
        return parsed
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析エラー: {e}")
        raise ValueError(f"レスポンスのJSON解析に失敗しました: {e}")
    except Exception as e:
        logger.error(f"レスポンス解析エラー: {e}")
        raise ValueError(f"レスポンスの解析に失敗しました: {e}")
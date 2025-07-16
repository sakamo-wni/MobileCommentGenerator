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
    # デバッグ用: レスポンス全体をログ出力
    logger.debug(f"Full response: {response}")
    logger.debug(f"Response length: {len(response) if response else 0}")
    
    try:
        # JSON部分の抽出（```json ... ``` の形式にも対応）
        # より柔軟なパターンで、改行や空白を考慮
        json_match = re.search(r'```json\s*\n?(.+?)\n?```', response, re.DOTALL | re.IGNORECASE)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # 単純なJSON形式を試す（バランスの取れたブレースを探す）
            # まず最初の{を探す
            start_idx = response.find('{')
            if start_idx != -1:
                # ブレースのバランスをチェックしてJSONを抽出
                brace_count = 0
                in_string = False
                escape_next = False
                end_idx = start_idx
                
                for i in range(start_idx, len(response)):
                    char = response[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                        
                    if char == '\\':
                        escape_next = True
                        continue
                        
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                
                if brace_count == 0:
                    json_str = response[start_idx:end_idx]
                else:
                    # ブレースがバランスしていない場合、切り詰められた可能性
                    logger.warning(f"JSONが切り詰められている可能性があります。ブレースカウント: {brace_count}")
                    json_str = response[start_idx:]
            else:
                # より緩い形式も試す（バックティックなしのjson形式）
                json_match = re.search(r'json\s*:?\s*\n?(.+?)(?:\n\n|\Z)', response, re.DOTALL | re.IGNORECASE)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    # デバッグ情報を含めてエラーを発生
                    logger.error(f"JSONレスポンスが見つかりません。レスポンス全体: {response}")
                    raise ValueError("JSONレスポンスが見つかりません")
        
        # JSON文字列の解析前にデバッグログ
        logger.debug(f"Extracted JSON string: {json_str}")
        
        # 切り詰められたJSONを修正する試み
        if json_str and not json_str.rstrip().endswith('}'):
            logger.warning("切り詰められたJSONを修正します")
            # 未完成の文字列を閉じる
            if '"' in json_str:
                # 最後のクォートの状態を確認
                quote_count = json_str.count('"') - json_str.count('\\"')
                if quote_count % 2 == 1:
                    json_str += '"'
            # 不足しているブレースを追加
            open_braces = json_str.count('{') - json_str.count('}')
            json_str += '}' * open_braces
        
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            # JSONが不完全な場合、デフォルト値を返す
            logger.error(f"JSON解析エラー: {e}")
            logger.error(f"JSON文字列: {json_str}")
            return {
                'selected_weather_index': 0,
                'selected_advice_index': 0,
                'weather_comment': '',
                'advice_comment': '',
                'selection_reason': 'JSON解析エラー'
            }
        
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
"""統合コメント生成ノード - 選択と生成を1回のLLM呼び出しで実行

このノードは、コメントペアの選択と最終コメントの生成を
単一のLLM呼び出しで実行することで、パフォーマンスを向上させます。
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import PastComment, CommentType
from src.llm.llm_manager import LLMManager
from src.validators import WeatherCommentValidator
from src.nodes.helpers.comment_safety import check_and_fix_weather_comment_safety
from src.nodes.helpers.ng_words import check_ng_words

logger = logging.getLogger(__name__)


def unified_comment_generation_node(state: CommentGenerationState) -> CommentGenerationState:
    """選択と生成を1回のLLM呼び出しで実行する統合ノード"""
    logger.info("UnifiedCommentGenerationNode: 統合コメント生成を開始")
    
    try:
        # 入力データの検証
        weather_data = state.weather_data
        past_comments = state.past_comments
        location_name = state.location_name
        target_datetime = state.target_datetime or datetime.now()
        llm_provider = state.llm_provider or "openai"
        
        if not weather_data:
            raise ValueError("天気データが利用できません")
        if not past_comments:
            raise ValueError("過去コメントが存在しません")
            
        # コメントをタイプ別に分離
        weather_comments = [c for c in past_comments if c.comment_type == CommentType.WEATHER_COMMENT]
        advice_comments = [c for c in past_comments if c.comment_type == CommentType.ADVICE]
        
        if not weather_comments or not advice_comments:
            raise ValueError("適切なコメントタイプが見つかりません")
            
        logger.info(f"天気コメント数: {len(weather_comments)}, アドバイスコメント数: {len(advice_comments)}")
        
        # LLMマネージャーの初期化
        llm_manager = LLMManager(provider=llm_provider)
        
        # 天気情報のフォーマット
        weather_info = _format_weather_info(weather_data, location_name, target_datetime)
        
        # 統合プロンプトの構築
        unified_prompt = _build_unified_prompt(
            weather_comments[:10],  # 上位10件に制限
            advice_comments[:10],   # 上位10件に制限
            weather_info,
            weather_data
        )
        
        # 1回のLLM呼び出しで選択と生成を実行
        response = llm_manager.generate_text(
            unified_prompt,
            temperature=0.7,
            max_tokens=500
        )
        
        # レスポンスの解析
        result = _parse_unified_response(response)
        
        # 選択されたコメントペアを取得
        weather_idx = result.get("weather_index", 0)
        advice_idx = result.get("advice_index", 0)
        
        selected_weather = weather_comments[weather_idx] if weather_idx < len(weather_comments) else weather_comments[0]
        selected_advice = advice_comments[advice_idx] if advice_idx < len(advice_comments) else advice_comments[0]
        
        # CommentPairの作成
        selected_pair = CommentPair(
            weather_comment=selected_weather,
            advice_comment=selected_advice
        )
        
        # 生成されたコメントを取得（フォールバック: 選択されたコメントの結合）
        generated_comment = result.get("generated_comment", "")
        if not generated_comment:
            # フォールバック: 選択されたコメントを結合
            weather_text = selected_weather.comment_text
            advice_text = selected_advice.comment_text
            
            # 安全性チェック
            weather_text, advice_text = check_and_fix_weather_comment_safety(
                weather_data, weather_text, advice_text, state
            )
            
            generated_comment = f"{weather_text}　{advice_text}"
        
        # NGワードチェック
        ng_check = check_ng_words(generated_comment)
        if not ng_check["is_valid"]:
            logger.warning(f"NGワードが検出されました: {ng_check['found_words']}")
            # NGワードが含まれる場合は、選択されたペアのコメントを結合して使用
            generated_comment = f"{selected_weather.comment_text}　{selected_advice.comment_text}"
        
        # 状態の更新
        state.selected_pair = selected_pair
        state.generated_comment = generated_comment
        state.final_comment = generated_comment
        
        # メタデータの更新
        generation_metadata = state.generation_metadata or {}
        generation_metadata.update({
            "unified_generation": True,
            "selected_weather_index": weather_idx,
            "selected_advice_index": advice_idx,
            "selected_weather_comment": selected_weather.comment_text,
            "selected_advice_comment": selected_advice.comment_text,
            "llm_provider": llm_provider,
            "generation_method": "unified",
            "weather_comments_count": len(weather_comments),
            "advice_comments_count": len(advice_comments)
        })
        state.generation_metadata = generation_metadata
        
        logger.info(f"統合生成完了 - 天気: {selected_weather.comment_text}, アドバイス: {selected_advice.comment_text}")
        logger.info(f"最終コメント: {generated_comment}")
        
        return state
        
    except Exception as e:
        logger.error(f"統合コメント生成エラー: {str(e)}", exc_info=True)
        state.errors = state.errors or []
        state.errors.append(f"UnifiedCommentGenerationNode: {str(e)}")
        state.is_candidate_suitable = False
        return state


def _format_weather_info(weather_data: Dict[str, Any], 
                        location_name: str, 
                        target_datetime: datetime) -> str:
    """天気情報を文字列にフォーマット"""
    weather_desc = weather_data.get('weather_description', '不明')
    temp = weather_data.get('temperature', 0)
    humidity = weather_data.get('humidity', 0)
    wind_speed = weather_data.get('wind_speed', 0)
    
    return (f"{location_name}の{target_datetime.strftime('%Y-%m-%d %H:%M')}の天気: "
            f"{weather_desc}、気温: {temp}°C、湿度: {humidity}%、風速: {wind_speed}m/s")


def _build_unified_prompt(weather_comments: List[PastComment],
                         advice_comments: List[PastComment],
                         weather_info: str,
                         weather_data: Dict[str, Any]) -> str:
    """統合プロンプトの構築"""
    
    # 候補のフォーマット
    weather_candidates = "\n".join([
        f"{i}. {c.comment_text} (天気条件: {c.weather_condition}, 使用回数: {c.usage_count})"
        for i, c in enumerate(weather_comments)
    ])
    
    advice_candidates = "\n".join([
        f"{i}. {c.comment_text} (使用回数: {c.usage_count})"
        for i, c in enumerate(advice_comments)
    ])
    
    prompt = f"""あなたは天気コメント生成の専門家です。
以下の天気情報と候補から、最適なコメントペアを選択し、自然な最終コメントを生成してください。

【天気情報】
{weather_info}

【天気コメント候補】
{weather_candidates}

【アドバイスコメント候補】
{advice_candidates}

【タスク】
1. 天気情報に最も適した天気コメントを1つ選択（インデックス番号）
2. 状況に最も適したアドバイスコメントを1つ選択（インデックス番号）
3. 選択したコメントを自然に組み合わせて最終コメントを生成

【選択基準】
- 天気条件との一致度
- 使用回数が少ないものを優先
- 組み合わせの自然さ

【制約】
- 最終コメントは15文字以内
- 「　」で天気とアドバイスを区切る

必ず以下のJSON形式で回答してください：
{{
    "weather_index": 選択した天気コメントのインデックス番号(0から始まる整数),
    "advice_index": 選択したアドバイスコメントのインデックス番号(0から始まる整数),
    "generated_comment": "最終的に生成されたコメント"
}}"""
    
    return prompt


def _parse_unified_response(response: str) -> Dict[str, Any]:
    """統合レスポンスの解析"""
    try:
        # JSON部分を抽出
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            result = json.loads(json_str)
            
            # 必須フィールドの確認
            if all(key in result for key in ["weather_index", "advice_index"]):
                return result
                
    except json.JSONDecodeError as e:
        logger.error(f"JSONパースエラー: {e}")
    except Exception as e:
        logger.error(f"レスポンス解析エラー: {e}")
    
    # フォールバック
    logger.warning("統合レスポンスの解析に失敗。デフォルト値を使用")
    return {
        "weather_index": 0,
        "advice_index": 0,
        "generated_comment": ""
    }
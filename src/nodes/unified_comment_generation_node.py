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
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.nodes.helpers.comment_safety import check_and_fix_weather_comment_safety
from src.nodes.helpers.ng_words import check_ng_words
from src.constants.content_constants import FORBIDDEN_PHRASES

logger = logging.getLogger(__name__)

# 連続雨判定の閾値（時間）
CONTINUOUS_RAIN_THRESHOLD_HOURS = 4


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
        
        logger.debug(f"入力データ確認 - weather_data: {weather_data is not None}, past_comments: {past_comments is not None}")
        if past_comments:
            logger.debug(f"past_comments count: {len(past_comments)}")
        
        if not weather_data:
            raise ValueError("天気データが利用できません")
        if not past_comments:
            logger.error("過去コメントが空です。CSVファイルの読み込みに問題がある可能性があります。")
            raise ValueError("過去コメントが存在しません")
            
        # コメントをタイプ別に分離
        weather_comments = [c for c in past_comments if c.comment_type == CommentType.WEATHER_COMMENT]
        advice_comments = [c for c in past_comments if c.comment_type == CommentType.ADVICE]
        
        # 禁止フレーズを含むコメントをフィルタリング
        weather_comments = _filter_forbidden_phrases(weather_comments)
        advice_comments = _filter_forbidden_phrases(advice_comments)
        
        if not weather_comments or not advice_comments:
            raise ValueError("適切なコメントタイプが見つかりません")
            
        logger.info(f"天気コメント数: {len(weather_comments)}, アドバイスコメント数: {len(advice_comments)}")
        
        # LLMマネージャーの初期化
        from src.config.config import get_config
        config = get_config()
        llm_manager = LLMManager(provider=llm_provider, config=config)
        
        # 温度に応じたコメントのフィルタリング
        temperature = getattr(weather_data, 'temperature', 0)
        if temperature < 35.0:
            # 35度未満では熱中症関連のコメントを除外
            logger.info(f"温度が{temperature}°C（35°C未満）のため、熱中症関連コメントを除外")
            weather_comments = [c for c in weather_comments if "熱中症" not in c.comment_text]
            advice_comments = [c for c in advice_comments if "熱中症" not in c.comment_text]
        
        # 天気に応じたコメントのフィルタリング
        if hasattr(weather_data, 'weather_description') and '雨' in weather_data.weather_description:
            precipitation = getattr(weather_data, 'precipitation', 0)
            logger.info(f"雨の天気（降水量: {precipitation}mm）のため、適切なコメントを選択")
            
            # 降水量に応じて適切なコメントを選択
            original_weather_comments = weather_comments.copy()  # フィルタリング前のリストを保存
            
            if precipitation >= 10.0:  # 10mm以上は大雨
                logger.info("大雨のため、大雨・豪雨関連のコメントを優先")
                weather_comments = [c for c in original_weather_comments if c.weather_condition in ['大雨', '嵐', '雷']]
                if not weather_comments:  # 大雨コメントがない場合は通常の雨コメントも含める
                    weather_comments = [c for c in original_weather_comments if c.weather_condition in ['雨', '大雨', '嵐', '雷']]
            elif precipitation >= 1.0:  # 1mm以上は通常の雨
                logger.info("通常の雨のため、雨関連のコメントを選択")
                weather_comments = [c for c in original_weather_comments if c.weather_condition in ['雨', '大雨', '雷']]
            else:  # 1mm未満は小雨
                logger.info("小雨のため、軽い雨のコメントも含めて選択")
                weather_comments = [c for c in original_weather_comments if c.weather_condition in ['雨', '曇り']]  # 曇りも含める（小雨の可能性）
            
            if not weather_comments:
                logger.warning("適切な雨関連のコメントが見つかりません。全コメントを使用します。")
                weather_comments = [c for c in past_comments if c.comment_type == CommentType.WEATHER_COMMENT]
                weather_comments = _filter_forbidden_phrases(weather_comments)
        
        # 連続雨判定
        is_continuous_rain = _check_continuous_rain(state)
        
        # 連続雨の場合、「にわか雨」を含むコメントをフィルタリング
        if is_continuous_rain:
            logger.info("連続雨を検出 - にわか雨表現を含むコメントをフィルタリング")
            
            # フィルタリング前のログ
            logger.info(f"フィルタリング前 - 天気コメント数: {len(weather_comments)}")
            logger.info(f"フィルタリング前 - アドバイスコメント数: {len(advice_comments)}")
            
            # アドバイスコメントの内容を確認
            logger.debug("フィルタリング前のアドバイスコメント:")
            for i, comment in enumerate(advice_comments[:10]):
                logger.debug(f"  {i}: {comment.comment_text}")
            
            weather_comments = _filter_shower_comments(weather_comments)
            advice_comments = _filter_mild_umbrella_comments(advice_comments)
            
            # フィルタリング後のログ
            logger.info(f"フィルタリング後 - 天気コメント数: {len(weather_comments)}")
            logger.info(f"フィルタリング後 - アドバイスコメント数: {len(advice_comments)}")
            
            # フィルタリング後のアドバイスコメントの内容を確認
            logger.debug("フィルタリング後のアドバイスコメント:")
            for i, comment in enumerate(advice_comments[:10]):
                logger.debug(f"  {i}: {comment.comment_text}")
        
        # 天気情報のフォーマット
        weather_info = _format_weather_info(weather_data, location_name, target_datetime)
        
        # 統合プロンプトの構築
        unified_prompt = _build_unified_prompt(
            weather_comments[:10],  # 上位10件に制限
            advice_comments[:10],   # 上位10件に制限
            weather_info,
            weather_data,
            is_continuous_rain
        )
        
        # 1回のLLM呼び出しで選択と生成を実行
        response = llm_manager.generate(unified_prompt)
        
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
            advice_comment=selected_advice,
            similarity_score=1.0,  # 統一モードでは常に最適として扱う
            selection_reason="統一モードによる自動選択"
        )
        
        # 生成されたコメントを取得
        generated_comment = result.get("generated_comment", "")
        
        # 常に選択されたコメントの結合を使用（LLMが創作しないように）
        weather_text = selected_weather.comment_text
        advice_text = selected_advice.comment_text
        
        # 安全性チェック
        weather_text, advice_text = check_and_fix_weather_comment_safety(
            weather_data, weather_text, advice_text, state
        )
        
        # 最終的なコメントは必ず選択されたコメントの結合
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
            "advice_comments_count": len(advice_comments),
            "is_continuous_rain": is_continuous_rain
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


def _format_weather_info(weather_data: Any, 
                        location_name: str, 
                        target_datetime: datetime) -> str:
    """天気情報を文字列にフォーマット"""
    # WeatherForecastオブジェクトとdictの両方に対応
    if hasattr(weather_data, 'weather_description'):
        # WeatherForecastオブジェクトの場合
        weather_desc = weather_data.weather_description or '不明'
        temp = weather_data.temperature or 0
        humidity = weather_data.humidity or 0
        wind_speed = weather_data.wind_speed or 0
        precipitation = weather_data.precipitation if hasattr(weather_data, 'precipitation') else 0
    else:
        # dictの場合
        weather_desc = weather_data.get('weather_description', '不明')
        temp = weather_data.get('temperature', 0)
        humidity = weather_data.get('humidity', 0)
        wind_speed = weather_data.get('wind_speed', 0)
        precipitation = weather_data.get('precipitation', 0)
    
    result = (f"{location_name}の{target_datetime.strftime('%Y-%m-%d %H:%M')}の天気: "
              f"{weather_desc}、気温: {temp}°C、湿度: {humidity}%、風速: {wind_speed}m/s")
    
    # 降水量情報を追加（雨の場合のみ）
    if precipitation > 0:
        result += f"、降水量: {precipitation}mm"
    
    return result


def _build_unified_prompt(weather_comments: List[PastComment],
                         advice_comments: List[PastComment],
                         weather_info: str,
                         weather_data: Any,
                         is_continuous_rain: bool = False) -> str:
    """統合プロンプトの構築"""
    
    # 候補のフォーマット
    weather_candidates = "\n".join([
        f"{i}. {c.comment_text} (天気条件: {c.weather_condition or '不明'}, 使用回数: {getattr(c, 'usage_count', c.raw_data.get('count', 0))})"
        for i, c in enumerate(weather_comments)
    ])
    
    advice_candidates = "\n".join([
        f"{i}. {c.comment_text} (使用回数: {getattr(c, 'usage_count', c.raw_data.get('count', 0))})"
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
3. 選択した2つのコメントを「　」で結合して最終コメントを生成

【重要】
- 必ず上記の候補リストから選択してください
- 新しいコメントを創作しないでください
- generated_commentは選択したコメントを「　」で結合したものにしてください
- 天気が「雨」の場合は、必ず雨に関するコメントを選択してください
- 天気と関係ないコメントは絶対に選択しないでください
- 天気コメントとアドバイスコメントで意味が重複するものは絶対に選ばないでください
  （例：両方に「傘」が含まれる、両方に「暑さ」が含まれる等）

【選択基準】
1. 天気条件との一致度（最優先）- 実際の天気と異なる内容のコメントは選択禁止
2. 降水量に応じた選択:
   - 降水量10mm以上: 「傘が必須」「傘は必須」など強い表現を優先
   - 降水量1-10mm: 「傘が活躍」「傘の用意」など通常の雨表現
   - 降水量0.1-1mm: 「にわか雨」「軽い雨」など（連続雨でない場合のみ）
3. 使用回数が少ないものを優先
4. 組み合わせの自然さ
5. 重複・冗長性の回避:
   - 天気コメントとアドバイスコメントで同じ意味の内容を避ける
   - 例: 「傘が必須」（天気）と「傘があると安心」（アドバイス）は重複なので不可
   - 例: 「強い雨」（天気）と「雨脚が強い」（アドバイス）は重複なので不可

【制約】
- 最終コメントは15文字以内
- 「　」で天気とアドバイスを区切る

必ず以下のJSON形式で回答してください：
{{
    "weather_index": 選択した天気コメントのインデックス番号(0から始まる整数),
    "advice_index": 選択したアドバイスコメントのインデックス番号(0から始まる整数),
    "generated_comment": "選択したコメントを「　」で結合したもの（新規作成禁止）"
}}

例：weather_index=1, advice_index=2の場合
generated_comment: "天気コメント候補の1番　アドバイスコメント候補の2番" """
    
    # 連続雨の場合の追加指示
    if is_continuous_rain:
        prompt += """

【重要な追加指示】
現在、4時間以上の連続した雨が予測されています。以下の点に特に注意してください：
- 「にわか雨」「一時的な雨」「急な雨」などの表現は避けてください
- 「傘があると安心」のような控えめな表現ではなく、「傘は必須」のような明確な表現を使用してください
- 雨が長時間続くことを前提としたコメントを生成してください"""
    
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


def _check_continuous_rain(state: CommentGenerationState) -> bool:
    """連続雨かどうかを判定"""
    if not state or not hasattr(state, 'generation_metadata') or not state.generation_metadata:
        return False
        
    period_forecasts = state.generation_metadata.get('period_forecasts', [])
    if not period_forecasts:
        return False
    
    # 天気が「雨」または降水量が0.1mm以上の時間をカウント
    rain_hours = 0
    for f in period_forecasts:
        if hasattr(f, 'weather') and '雨' in f.weather:
            rain_hours += 1
        elif hasattr(f, 'precipitation') and f.precipitation >= 0.1:
            rain_hours += 1
    
    is_continuous_rain = rain_hours >= CONTINUOUS_RAIN_THRESHOLD_HOURS
    
    if is_continuous_rain:
        logger.info(f"連続雨を検出: {rain_hours}時間の雨")
        # デバッグ情報
        for f in period_forecasts:
            if hasattr(f, 'datetime') and hasattr(f, 'weather'):
                time_str = f.datetime.strftime('%H時')
                weather = f.weather
                precip = f.precipitation if hasattr(f, 'precipitation') else 0
                logger.debug(f"  {time_str}: {weather}, 降水量{precip}mm")
    
    return is_continuous_rain


def _filter_shower_comments(comments: List[PastComment]) -> List[PastComment]:
    """にわか雨表現を含むコメントをフィルタリング"""
    # 連続雨時に不適切な「一時的」「急な」「にわか」表現のみをフィルタリング
    temporary_rain_expressions = ["にわか雨", "ニワカ雨", "一時的な雨", "急な雨", "突然の雨"]
    
    filtered = []
    for comment in comments:
        if not any(expr in comment.comment_text for expr in temporary_rain_expressions):
            filtered.append(comment)
        else:
            logger.debug(f"連続雨のためフィルタリング: {comment.comment_text}")
    
    # フィルタリング後にコメントがなくなった場合は元のリストを返す
    if not filtered:
        logger.warning("すべてのコメントがフィルタリングされました。元のリストを使用します。")
        return comments
    
    return filtered


def _filter_mild_umbrella_comments(comments: List[PastComment]) -> List[PastComment]:
    """控えめな傘表現とにわか雨表現を含むコメントをフィルタリング"""
    # にわか雨が心配も含める
    mild_umbrella_expressions = ["傘があると安心", "傘がお守り", "念のため傘", "折りたたみ傘", "傘をお忘れなく", "にわか雨が心配", "にわか雨", "急な雨"]
    
    filtered = []
    for comment in comments:
        if not any(expr in comment.comment_text for expr in mild_umbrella_expressions):
            filtered.append(comment)
        else:
            logger.debug(f"連続雨のためフィルタリング: {comment.comment_text}")
    
    # フィルタリング後にコメントがなくなった場合は元のリストを返す
    if not filtered:
        logger.warning("すべてのアドバイスがフィルタリングされました。元のリストを使用します。")
        return comments
    
    return filtered


def _filter_forbidden_phrases(comments: List[PastComment]) -> List[PastComment]:
    """禁止フレーズを含むコメントをフィルタリング"""
    filtered = []
    for comment in comments:
        if not any(phrase in comment.comment_text for phrase in FORBIDDEN_PHRASES):
            filtered.append(comment)
        else:
            logger.debug(f"禁止フレーズのためフィルタリング: {comment.comment_text}")
    
    # フィルタリング後にコメントがなくなった場合は元のリストを返す
    if not filtered:
        logger.warning("すべてのコメントが禁止フレーズでフィルタリングされました。元のリストを使用します。")
        return comments
    
    return filtered
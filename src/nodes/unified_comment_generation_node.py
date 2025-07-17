"""統合コメント生成ノード - 選択と生成を1回のLLM呼び出しで実行

このノードは、コメントペアの選択と最終コメントの生成を
単一のLLM呼び出しで実行することで、パフォーマンスを向上させます。
"""

from __future__ import annotations
import json
import logging
from typing import Any
from datetime import datetime

from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import PastComment, CommentType
from src.llm.llm_manager import LLMManager
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.nodes.helpers.comment_safety import check_and_fix_weather_comment_safety
from src.nodes.helpers.ng_words import check_ng_words
from src.constants.weather_constants import TEMP, PRECIP, COMMENT
from src.nodes.unified_comment_generation import (
    format_weather_info,
    build_unified_prompt,
    parse_unified_response,
    check_continuous_rain,
    filter_shower_comments,
    filter_mild_umbrella_comments,
    filter_forbidden_phrases,
    filter_seasonal_inappropriate_comments
)
from src.utils.comment_deduplicator import CommentDeduplicator

logger = logging.getLogger(__name__)


def unified_comment_generation_node(state: CommentGenerationState) -> CommentGenerationState:
    """選択と生成を1回のLLM呼び出しで実行する統合ノード"""
    logger.info("UnifiedCommentGenerationNode: 統合コメント生成を開始")
    
    try:
        # 入力データの検証
        weather_data = state.weather_data
        past_comments = state.past_comments
        location_name = state.location_name
        # target_datetimeの安全な取得
        target_datetime = state.target_datetime
        if not isinstance(target_datetime, datetime):
            logger.warning(f"target_datetimeが不正な型です: {type(target_datetime)}, 現在時刻を使用します")
            target_datetime = datetime.now()
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
        weather_comments = filter_forbidden_phrases(weather_comments)
        advice_comments = filter_forbidden_phrases(advice_comments)
        
        # 季節性に矛盾するコメントをフィルタリング
        month = target_datetime.month
        weather_comments = filter_seasonal_inappropriate_comments(weather_comments, month)
        advice_comments = filter_seasonal_inappropriate_comments(advice_comments, month)
        
        if not weather_comments or not advice_comments:
            raise ValueError("適切なコメントタイプが見つかりません")
            
        logger.info(f"天気コメント数: {len(weather_comments)}, アドバイスコメント数: {len(advice_comments)}")
        
        # 天気と矛盾するコメントを候補から除外
        filtered_weather_comments = []
        for comment in weather_comments:
            comment_text = comment.comment_text
            
            # 季節に不適切なコメントを除外
            month = target_datetime.month
            
            # 残暑は9月以降のみ
            if month not in [9, 10, 11] and "残暑" in comment_text:
                logger.debug(f"{month}月に「残暑」は不適切: '{comment_text}'")
                continue
            
            # 春（3-5月）に不適切な表現
            if month in [3, 4, 5]:
                spring_inappropriate = ["梅雨", "真夏", "猛暑", "残暑", "師走", "年末", "初雪", "真冬"]
                if any(word in comment_text for word in spring_inappropriate):
                    logger.debug(f"春（{month}月）に不適切な表現を除外: '{comment_text}'")
                    continue
            
            # 夏（6-8月）に不適切な表現
            elif month in [6, 7, 8]:
                summer_inappropriate = ["初雪", "雪", "真冬", "厳寒", "凍結", "霜", "初霜", "残暑", "紅葉", "落ち葉"]
                if any(word in comment_text for word in summer_inappropriate):
                    logger.debug(f"夏（{month}月）に不適切な表現を除外: '{comment_text}'")
                    continue
            
            # 秋（9-11月）に不適切な表現
            elif month in [9, 10, 11]:
                autumn_inappropriate = ["真夏", "猛暑", "梅雨", "初雪", "真冬", "厳寒"]
                # 9月は残暑OK、10-11月は微妙だが許容
                if any(word in comment_text for word in autumn_inappropriate):
                    logger.debug(f"秋（{month}月）に不適切な表現を除外: '{comment_text}'")
                    continue
            
            # 冬（12-2月）に不適切な表現
            elif month in [12, 1, 2]:
                winter_inappropriate = ["残暑", "猛暑", "真夏", "梅雨", "桜", "新緑", "紅葉"]
                if any(word in comment_text for word in winter_inappropriate):
                    logger.debug(f"冬（{month}月）に不適切な表現を除外: '{comment_text}'")
                    continue
            
            # 晴天時に雨のコメントを除外
            if "晴" in weather_data.weather_description and weather_data.precipitation < 0.5:
                rain_keywords = ["雨", "雷雨", "降水", "傘", "濡れ", "豪雨", "にわか雨", "大雨", "激しい雨"]
                if any(keyword in comment_text for keyword in rain_keywords):
                    logger.debug(f"晴天時に雨のコメントを除外: '{comment_text}'")
                    continue
            
            # 晴天時に曇りのコメントを除外
            if "晴" in weather_data.weather_description:
                cloudy_keywords = ["雲が優勢", "雲が多", "どんより", "雲が厚", "曇り空", "グレーの空", "雲に覆われ"]
                if any(keyword in comment_text for keyword in cloudy_keywords):
                    logger.debug(f"晴天時に曇りのコメントを除外: '{comment_text}'")
                    continue
            
            # 雨天時に晴天のコメントを除外
            if "雨" in weather_data.weather_description:
                sunny_keywords = ["快晴", "青空", "強い日差し", "眩しい", "太陽がギラギラ"]
                if any(keyword in comment_text for keyword in sunny_keywords):
                    logger.debug(f"雨天時に晴天のコメントを除外: '{comment_text}'")
                    continue
            
            # 曇天時（うすぐもり含む）に強い日差しのコメントを除外
            if any(cloud in weather_data.weather_description for cloud in ["曇", "くもり", "うすぐもり"]):
                sunshine_keywords = ["強い日差し", "眩しい", "太陽がギラギラ", "日光が強", "日差しジリジリ", "照りつける", "燦々"]
                if any(keyword in comment_text for keyword in sunshine_keywords):
                    logger.debug(f"曇天時に日差しのコメントを除外: '{comment_text}'")
                    continue
            
            filtered_weather_comments.append(comment)
        
        # フィルタリング後のコメントを使用
        if filtered_weather_comments:
            weather_comments = filtered_weather_comments
            logger.info(f"フィルタリング後の天気コメント数: {len(weather_comments)}")
        else:
            logger.warning("フィルタリング後の天気コメントが0件になったため、元のリストを使用")
        
        # LLMマネージャーの初期化
        from src.config.config import get_config
        config = get_config()
        llm_manager = LLMManager(provider=llm_provider, config=config)
        
        # 温度に応じたコメントのフィルタリング
        temperature = getattr(weather_data, 'temperature', 0)
        if temperature is None:
            temperature = 0
        if temperature < TEMP.HEATSTROKE:
            # 熱中症閾値未満では熱中症関連のコメントを除外
            logger.info(f"温度が{temperature}°C（{TEMP.HEATSTROKE}°C未満）のため、熱中症関連コメントを除外")
            weather_comments = [c for c in weather_comments if "熱中症" not in c.comment_text]
            advice_comments = [c for c in advice_comments if "熱中症" not in c.comment_text]
        
        # 天気に応じたコメントのフィルタリング
        if hasattr(weather_data, 'weather_description') and '雨' in weather_data.weather_description:
            precipitation = getattr(weather_data, 'precipitation', 0)
            if precipitation is None:
                precipitation = 0
            logger.info(f"雨の天気（降水量: {precipitation}mm）のため、適切なコメントを選択")
            
            # 降水量に応じて適切なコメントを選択
            original_weather_comments = weather_comments.copy()  # フィルタリング前のリストを保存
            
            if precipitation >= PRECIP.HEAVY:  # 大雨閾値以上
                logger.info("大雨のため、大雨・豪雨関連のコメントを優先")
                weather_comments = [c for c in original_weather_comments if c.weather_condition in ['大雨', '嵐', '雷']]
                if not weather_comments:  # 大雨コメントがない場合は通常の雨コメントも含める
                    weather_comments = [c for c in original_weather_comments if c.weather_condition in ['雨', '大雨', '嵐', '雷']]
            elif precipitation >= PRECIP.LIGHT_RAIN:  # 軽い雨閾値以上
                logger.info("通常の雨のため、雨関連のコメントを選択")
                weather_comments = [c for c in original_weather_comments if c.weather_condition in ['雨', '大雨', '雷']]
            else:  # 1mm未満は小雨
                logger.info("小雨のため、軽い雨のコメントも含めて選択")
                weather_comments = [c for c in original_weather_comments if c.weather_condition in ['雨', '曇り']]  # 曇りも含める（小雨の可能性）
            
            if not weather_comments:
                logger.warning("適切な雨関連のコメントが見つかりません。全コメントを使用します。")
                weather_comments = [c for c in past_comments if c.comment_type == CommentType.WEATHER_COMMENT]
                weather_comments = filter_forbidden_phrases(weather_comments)
        
        # 連続雨判定
        is_continuous_rain = check_continuous_rain(state)
        
        # 連続雨の場合、「にわか雨」を含むコメントをフィルタリング
        if is_continuous_rain:
            logger.info("連続雨を検出 - にわか雨表現を含むコメントをフィルタリング")
            
            # フィルタリング前のログ
            logger.info(f"フィルタリング前 - 天気コメント数: {len(weather_comments)}")
            logger.info(f"フィルタリング前 - アドバイスコメント数: {len(advice_comments)}")
            
            # アドバイスコメントの内容を確認
            logger.debug("フィルタリング前のアドバイスコメント:")
            for i, comment in enumerate(advice_comments[:COMMENT.CANDIDATE_LIMIT]):
                logger.debug(f"  {i}: {comment.comment_text}")
            
            weather_comments = filter_shower_comments(weather_comments)
            advice_comments = filter_mild_umbrella_comments(advice_comments)
            
            # フィルタリング後のログ
            logger.info(f"フィルタリング後 - 天気コメント数: {len(weather_comments)}")
            logger.info(f"フィルタリング後 - アドバイスコメント数: {len(advice_comments)}")
            
            # フィルタリング後のアドバイスコメントの内容を確認
            logger.debug("フィルタリング後のアドバイスコメント:")
            for i, comment in enumerate(advice_comments[:COMMENT.CANDIDATE_LIMIT]):
                logger.debug(f"  {i}: {comment.comment_text}")
        
        # 天気情報のフォーマット
        weather_info = format_weather_info(
            weather_data, 
            state.generation_metadata.get('temperature_differences') if state.generation_metadata else None,
            state.generation_metadata.get('weather_trend') if state.generation_metadata else None
        )
        
        # 統合プロンプトの構築
        # パフォーマンス最適化のため候補数を5に制限
        OPTIMIZED_CANDIDATE_LIMIT = 5
        unified_prompt = build_unified_prompt(
            weather_comments[:OPTIMIZED_CANDIDATE_LIMIT],  # 上位5件に制限（パフォーマンス最適化）
            advice_comments[:OPTIMIZED_CANDIDATE_LIMIT],   # 上位5件に制限（パフォーマンス最適化）
            weather_info,
            location_name,
            target_datetime
        )
        
        # 1回のLLM呼び出しで選択と生成を実行
        response = llm_manager.generate(unified_prompt)
        
        # レスポンスの解析
        result = parse_unified_response(response)
        
        # 選択されたコメントペアを取得
        weather_idx = result.get("selected_weather_index", 0)
        advice_idx = result.get("selected_advice_index", 0)
        
        # LLMがnullを返した場合の処理
        if weather_idx is None:
            logger.warning("LLMがweather_indexにnullを返しました。デフォルト値0を使用します。")
            weather_idx = 0
        if advice_idx is None:
            logger.warning("LLMがadvice_indexにnullを返しました。デフォルト値0を使用します。")
            advice_idx = 0
        
        selected_weather = weather_comments[weather_idx] if weather_idx < len(weather_comments) else weather_comments[0]
        selected_advice = advice_comments[advice_idx] if advice_idx < len(advice_comments) else advice_comments[0]
        
        # CommentPairの作成
        selected_pair = CommentPair(
            weather_comment=selected_weather,
            advice_comment=selected_advice,
            similarity_score=1.0,  # 統一モードでは常に最適として扱う
            selection_reason="統一モードによる自動選択"
        )
        
        # 生成されたコメントを取得（使用しないが、LLMの応答を確認）
        weather_comment = result.get("weather_comment", "")
        advice_comment = result.get("advice_comment", "")
        generated_comment = f"{weather_comment}　{advice_comment}" if weather_comment and advice_comment else ""
        
        # 常に選択されたコメントの結合を使用（LLMが創作しないように）
        weather_text = selected_weather.comment_text
        advice_text = selected_advice.comment_text
        
        # 安全性チェック
        weather_text, advice_text = check_and_fix_weather_comment_safety(
            weather_data, weather_text, advice_text, state
        )
        
        # 重複除去
        weather_text, advice_text = CommentDeduplicator.deduplicate_comment(weather_text, advice_text)
        
        # 最終的なコメントは必ず選択されたコメントの結合
        generated_comment = f"{weather_text}　{advice_text}"
        
        # NGワードチェック
        ng_check = check_ng_words(generated_comment)
        if not ng_check["is_valid"]:
            logger.warning(f"NGワードが検出されました: {ng_check['found_words']}")
            # NGワードは既に適切に処理されているはずなので、そのまま使用
            # （重複除去済みのコメントを維持）
        
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

"""コメントペア選択ノード - LLMを使用して適切なコメントペアを選択"""

import json
import logging
import re
from datetime import datetime

from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import CommentType, PastCommentCollection
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager

logger = logging.getLogger(__name__)


def select_comment_pair_node(state: CommentGenerationState) -> CommentGenerationState:
    """LLMを使用して適切なコメントペアを選択"""
    logger.info("SelectCommentPairNode: LLMによるコメントペア選択を開始")

    try:
        # 必要なデータの取得
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
        collection = PastCommentCollection(past_comments)
        weather_comments = collection.filter_by_type(CommentType.WEATHER_COMMENT).comments
        advice_comments = collection.filter_by_type(CommentType.ADVICE).comments

        if not weather_comments or not advice_comments:
            raise ValueError("適切なコメントタイプが見つかりません")

        logger.info(f"天気コメント数: {len(weather_comments)}, アドバイスコメント数: {len(advice_comments)}")

        # LLMマネージャーの初期化
        llm_manager = LLMManager(provider=llm_provider)

        # 最適なコメントを選択
        best_weather = _select_best_comment(
            weather_comments, weather_data, location_name, target_datetime, 
            llm_manager, CommentType.WEATHER_COMMENT
        )
        best_advice = _select_best_comment(
            advice_comments, weather_data, location_name, target_datetime,
            llm_manager, CommentType.ADVICE
        )

        # ペアを作成
        if best_weather and best_advice:
            pair = CommentPair(
                weather_comment=best_weather,
                advice_comment=best_advice,
                similarity_score=1.0,
                selection_reason="LLMによる最適選択",
            )
            state.selected_pair = pair
            
            logger.info(f"選択完了 - 天気: {best_weather.comment_text}, アドバイス: {best_advice.comment_text}")
            
            state.update_metadata("selection_metadata", {
                "weather_comments_count": len(weather_comments),
                "advice_comments_count": len(advice_comments),
                "selection_method": "LLM",
                "llm_provider": llm_provider,
                "selected_weather_comment": best_weather.comment_text,
                "selected_advice_comment": best_advice.comment_text,
            })
        else:
            raise ValueError("LLMによるコメントペアの選択に失敗しました")

    except Exception as e:
        logger.error(f"コメントペア選択中にエラー: {e!s}")
        state.add_error(f"SelectCommentPairNode: {e!s}", "select_comment_pair_node")
        raise

    return state


def _select_best_comment(comments, weather_data, location_name, target_datetime, 
                        llm_manager, comment_type):
    """LLMを使用して最適なコメントを選択"""
    if not comments:
        return None

    # 候補の準備（天気コメントは天気一致を優先）
    candidates = []
    if comment_type == CommentType.WEATHER_COMMENT:
        weather_matched = []
        others = []
        
        for i, comment in enumerate(comments):
            candidate = _create_candidate_dict(i, comment)
            
            if _is_weather_matched(comment.weather_condition, weather_data.weather_description):
                weather_matched.append(candidate)
            else:
                others.append(candidate)
        
        candidates = weather_matched[:20] + others[:10]
        logger.info(f"天気コメント候補: 全{len(comments)}件中、天気一致{len(weather_matched)}件を優先")
    else:
        # アドバイスコメントは気温による事前フィルタリング
        candidates = []
        for i, comment in enumerate(comments[:30]):
            candidate = _create_candidate_dict(i, comment)
            # 気温による除外
            if weather_data.temperature < 25 and "熱中症" in comment.comment_text:
                logger.info(f"気温{weather_data.temperature}°Cのため熱中症コメントを除外: {comment.comment_text}")
                continue
            if weather_data.temperature >= 15 and any(word in comment.comment_text for word in ["防寒", "暖かく", "寒さ"]):
                logger.info(f"気温{weather_data.temperature}°Cのため防寒コメントを除外: {comment.comment_text}")
                continue
            candidates.append(candidate)

    # プロンプト生成
    prompt = _generate_prompt(candidates, weather_data, location_name, target_datetime, comment_type)

    try:
        response = llm_manager.generate(prompt)
        match = re.search(r"\d+", response)
        selected_index = int(match.group()) if match else 0

        if 0 <= selected_index < len(comments):
            logger.info(f"LLMが{comment_type.value}を選択: index={selected_index}")
            return comments[selected_index]
            
        logger.warning(f"無効なインデックス: {selected_index}")
        return comments[0]

    except Exception as e:
        raise ValueError(f"{comment_type.value}選択失敗: {e!s}")


def _create_candidate_dict(index, comment):
    """候補辞書を作成"""
    return {
        "index": index,
        "text": comment.comment_text,
        "season": comment.raw_data.get("season", "不明"),
    }


def _is_weather_matched(comment_weather, current_weather):
    """天気条件が一致するか判定"""
    if not comment_weather or not current_weather:
        return False
    return current_weather in comment_weather or comment_weather in current_weather


def _generate_prompt(candidates, weather_data, location_name, target_datetime, comment_type):
    """選択用プロンプトを生成"""
    base = f"""現在の天気条件に最も適した{comment_type.value}を選んでください。

現在の条件:
- 地点: {location_name}
- 天気: {weather_data.weather_description}
- 気温: {weather_data.temperature}°C
- 湿度: {weather_data.humidity}%
- 風速: {weather_data.wind_speed}m/s
- 降水量: {weather_data.precipitation}mm
- 日時: {target_datetime.strftime("%Y年%m月%d日 %H時")}

候補:
{json.dumps(candidates, ensure_ascii=False, indent=2)}

"""

    if comment_type == CommentType.WEATHER_COMMENT:
        base += f"""選択基準:
1. 天気条件の一致（雨なら「スッキリしない空」等）
2. 気温表現の適合性（{weather_data.temperature}°Cに適した表現）
3. 絶対禁止：雨天+「晴れ」系、22°C+「猛暑」系

現在は{weather_data.weather_description}・{weather_data.temperature}°Cです。適切な表現を選んでください。"""
    else:
        base += f"""選択基準:
1. 気温による除外（{weather_data.temperature}°C）：
   - 25°C未満で「熱中症」系は選択禁止
   - 15°C以上で「防寒」系は選択禁止
2. 天気条件への適切性（雨なら濡れ対策等）
3. 実用的で具体的なアドバイス

**重要**: 現在{weather_data.temperature}°Cなので、熱中症関連は{'選択禁止' if weather_data.temperature < 25 else '選択可能'}です。"""

    return base + f"\n\n必ず候補から1つ選び、index (0〜{len(candidates)-1}) を半角数字のみで答えてください。"
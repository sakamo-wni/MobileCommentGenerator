"""コメントペア選択ノード - LLMを使用して適切なコメントペアを選択"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import CommentType, PastCommentCollection, PastComment
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager
from src.config.comment_config import get_comment_config
from src.config.severe_weather_config import get_severe_weather_config
from src.data.forecast_cache import ForecastCache
from datetime import timedelta

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

        # 最適なコメントを選択（stateを渡す）
        best_weather = _select_best_comment(
            weather_comments, weather_data, location_name, target_datetime, 
            llm_manager, CommentType.WEATHER_COMMENT, state
        )
        best_advice = _select_best_comment(
            advice_comments, weather_data, location_name, target_datetime,
            llm_manager, CommentType.ADVICE, state
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


def _select_best_comment(comments: List[PastComment], weather_data: WeatherForecast, location_name: str, target_datetime: datetime, 
                        llm_manager: LLMManager, comment_type: CommentType, state: Optional[CommentGenerationState] = None) -> Optional[PastComment]:
    """LLMを使用して最適なコメントを選択"""
    if not comments:
        return None

    # 悪天候設定を取得
    severe_config = get_severe_weather_config()
    
    # 候補の準備（事前フィルタリング適用）
    candidates = []
    if comment_type == CommentType.WEATHER_COMMENT:
        severe_weather_matched = []  # 悪天候に特化したコメント
        weather_matched = []
        others = []
        
        for i, comment in enumerate(comments):
            # 天気コメントの事前フィルタリング
            if _should_exclude_weather_comment(comment.comment_text, weather_data):
                logger.info(f"天気条件不適合のためコメントを除外: {comment.comment_text} (天気: {weather_data.weather_description})")
                continue
                
            candidate = _create_candidate_dict(len(severe_weather_matched) + len(weather_matched) + len(others), comment, original_index=i)
            
            # 悪天候時の特別な優先順位付け
            if severe_config.is_severe_weather(weather_data.weather_condition):
                # 悪天候に適したコメントかチェック
                if _is_severe_weather_appropriate(comment.comment_text, weather_data):
                    severe_weather_matched.append(candidate)
                elif _is_weather_matched(comment.weather_condition, weather_data.weather_description):
                    weather_matched.append(candidate)
                else:
                    others.append(candidate)
            else:
                # 通常の天気マッチング
                if _is_weather_matched(comment.weather_condition, weather_data.weather_description):
                    weather_matched.append(candidate)
                else:
                    others.append(candidate)
        
        # 悪天候時は悪天候用コメントを最優先、次に天気一致、最後にその他
        candidates = severe_weather_matched[:15] + weather_matched[:10] + others[:5]
        logger.info(f"天気コメント候補: 全{len(comments)}件中、悪天候専用{len(severe_weather_matched)}件、天気一致{len(weather_matched)}件を優先")
    else:
        # アドバイスコメントの事前フィルタリング
        severe_advice_matched = []  # 悪天候に適したアドバイス
        normal_advice = []
        
        for i, comment in enumerate(comments[:30]):
            # アドバイスコメントの事前フィルタリング
            if _should_exclude_advice_comment(comment.comment_text, weather_data):
                logger.info(f"天気・気温条件不適合のためコメントを除外: {comment.comment_text}")
                continue
            
            candidate = _create_candidate_dict(len(severe_advice_matched) + len(normal_advice), comment, original_index=i)
            
            # 悪天候時の特別な優先順位付け
            if severe_config.is_severe_weather(weather_data.weather_condition):
                if _is_severe_weather_advice_appropriate(comment.comment_text, weather_data):
                    severe_advice_matched.append(candidate)
                else:
                    normal_advice.append(candidate)
            else:
                normal_advice.append(candidate)
        
        # 悪天候時は安全重視のアドバイスを優先
        candidates = severe_advice_matched[:15] + normal_advice[:15]
        logger.info(f"アドバイス候補: 悪天候用{len(severe_advice_matched)}件を優先")

    # プロンプト生成（stateを渡す）
    prompt = _generate_prompt(candidates, weather_data, location_name, target_datetime, comment_type, state)

    try:
        response = llm_manager.generate(prompt)
        match = re.search(r"\d+", response)
        selected_index = int(match.group()) if match else 0

        logger.debug(f"LLM応答: {response}, 選択インデックス: {selected_index}, 候補数: {len(candidates)}, コメント数: {len(comments)}")
        
        if 0 <= selected_index < len(candidates):
            selected_candidate = candidates[selected_index]
            original_index = selected_candidate.get('original_index', selected_index)
            logger.info(f"LLMが{comment_type.value}を選択: candidates[{selected_index}] -> comments[{original_index}]")
            
            if 0 <= original_index < len(comments):
                return comments[original_index]
            else:
                logger.error(f"original_indexが範囲外: {original_index} (comments数: {len(comments)})")
        else:
            logger.warning(f"無効なインデックス: {selected_index} (候補数: {len(candidates)})")
        return comments[0]

    except Exception as e:
        raise ValueError(f"{comment_type.value}選択失敗: {e!s}")


def _create_candidate_dict(index: int, comment: PastComment, original_index: Optional[int] = None) -> Dict[str, Any]:
    """候補辞書を作成"""
    return {
        "index": index,
        "original_index": original_index if original_index is not None else index,
        "text": comment.comment_text,
        "season": comment.raw_data.get("season", "不明"),
    }


def _should_exclude_weather_comment(comment_text: str, weather_data: WeatherForecast) -> bool:
    """天気コメントを除外すべきかどうか判定"""
    current_weather = weather_data.weather_description.lower()
    comment_lower = comment_text.lower()
    
    # 激しい悪天候時の不適切なコメント（最優先）
    if any(severe_word in current_weather for severe_word in ["大雨", "豪雨", "嵐", "暴風", "台風", "雷"]):
        # 穏やかさや過ごしやすさを表現するコメントを除外
        if any(calm_word in comment_lower for calm_word in ["穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "のどか", "静か"]):
            return True
        # 晴天関連のコメントを除外
        if any(sunny_word in comment_lower for sunny_word in ["青空", "晴れ", "快晴", "日差し", "太陽", "陽射し", "眩しい"]):
            return True
    
    # 雨天時の不適切なコメント
    if any(rain_word in current_weather for rain_word in ["雨", "小雨", "中雨", "大雨", "豪雨"]):
        # 晴天関連のコメントを除外
        if any(sunny_word in comment_lower for sunny_word in ["青空", "晴れ", "快晴", "日差し", "太陽", "陽射し"]):
            return True
        # 外出推奨系コメントを除外
        if any(outdoor_word in comment_lower for outdoor_word in ["お出かけ", "外出", "散歩", "ピクニック", "日和"]):
            return True
        # 雨天時は穏やかなコメントも除外（雨の強さに関係なく）
        if any(calm_word in comment_lower for calm_word in ["穏やか", "過ごしやすい", "快適", "爽やか", "心地良い"]):
            return True
    
    # 晴天時の不適切なコメント  
    if any(sunny_word in current_weather for sunny_word in ["晴れ", "快晴"]):
        if any(rain_word in comment_lower for rain_word in ["雨", "じめじめ", "湿った", "どんより"]):
            return True
    
    # 曇天時の不適切なコメント
    if "くもり" in current_weather or "曇" in current_weather:
        if any(sunny_word in comment_lower for sunny_word in ["青空", "快晴", "眩しい"]):
            return True
    
    # 気温による不適切なコメント
    if weather_data.temperature < 10 and any(hot_word in comment_lower for hot_word in ["暑い", "猛暑", "酷暑"]):
        return True
    if weather_data.temperature > 30 and any(cold_word in comment_lower for cold_word in ["寒い", "冷える", "肌寒い"]):
        return True
    
    return False


def _should_exclude_advice_comment(comment_text: str, weather_data: WeatherForecast) -> bool:
    """アドバイスコメントを除外すべきかどうか判定"""
    current_weather = weather_data.weather_description.lower()
    comment_lower = comment_text.lower()
    
    # 設定から温度閾値を取得
    config = get_comment_config()
    heat_threshold = config.heat_warning_threshold
    cold_threshold = config.cold_warning_threshold
    
    # 激しい悪天候時は適切なアドバイスを優先
    if any(severe_word in current_weather for severe_word in ["大雨", "豪雨", "嵐", "暴風", "台風", "雷"]):
        # 悪天候時の不適切なアドバイスを除外
        if any(good_weather_advice in comment_lower for good_weather_advice in ["散歩", "外出", "お出かけ", "ピクニック", "日光浴"]):
            return True
        # 晴天向けアドバイスを除外
        if any(sunny_advice in comment_lower for sunny_advice in ["日焼け止め", "帽子", "サングラス", "日傘"]):
            return True
    
    # 気温による除外
    if weather_data.temperature < heat_threshold and "熱中症" in comment_text:
        return True
    if weather_data.temperature >= cold_threshold and any(word in comment_text for word in ["防寒", "暖かく", "寒さ"]):
        return True
    
    # 雨天時の不適切なアドバイス
    if any(rain_word in current_weather for rain_word in ["雨", "小雨", "中雨", "大雨", "豪雨"]):
        # 晴天向けアドバイスを除外
        if any(sunny_advice in comment_lower for sunny_advice in ["日焼け止め", "帽子", "サングラス", "日傘"]):
            return True
        # 外出推奨系アドバイスを除外
        if any(outdoor_advice in comment_lower for outdoor_advice in ["お出かけ", "外出", "散歩", "ピクニック", "日和"]):
            return True
    
    # 晴天時の不適切なアドバイス
    if any(sunny_word in current_weather for sunny_word in ["晴れ", "快晴"]):
        if any(rain_advice in comment_lower for rain_advice in ["傘", "レインコート", "濡れ"]):
            return True
    
    # 低湿度時の不適切なアドバイス
    if weather_data.humidity < 30 and any(humid_advice in comment_lower for humid_advice in ["除湿", "湿気対策"]):
        return True
    
    # 高湿度時の不適切なアドバイス  
    if weather_data.humidity > 80 and any(dry_advice in comment_lower for dry_advice in ["乾燥対策", "保湿"]):
        return True
    
    return False


def _is_weather_matched(comment_weather: str, current_weather: str) -> bool:
    """天気条件が一致するか判定"""
    if not comment_weather or not current_weather:
        return False
    return current_weather in comment_weather or comment_weather in current_weather


def _is_severe_weather_appropriate(comment_text: str, weather_data: WeatherForecast) -> bool:
    """コメントが悪天候に適しているか判定"""
    comment_lower = comment_text.lower()
    severe_config = get_severe_weather_config()
    
    # 悪天候を示唆するキーワードがあるかチェック
    severe_keywords = [
        "荒れ", "激し", "警戒", "注意", "不安定", "変わりやすい", 
        "スッキリしない", "崩れ", "悪化", "心配", "必須", "警報",
        "視界", "慎重", "安全", "控えめ", "様子", "傘", "雨",
        "ニワカ", "どんより", "じめじめ", "湿った"
    ]
    
    # 悪天候キーワードが含まれているか
    has_severe_keyword = any(keyword in comment_lower for keyword in severe_keywords)
    
    # 除外キーワードが含まれていないか
    has_exclude_keyword = any(keyword in comment_lower for keyword in severe_config.exclude_keywords_severe)
    
    return has_severe_keyword and not has_exclude_keyword


def _is_severe_weather_advice_appropriate(comment_text: str, weather_data: WeatherForecast) -> bool:
    """アドバイスが悪天候に適しているか判定"""
    comment_lower = comment_text.lower()
    severe_config = get_severe_weather_config()
    
    # 悪天候時に推奨されるアドバイスキーワード
    severe_advice_keywords = [
        "室内", "屋内", "安全", "慎重", "警戒", "注意",
        "早め", "備え", "確認", "中止", "延期", "控え",
        "無理", "避け", "気をつけ", "余裕", "ゆっくり",
        "傘", "雨具", "濡れ", "心配", "必須", "お守り"
    ]
    
    # 悪天候アドバイスキーワードが含まれているか
    has_severe_keyword = any(keyword in comment_lower for keyword in severe_advice_keywords)
    
    # 除外キーワードが含まれていないか（お出かけ系など）
    outdoor_keywords = ["散歩", "外出", "お出かけ", "ピクニック", "外遊び", "日光浴", "日焼け"]
    has_outdoor_keyword = any(keyword in comment_lower for keyword in outdoor_keywords)
    
    return has_severe_keyword and not has_outdoor_keyword


def _generate_prompt(candidates: List[Dict[str, Any]], weather_data: WeatherForecast, location_name: str, target_datetime: datetime, comment_type: CommentType, state: Optional[CommentGenerationState] = None) -> str:
    """選択用プロンプトを生成"""
    
    # 時系列データの取得と分析（直接ForecastCacheから取得）
    timeline_info = ""
    severe_future_warning = ""
    
    location_name_param = state.location_name if state else None
    if location_name_param and weather_data and weather_data.datetime:
        try:
            cache = ForecastCache()
            future_forecasts = []
            
            # 未来の予報を直接取得（3, 6, 9時間後）
            for hours in [3, 6, 9]:
                future_time = weather_data.datetime + timedelta(hours=hours)
                try:
                    forecast = cache.get_forecast_at_time(location_name_param, future_time)
                    if forecast:
                        future_forecasts.append({
                            'label': f'+{hours}h',
                            'weather': forecast.weather_description,
                            'temperature': forecast.temperature,
                            'precipitation': forecast.precipitation
                        })
                except Exception as e:
                    logger.debug(f"未来予報取得エラー (+{hours}h): {e}")
            
            # 未来の悪天候を検出
            if future_forecasts:
                severe_future = []
                for forecast in future_forecasts:
                    weather_desc = forecast.get('weather', '')
                    if any(severe in weather_desc for severe in ['大雨', '嵐', '暴風', '台風', '雷', '豪雨']):
                        severe_future.append(f"{forecast['label']}: {weather_desc}")
                
                if severe_future:
                    severe_future_warning = f"""
【重要警告】今後悪天候が予想されています:
{chr(10).join(f'- {warning}' for warning in severe_future)}
→ より強い警戒コメントを優先してください！"""
                
                timeline_info = f"""
                
【時系列予報情報】
- 今後の変化: {len(future_forecasts)}時点の予報あり
- 悪天候検出: {len(severe_future)}件の警告"""
        
        except Exception as e:
            logger.warning(f"時系列データ取得エラー: {e}")
    
    # WeatherTrendの取得（既存）
    weather_trend_info = ""
    if state and hasattr(state, 'generation_metadata'):
        weather_trend = state.generation_metadata.get('weather_trend')
        if weather_trend:
                weather_trend_info = f"""
                
今後12時間の気象変化:
- 気温変化: {weather_trend.temperature_change:+.1f}°C ({weather_trend.min_temperature:.1f}°C〜{weather_trend.max_temperature:.1f}°C)
- 天気変化: {weather_trend.get_summary()}
- 傾向: 天気は{weather_trend.weather_trend.value}、気温は{weather_trend.temperature_trend.value}"""
    
    base = f"""現在の天気条件に最も適した{comment_type.value}を選んでください。

現在の条件:
- 地点: {location_name}
- 天気: {weather_data.weather_description}
- 気温: {weather_data.temperature}°C
- 湿度: {weather_data.humidity}%
- 風速: {weather_data.wind_speed}m/s
- 降水量: {weather_data.precipitation}mm
- 日時: {target_datetime.strftime("%Y年%m月%d日 %H時")}{timeline_info}{weather_trend_info}{severe_future_warning}

候補:
{json.dumps(candidates, ensure_ascii=False, indent=2)}

"""

    if comment_type == CommentType.WEATHER_COMMENT:
        # 悪天候時の特別な指示
        severe_config = get_severe_weather_config()
        severe_instruction = ""
        
        # 現在または未来の悪天候チェック
        current_severe = severe_config.is_severe_weather(weather_data.weather_condition)
        future_severe = bool(severe_future_warning)
        
        if current_severe or future_severe:
            current_desc = f"現在は{weather_data.weather_description}" if current_severe else "現在は軽微な天候"
            future_desc = "、さらに今後悪天候が予想されています" if future_severe else ""
            
            severe_instruction = f"""
【重要】{current_desc}{future_desc}。
以下の点を最優先で考慮してください：
1. 安全性を重視したコメントを選ぶ（特に未来の悪天候を考慮）
2. 警戒や注意を促す表現を優先
3. 穏やかさや快適さを表現するコメントは避ける
4. 現在～未来の厳しい気象状況を的確に表現する
5. 【特に重要】今後悪天候が予想される場合は強い警戒コメントを選択
"""
        
        # 気象変化を考慮した追加基準
        trend_criteria = ""
        if state and hasattr(state, 'generation_metadata'):
            weather_trend = state.generation_metadata.get('weather_trend')
            if weather_trend:
                if weather_trend.has_weather_change:
                    trend_criteria = "\n4. 気象変化の考慮：今後天気が変わるため、変化を示唆する表現を優先"
                if abs(weather_trend.temperature_change) >= 5:
                    trend_criteria += f"\n5. 気温変化の考慮：{weather_trend.temperature_change:+.1f}°Cの変化があるため、それを反映した表現を優先"
        
        # 特殊気象条件の優先基準（天気コメント用）
        special_criteria = ""
        if weather_data.weather_condition.is_special_condition:
            special_criteria = f"\n\n【最優先】{weather_data.weather_condition.value}に関連するコメントを選択："
            if weather_data.weather_condition.value == "thunder":
                special_criteria += "\n   - 「雷」「雷雨」「ゴロゴロ」「急な雷雨」などの表現を含むコメント"
            elif weather_data.weather_condition.value == "fog":
                special_criteria += "\n   - 「霧」「かすむ」「視界」「霧の可能性」などの表現を含むコメント"
            elif weather_data.weather_condition.value == "storm":
                special_criteria += "\n   - 「嵐」「暴風」「荒れる」「嵐の可能性」などの表現を含むコメント"
            elif weather_data.weather_condition.value == "extreme_heat":
                special_criteria += "\n   - 「猛暑」「酷暑」「熱中症」「暑さ対策」などの表現を含むコメント"
            elif weather_data.weather_condition.value == "severe_storm":
                special_criteria += "\n   - 「大雨」「嵐」「暴風」「危険」「警戒」などの表現を含むコメント"
        
        # 悪天候時の特別な基準を追加
        severe_weather_criteria = ""
        if any(severe in weather_data.weather_description.lower() for severe in ["大雨", "豪雨", "嵐", "暴風", "台風", "雷"]):
            severe_weather_criteria = f"""

【重要】悪天候時の選択基準:
⚠️ 現在は「{weather_data.weather_description}」という激しい天候です
- 「穏やか」「過ごしやすい」「快適」などの表現は絶対に避ける
- 「荒れる」「注意」「気をつけて」などの警戒を促す表現を優先
- 悪天候の状況を適切に表現するコメントを選択"""

        # 未来の悪天候による基準強化
        future_criteria = ""
        if future_severe:
            future_criteria = "\n6. 【最重要】今後の悪天候を考慮し、より強い警戒コメントを選択（「大荒れ」「激しい」「警戒」等）"
        
        base += f"""{severe_instruction}{special_criteria}{severe_weather_criteria}

選択基準:
1. 【最優先】悪天候時は危険性や注意を促すコメント
2. 天気条件の一致（雨なら「スッキリしない空」等、嵐なら「荒れる」等）
3. 気温表現の適合性（{weather_data.temperature}°Cに適した表現）
4. 絶対禁止：悪天候時+「穏やか」系、雨天+「晴れ」系、気温不一致{trend_criteria}{future_criteria}

現在は{weather_data.weather_description}・{weather_data.temperature}°Cです。安全で適切な表現を選んでください。"""
    else:
        # 悪天候時の特別な指示（アドバイス用）
        severe_config = get_severe_weather_config()
        severe_instruction = ""
        
        # 現在または未来の悪天候チェック（アドバイス用）
        current_severe = severe_config.is_severe_weather(weather_data.weather_condition)
        future_severe = bool(severe_future_warning)
        
        if current_severe or future_severe:
            current_desc = f"現在は{weather_data.weather_description}" if current_severe else "現在は軽微な天候"
            future_desc = "、さらに今後悪天候が予想されています" if future_severe else ""
            
            severe_instruction = f"""
【重要】{current_desc}{future_desc}。
以下の点を最優先で考慮してください：
1. 安全確保を最優先としたアドバイスを選ぶ（特に未来の悪天候を考慮）
2. 室内での過ごし方や安全対策を推奨
3. 外出を推奨するようなアドバイスは避ける
4. 悪天候に対する適切な準備を促す
5. 【特に重要】今後悪天候が予想される場合は強い安全対策アドバイスを選択
"""
        
        # アドバイスも気象変化を考慮
        trend_advice = ""
        if state and hasattr(state, 'generation_metadata'):
            weather_trend = state.generation_metadata.get('weather_trend')
            if weather_trend:
                if weather_trend.weather_trend == "worsening" or weather_trend.precipitation_total > 10:
                    trend_advice = "\n4. 今後の悪天候に備えた準備系のアドバイスを優先"
                elif weather_trend.temperature_trend == "worsening":
                    config = get_comment_config()
                    if weather_trend.max_temperature > config.heat_warning_threshold:
                        trend_advice = "\n4. 今後の高温に備えた熱中症対策系のアドバイスを優先"
                
        # 設定から温度閾値を取得
        config = get_comment_config()
        heat_threshold = config.heat_warning_threshold
        cold_threshold = config.cold_warning_threshold
        
        # 特殊気象条件の優先基準（アドバイス用）
        special_criteria = ""
        if weather_data.weather_condition.is_special_condition:
            special_criteria = f"\n\n【最優先】{weather_data.weather_condition.value}に関連するアドバイスを選択："
            if weather_data.weather_condition.value == "thunder":
                special_criteria += "\n   - 「雷雨に注意」「屋内へ避難」「急な雷雨に注意」などの安全対策"
            elif weather_data.weather_condition.value == "fog":
                special_criteria += "\n   - 「視界不良に注意」「運転注意」「霧の可能性」などの安全対策"
            elif weather_data.weather_condition.value == "storm":
                special_criteria += "\n   - 「強風に注意」「外出を控える」「嵐の可能性」などの安全対策"
            elif weather_data.weather_condition.value == "extreme_heat":
                special_criteria += "\n   - 「熱中症に注意」「水分補給」「猛暑に警戒」などの安全対策"
            elif weather_data.weather_condition.value == "severe_storm":
                special_criteria += "\n   - 「大雨に警戒」「外出危険」「嵐に備える」などの安全対策"
        
        # 悪天候時のアドバイス基準を追加
        severe_weather_advice = ""
        if any(severe in weather_data.weather_description.lower() for severe in ["大雨", "豪雨", "嵐", "暴風", "台風", "雷"]):
            severe_weather_advice = f"""

【重要】悪天候時のアドバイス基準:
⚠️ 現在は「{weather_data.weather_description}」という危険な天候です
- 「外出注意」「安全第一」「傘必携」などの安全対策を最優先
- 「散歩」「お出かけ」「ピクニック」などの外出推奨は絶対に避ける
- 悪天候に適した準備・対策のアドバイスを選択"""

        base += f"""{severe_instruction}{special_criteria}{severe_weather_advice}

選択基準:
1. 【最優先】悪天候時は安全対策・注意喚起のアドバイス
2. 気温による除外（{weather_data.temperature}°C）：
   - {heat_threshold}°C未満で「熱中症」系は選択禁止
   - {cold_threshold}°C以上で「防寒」系は選択禁止
3. 天気条件への適切性（雨なら濡れ対策等、嵐なら外出控える等）
4. 実用的で具体的なアドバイス{trend_advice}

**重要**: 現在{weather_data.temperature}°Cなので、熱中症関連は{'選択禁止' if weather_data.temperature < heat_threshold else '選択可能'}です。"""

    return base + f"\n\n必ず候補から1つ選び、index (0〜{len(candidates)-1}) を半角数字のみで答えてください。"
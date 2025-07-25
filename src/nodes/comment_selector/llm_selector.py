"""LLMを使用したコメント選択ロジック"""

from __future__ import annotations
import logging
import re
from datetime import datetime
from typing import Any
from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import CommentType, PastComment
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class LLMCommentSelector:
    """LLMを使用したコメント選択クラス"""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
    
    def llm_select_comment(
        self,
        candidates: list[dict[str, Any]],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        comment_type: CommentType,
        state: CommentGenerationState | None = None
    ) -> PastComment | None:
        """LLMを使用してコメントを選択"""
        if not candidates:
            return None
        
        # 候補が1つだけの場合は選択の必要なし
        if len(candidates) == 1:
            logger.info(f"候補が1件のみ、そのまま選択: '{candidates[0]['comment']}'")
            return candidates[0]['comment_object']
        
        # 再生成時はランダム性を追加
        if getattr(state, 'exclude_previous', False):
            import random
            # 上位候補からランダムに選択（上位30%または最低3件）
            top_count = max(3, len(candidates) // 3)
            top_candidates = candidates[:top_count]
            selected = random.choice(top_candidates)
            logger.info(f"再生成モード: 上位{top_count}件からランダム選択: '{selected['comment']}'")
            return selected['comment_object']
        
        try:
            logger.info(f"LLM選択開始: {len(candidates)}件の候補から選択中...")
            
            # デバッグ: 候補リストの内容を確認
            logger.info("候補リスト詳細:")
            for i, cand in enumerate(candidates[:5]):  # 最初の5件のみ表示
                logger.info(f"  候補{i}: {cand['comment']} (天気条件: {cand['weather_condition']})")
            
            # LLMによる選択を実行
            selected_candidate = self._perform_llm_selection(
                candidates, weather_data, location_name, target_datetime, comment_type, state
            )
            
            if selected_candidate:
                logger.info(f"LLMによる選択完了: '{selected_candidate['comment']}' (インデックス: {selected_candidate['index']})")
                return selected_candidate['comment_object']
            else:
                # LLM選択に失敗した場合は最初の候補を返す
                logger.warning("LLM選択に失敗、最初の候補を使用")
                logger.warning(f"フォールバック選択: '{candidates[0]['comment']}'")
                return candidates[0]['comment_object']
                
        except Exception as e:
            logger.error(f"LLM選択エラー: {e}")
            # エラー時は最初の候補を返す
            return candidates[0]['comment_object']
    
    def _perform_llm_selection(
        self,
        candidates: list[dict[str, Any]],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        comment_type: CommentType,
        state: CommentGenerationState | None = None
    ) -> dict[str, Any | None]:
        """LLMによる実際の選択処理"""
        # 候補リストを文字列として整形
        candidates_text = self._format_candidates_for_llm(candidates)
        
        # 天気情報を整形
        weather_context = self._format_weather_context(weather_data, location_name, target_datetime, state)
        
        # デバッグ: 天気コンテキストの内容を確認
        logger.info("天気コンテキスト内容:")
        logger.info(weather_context)
        
        # コメントタイプ別のプロンプトを作成
        prompt = self._create_selection_prompt(candidates_text, weather_context, comment_type)
        
        try:
            logger.info(f"LLMに選択プロンプトを送信中...")
            logger.debug(f"プロンプト内容: {prompt[:500]}...")
            
            # LLMに選択を依頼
            response = self.llm_manager.generate(prompt)
            
            logger.info(f"LLMレスポンス: {response}")
            
            # レスポンスから選択されたインデックスを抽出
            selected_index = self._extract_selected_index(response, len(candidates))
            
            logger.info(f"抽出されたインデックス: {selected_index}")
            
            if selected_index is not None and 0 <= selected_index < len(candidates):
                return candidates[selected_index]
            else:
                logger.warning(f"無効な選択インデックス: {selected_index} (候補数: {len(candidates)})")
                logger.warning(f"LLMレスポンス全文: '{response}'")
                return None
                
        except Exception as e:
            logger.error(f"LLM API呼び出しエラー: {e}")
            logger.error(f"プロンプト長: {len(prompt)}文字")
            logger.error(f"候補数: {len(candidates)}")
            return None
    
    def _format_candidates_for_llm(self, candidates: list[dict[str, Any]]) -> str:
        """候補をLLM用に整形"""
        formatted_candidates = []
        for i, candidate in enumerate(candidates):
            formatted_candidates.append(
                f"{i}: {candidate['comment']} "
                f"(天気条件: {candidate['weather_condition']}, 使用回数: {candidate['usage_count']})"
            )
        return "\n".join(formatted_candidates)
    
    def _format_weather_context(self, weather_data: WeatherForecast, location_name: str, target_datetime: datetime, state: CommentGenerationState | None = None) -> str:
        """天気情報をLLM用に整形（時系列分析を含む）"""
        
        # 基本天気情報
        context = f"""
現在の天気情報:
- 場所: {location_name}
- 日時: {target_datetime.strftime('%Y年%m月%d日 %H時')}
- 天気: {weather_data.weather_description}
- 気温: {weather_data.temperature}°C
- 湿度: {weather_data.humidity}%
- 降水量: {weather_data.precipitation}mm
- 風速: {weather_data.wind_speed}m/s
"""
        
        # 翌日予報のシンプルな情報を追加
        month = target_datetime.month
        temp = weather_data.temperature
        
        # 季節と気温の関係
        if month in [6, 7, 8]:  # 夏
            if temp >= 35:
                context += "- 猛暑日（35℃以上）です：熱中症に厳重注意\n"
            elif temp >= 30:
                context += "- 真夏日（30℃以上）です：暑さ対策を推奨\n"
            elif temp < 25:
                context += "- 夏としては涼しめです\n"
        elif month in [12, 1, 2]:  # 冬
            if temp <= 0:
                context += "- 氷点下です：凍結や防寒対策必須\n"
            elif temp < 5:
                context += "- 真冬の寒さです：しっかりとした防寒が必要\n"
            elif temp > 15:
                context += "- 冬としては暖かめです\n"
        elif month in [3, 4, 5]:  # 春
            context += "- 春の気候です：気温変化に注意\n"
        elif month in [9, 10, 11]:  # 秋
            context += "- 秋の気候です：朝晩の冷え込みに注意\n"
        
        # 降水量の詳細
        if weather_data.precipitation > 10:
            context += "- 強雨（10mm/h以上）：外出時は十分な雨具を\n"
            context += "【最重要】雨に関するコメントを最優先で選択してください\n"
            context += "【禁止】晴天や快適さを示唆するコメントは絶対に選ばないでください\n"
        elif weather_data.precipitation > 1:
            context += "- 軽雨～中雨：傘の携帯を推奨\n"
            context += "【重要】雨に関するコメントを優先的に選択してください\n"
            context += "【注意】雨を無視したコメントは選ばないでください\n"
        elif weather_data.precipitation > 0:
            context += "- 小雨：念のため傘があると安心\n"
            context += "【重要】雨に関するコメントを優先的に選択してください\n"
            context += "【注意】雨の可能性に触れているコメントを優先してください\n"
        
        # 高温時の特別な優先度
        if weather_data.temperature >= 35.0:
            context += "\n【最重要】猛暑日のため、熱中症対策に関するコメントを最優先で選択してください\n"
        
        # 4時点の予報データを追加
        if state and hasattr(state, 'generation_metadata'):
            period_forecasts = state.generation_metadata.get('period_forecasts', [])
            logger.info(f"LLM選択用period_forecastsを取得: {len(period_forecasts) if period_forecasts else 0}件")
            if period_forecasts:
                logger.info("period_forecastsの詳細:")
                for pf in period_forecasts:
                    logger.info(f"  - {pf.datetime.strftime('%H:%M')}: {pf.weather_description}, {pf.temperature}°C, 降水量{pf.precipitation}mm")
                context += "\n【翌日の時間帯別予報】\n"
                has_rain_in_timeline = False
                max_temp_in_timeline = weather_data.temperature
                
                for forecast in period_forecasts:
                    if hasattr(forecast, 'datetime') and hasattr(forecast, 'weather_description'):
                        time_str = forecast.datetime.strftime('%H:%M')
                        temp = getattr(forecast, 'temperature', 0)
                        precip = getattr(forecast, 'precipitation', 0)
                        desc = getattr(forecast, 'weather_description', '')
                        
                        context += f"- {time_str}: {desc}, {temp}°C"
                        if precip > 0:
                            context += f", 降水量{precip}mm"
                            has_rain_in_timeline = True
                        context += "\n"
                        
                        if temp > max_temp_in_timeline:
                            max_temp_in_timeline = temp
                
                # 4時点データを考慮した追加の注意事項
                if has_rain_in_timeline:
                    context += "\n【最重要】翌日の予報に雨が含まれています。必ず雨に関するコメントを選択してください。\n"
                    context += "【絶対禁止】以下のコメントは絶対に選ばないでください：\n"
                    context += "  - 「夏空広がる」「青空」「晴天」など晴れを前提とした表現\n"
                    context += "  - 「爽やか」「カラッと」など雨と矛盾する表現\n"
                    context += "【必須】雨・傘・濡れる・降水などのキーワードを含むコメントを選んでください。\n"
                
                # 翌日の最高気温が35℃以上の場合の注意事項
                if max_temp_in_timeline >= 35:
                    context += f"\n【重要】翌日の最高気温が{max_temp_in_timeline}°Cの猛暑日です。\n"
                    context += "【必須】熱中症対策に関するコメントを選択してください。\n"
                elif max_temp_in_timeline < 30:
                    context += f"\n【注意】翌日の最高気温は{max_temp_in_timeline}°Cです。\n"
                    context += "【禁止】熱中症に関するコメントは選ばないでください。\n"
        
        return context
    
    def _create_selection_prompt(self, candidates_text: str, weather_context: str, comment_type: CommentType) -> str:
        """選択用プロンプトを作成（晴天時の不適切表現除外を強化）"""
        comment_type_desc = "天気コメント" if comment_type == CommentType.WEATHER_COMMENT else "アドバイスコメント"
        
        # 晴天時の特別な注意事項を追加
        sunny_warning = ""
        if "晴" in weather_context or "快晴" in weather_context:
            sunny_warning = """
【晴天時の特別注意】:
- 「変わりやすい空」「変わりやすい天気」「不安定」などの表現は晴れ・快晴時には不適切です
- 晴天は安定した天気なので、安定性を表現するコメントを選んでください
- 「爽やか」「穏やか」「安定」「良好」などの表現が適切です
"""
        
        # 月別の不適切表現の注意事項を追加
        import re
        month_match = re.search(r'(\d+)月', weather_context)
        month_warning = ""
        if month_match:
            month = int(month_match.group(1))
            if month == 6:
                month_warning = """
【月別注意事項】:
- 現在は6月です。以下の表現は不適切です：
  - 「残暑」（9月以降の表現）
  - 「晩夏」（8月後半の表現）
  - 「盛夏」「真夏」（7-8月の表現）
  - 「秋の気配」「秋めく」（8月後半～9月の表現）
- 適切な表現：「初夏」「梅雨」「夏の始まり」など
"""
            elif month == 7:
                month_warning = """
【月別注意事項】:
- 現在は7月です。以下の表現は不適切です：
  - 「残暑」（9月以降の表現）
  - 「初夏」（5-6月の表現）
  - 「晩夏」（8月後半の表現）
  - 「秋の気配」「秋めく」（8月後半～9月の表現）
- 適切な表現：「真夏」「盛夏」「夏本番」「猛暑」「酷暑」など
"""
            elif month == 8:
                month_warning = """
【月別注意事項】:
- 現在は8月です。以下の表現は不適切です：
  - 「残暑」（9月以降の表現）
  - 「初夏」（5-6月の表現）
  - 「秋の気配」「秋めく」（8月後半のみ許容、前半は不適切）
- 適切な表現：「真夏」「盛夏」「夏本番」「猛暑」「酷暑」「晩夏」（後半のみ）など

【矛盾チェック重要事項】:
- 「昼間も涼しい　昼間は蒸し暑い」のような時間帯の温度矛盾は絶対に避けてください
- 「涼しい」と「蒸し暑い」のような対立する温度感覚を同時に含むコメントは選ばないでください
- 雨天時に「晴れ」「快晴」「日差し」などの表現を含むコメントは選ばないでください
""".format(month)
            elif month == 9:
                month_warning = """
【月別注意事項】:
- 現在は9月です。「残暑」は適切ですが、「真夏」「盛夏」は不適切です
"""
        
        return f"""
以下の天気情報と時系列変化を総合的に分析し、最も適した{comment_type_desc}を選択してください。

{weather_context}

候補一覧:
{candidates_text}

選択基準（重要度順）:
1. 【最優先】翌日の予報のいずれかの時間帯で降水がある場合は雨関連のコメント、いずれかの時間帯で35℃以上の場合は熱中症対策のコメント
2. 現在の天気だけでなく、翌日の9時・12時・15時・18時の予報全体を考慮
3. 天気の安定性や変化パターンに合致している（雨が予報されている場合は「晴天」「夏空」などの表現は不適切）
4. 時系列変化（12時間前後）を考慮した適切性
5. 地域特性（北海道の寒さ、沖縄の暑さなど）
6. 季節感が適切（月に応じた適切な表現）
7. 自然で読みやすい表現

{sunny_warning}
{month_warning}

特に以下を重視してください:
- 天気の安定性（晴れ・快晴は安定、雨・曇りは変化しやすい）
- 気温変化の傾向（上昇中、下降中、安定）
- 天気の変化予想（悪化、改善、安定）
- その地域の気候特性
- 現在の月に適した表現（不適切な季節表現を避ける）

【重要】選択した候補の番号のみを回答してください。
説明は不要です。数字のみを返してください。

例: 2
"""
    
    def _extract_selected_index(self, response: str, max_index: int) -> int | None:
        """LLMレスポンスから選択インデックスを抽出（堅牢化）"""
        response_clean = response.strip()
        
        # パターン1: 単純な数字のみの回答（最優先）
        if re.match(r'^\d+$', response_clean):
            try:
                index = int(response_clean)
                if 0 <= index < max_index:
                    return index
            except ValueError:
                pass
        
        # パターン2: 行頭の数字（例: "3\n説明文..."）
        match = re.match(r'^(\d+)', response_clean)
        if match:
            try:
                index = int(match.group(1))
                if 0 <= index < max_index:
                    return index
            except ValueError:
                pass
        
        # パターン3: 「答え: 2」「選択: 5」などの形式
        patterns = [
            r'(?:答え|選択|回答|結果)[:：]\s*(\d+)',
            r'(\d+)\s*(?:番|番目)',
            r'インデックス[:：]\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_clean, re.IGNORECASE)
            if match:
                try:
                    index = int(match.group(1))
                    if 0 <= index < max_index:
                        return index
                except ValueError:
                    continue
        
        # パターン4: 最後の手段として最初に見つかった数字（但し範囲内のもの）
        numbers = re.findall(r'\d+', response_clean)
        for num_str in numbers:
            try:
                index = int(num_str)
                if 0 <= index < max_index:
                    logger.warning(f"数値抽出: フォールバック使用 - '{response_clean}' -> {index}")
                    return index
            except ValueError:
                continue
        
        logger.error(f"数値抽出失敗: '{response_clean}' (範囲: 0-{max_index-1})")
        logger.error(f"元のレスポンス: '{response}'")
        logger.error(f"response_clean: '{response_clean}'")
        return None
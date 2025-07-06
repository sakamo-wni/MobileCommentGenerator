"""LLMを使用したコメント選択ロジック"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

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
        candidates: List[Dict[str, Any]],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        comment_type: CommentType,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
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
        candidates: List[Dict[str, Any]],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        comment_type: CommentType,
        state=None
    ) -> Optional[Dict[str, Any]]:
        """LLMによる実際の選択処理"""
        # 候補リストを文字列として整形
        candidates_text = self._format_candidates_for_llm(candidates)
        
        # 天気情報を整形
        weather_context = self._format_weather_context(weather_data, location_name, target_datetime, state)
        
        # コメントタイプ別のプロンプトを作成
        prompt = self._create_selection_prompt(candidates_text, weather_context, comment_type)
        
        try:
            logger.info(f"LLMに選択プロンプトを送信中...")
            logger.debug(f"プロンプト内容: {prompt[:200]}...")
            
            # LLMに選択を依頼
            response = self.llm_manager.generate(prompt)
            
            logger.info(f"LLMレスポンス: {response}")
            
            # レスポンスから選択されたインデックスを抽出
            selected_index = self._extract_selected_index(response, len(candidates))
            
            logger.info(f"抽出されたインデックス: {selected_index}")
            
            if selected_index is not None and 0 <= selected_index < len(candidates):
                return candidates[selected_index]
            else:
                logger.warning(f"無効な選択インデックス: {selected_index}")
                return None
                
        except Exception as e:
            logger.error(f"LLM API呼び出しエラー: {e}")
            return None
    
    def _format_candidates_for_llm(self, candidates: List[Dict[str, Any]]) -> str:
        """候補をLLM用に整形"""
        formatted_candidates = []
        for i, candidate in enumerate(candidates):
            formatted_candidates.append(
                f"{i}: {candidate['comment']} "
                f"(天気条件: {candidate['weather_condition']}, 使用回数: {candidate['usage_count']})"
            )
        return "\n".join(formatted_candidates)
    
    def _format_weather_context(self, weather_data: WeatherForecast, location_name: str, target_datetime: datetime, state=None) -> str:
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
        elif weather_data.precipitation > 1:
            context += "- 軽雨～中雨：傘の携帯を推奨\n"
        elif weather_data.precipitation > 0:
            context += "- 小雨：念のため傘があると安心\n"
        
        # 将来の降水予報も追加（forecast_collectionから取得）
        if state and hasattr(state, 'generation_metadata'):
            forecast_collection = state.generation_metadata.get('forecast_collection')
            if forecast_collection and hasattr(forecast_collection, 'forecasts'):
                future_rain = []
                # 翌日の予報のみ対象
                target_date = (weather_data.datetime.date() if hasattr(weather_data, 'datetime') 
                              else datetime.now().date())
                
                for forecast in forecast_collection.forecasts:
                    if forecast.datetime.date() == target_date:
                        if forecast.precipitation > 0:
                            future_rain.append((forecast.datetime.strftime('%H時'), forecast.precipitation))
                
                if future_rain:
                    context += "\n【降水予報】\n"
                    for time, precip in future_rain:
                        context += f"- {time}: {precip}mm/hの降水予想\n"
        
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
        
        # 雨天時の特別な注意事項を追加
        rain_warning = ""
        # 現在の降水量チェック
        import re
        current_precip = 0
        precip_match = re.search(r'降水量:\s*([\d.]+)mm', weather_context)
        if precip_match:
            current_precip = float(precip_match.group(1))
        
        # 予報の降水量チェック
        has_future_rain = "【降水予報】" in weather_context
        
        if current_precip > 0 or has_future_rain:
            if current_precip > 0:
                rain_warning = f"""
【雨天時の特別注意】:
- 現在降水量が{current_precip}mmあります。必ず雨に言及したコメントを選んでください
- 天気コメントでは「雨」「降雨」「雨が」「にわか雨」などの雨関連表現を含むものを優先
- アドバイスコメントでは「傘」「雨具」「雨対策」などの実用的なアドバイスを含むものを優先
- 「晴れ」「青空」「日差し」などの晴天表現を含むコメントは絶対に選ばないでください
"""
            else:
                rain_warning = """
【降水予報がある場合の特別注意】:
- 今後降水が予想されています。雨への備えに言及したコメントを選んでください
- 天気コメントでは「にわか雨」「天気の変化」「傘の準備」などの表現を含むものを優先
- アドバイスコメントでは「傘」「雨具」などの準備を促すものを優先
- 現在晴れていても、将来の雨を考慮したコメントを選んでください
"""
        
        # 月別の不適切表現の注意事項を追加
        import re
        month_match = re.search(r'(\d+)月', weather_context)
        month_warning = ""
        if month_match:
            month = int(month_match.group(1))
            if month in [6, 7, 8]:  # 夏
                month_warning = """
【月別注意事項】:
- 現在は{0}月です。以下の表現は不適切です：
  - 「残暑」（9月以降の表現）
  - 「初夏」（5-6月の表現）
  - 「晩夏」（8月後半の表現）
  - 「秋の気配」「秋めく」（8月後半～9月の表現）
- 適切な表現：「真夏」「盛夏」「夏本番」「猛暑」「酷暑」など
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
1. 現在の天気・気温に最も適している
2. 天気の安定性や変化パターンに合致している
3. 時系列変化（12時間前後）を考慮した適切性
4. 地域特性（北海道の寒さ、沖縄の暑さなど）
5. 季節感が適切（月に応じた適切な表現）
6. 自然で読みやすい表現

{sunny_warning}
{rain_warning}
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
    
    def _extract_selected_index(self, response: str, max_index: int) -> Optional[int]:
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
        return None
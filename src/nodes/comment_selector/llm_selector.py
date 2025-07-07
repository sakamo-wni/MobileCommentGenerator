"""LLMを使用したコメント選択ロジック"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import CommentType, PastComment
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager
from src.config.weather_constants import SEASON_MONTHS, SEASONAL_TEMP_THRESHOLDS

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
        state: Optional[CommentGenerationState] = None
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
                # 矛盾チェックを追加
                selected_candidate = candidates[selected_index]
                if comment_type == CommentType.WEATHER_COMMENT:
                    # 天気コメントが選択された場合、矛盾チェックを行う
                    is_valid = self._check_comment_contradictions(
                        selected_candidate['comment'], 
                        weather_data,
                        location_name,
                        target_datetime
                    )
                    if not is_valid:
                        logger.warning(f"選択されたコメントに矛盾が検出されました: '{selected_candidate['comment']}'")
                        # 矛盾が検出された場合、次の候補を試す
                        for i, candidate in enumerate(candidates):
                            if i != selected_index:
                                is_valid = self._check_comment_contradictions(
                                    candidate['comment'],
                                    weather_data,
                                    location_name,
                                    target_datetime
                                )
                                if is_valid:
                                    logger.info(f"代替候補を選択: '{candidate['comment']}'")
                                    return candidate
                        # すべて矛盾している場合は最初の候補を返す
                        logger.warning("すべての候補に矛盾が検出されました。最初の候補を使用します。")
                
                return selected_candidate
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
            # 使用回数はLLMの判断を歪める可能性があるため表示しない
            formatted_candidates.append(
                f"{i}: {candidate['comment']}"
            )
        return "\n".join(formatted_candidates)
    
    def _format_weather_context(self, weather_data: WeatherForecast, location_name: str, target_datetime: datetime, state: Optional[CommentGenerationState] = None) -> str:
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
        season = self._get_season(month)
        
        if season == 'summer':
            if temp >= SEASONAL_TEMP_THRESHOLDS['summer']['extreme_hot']:
                context += "- 猛暑日（35℃以上）です：熱中症に厳重注意\n"
            elif temp >= SEASONAL_TEMP_THRESHOLDS['summer']['hot']:
                context += "- 真夏日（30℃以上）です：暑さ対策を推奨\n"
            elif temp < SEASONAL_TEMP_THRESHOLDS['summer']['cool']:
                context += "- 夏としては涼しめです\n"
        elif season == 'winter':
            if temp <= SEASONAL_TEMP_THRESHOLDS['winter']['freezing']:
                context += "- 氷点下です：凍結や防寒対策必須\n"
            elif temp < SEASONAL_TEMP_THRESHOLDS['winter']['cold']:
                context += "- 真冬の寒さです：しっかりとした防寒が必要\n"
            elif temp > SEASONAL_TEMP_THRESHOLDS['winter']['warm']:
                context += "- 冬としては暖かめです\n"
        elif season == 'spring':
            context += "- 春の気候です：気温変化に注意\n"
        elif season == 'autumn':
            context += "- 秋の気候です：朝晩の冷え込みに注意\n"
        
        # 全時間帯の降水量をチェック
        max_precipitation = weather_data.precipitation
        rain_times = []
        
        # stateから4時点の予報データを取得
        if state and hasattr(state, 'generation_metadata') and state.generation_metadata:
            period_forecasts = state.generation_metadata.get('period_forecasts', [])
            for forecast in period_forecasts:
                if forecast.precipitation > 0:
                    rain_times.append(f"{forecast.datetime.strftime('%H時')}({forecast.precipitation}mm)")
                    max_precipitation = max(max_precipitation, forecast.precipitation)
        
        # 降水量の詳細（最大降水量で判定）
        if rain_times:
            context += f"\n【降水予報】翌日の降水時間帯: {', '.join(rain_times)}\n"
            context += "\n🚨【厳重注意】雨が降る予報です。以下の表現は絶対に選ばないでください：\n"
            context += "- 「穏やか」「のどか」「快適」「過ごしやすい」\n"
            context += "- 「晴れ」「青空」「日差し」などの晴天表現\n"
            context += "- 「お出かけ日和」「散歩日和」などの外出推奨表現\n"
        
        if max_precipitation > 10:
            context += "- 強雨（10mm/h以上）：外出時は十分な雨具を\n"
            context += "【最重要】雨に関するコメントを最優先で選択してください\n"
        elif max_precipitation > 1:
            context += "- 軽雨～中雨：傘の携帯を推奨\n"
            context += "【重要】雨に関するコメントを優先的に選択してください\n"
        elif max_precipitation > 0:
            context += "- 小雨：念のため傘があると安心\n"
            context += "【重要】雨に関するコメントを優先的に選択してください\n"
        
        # 高温時の特別な優先度
        if weather_data.temperature >= 35.0:
            context += "\n【最重要】猛暑日のため、熱中症対策に関するコメントを最優先で選択してください\n"
        
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
1. 【最優先】降水がある場合は雨関連のコメント、35℃以上の場合は熱中症対策のコメント
   - 雨予報時に「穏やか」「快適」等を選ぶのは厳禁
2. 現在の天気・気温に最も適している
3. 天気の安定性や変化パターンに合致している
4. 時系列変化（12時間前後）を考慮した適切性
5. 地域特性（北海道の寒さ、沖縄の暑さなど）
6. 季節感が適切（月に応じた適切な表現）
7. 自然で読みやすい表現

【絶対的ルール】
- 降水予報がある場合、雨に言及しないコメントは選択禁止
- 気温と矛盾する表現（34°C未満で「熱中症」、25°C以上で「涼しい」等）は選択禁止

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
    
    def _get_season(self, month: int) -> str:
        """月から季節を判定"""
        for season, months in SEASON_MONTHS.items():
            if month in months:
                return season
        return 'unknown'
    
    def _check_comment_contradictions(
        self, 
        comment_text: str, 
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime
    ) -> bool:
        """LLMを使用してコメント内の矛盾をチェック"""
        
        # 雨予報時の禁止表現チェック
        if weather_data.precipitation > 0 or "雨" in weather_data.weather_description:
            rain_forbidden_words = [
                "穏やか", "のどか", "快適", "過ごしやすい", "心地良い",
                "晴れ", "青空", "日差し", "太陽", "陽射し",
                "お出かけ日和", "散歩日和", "ピクニック",
                "カラッと", "さっぱり", "爽やか"
            ]
            for word in rain_forbidden_words:
                if word in comment_text:
                    logger.info(f"雨予報時の禁止ワード検出: '{word}' in '{comment_text}'")
                    return False
        
        # 簡単な矛盾パターンを事前チェック（LLM呼び出しを減らすため）
        contradiction_patterns = [
            ("過ごしやすい", "蒸し暑い"),
            ("涼しい", "暑い"),
            ("爽やか", "じめじめ"),
            ("快適", "厳しい"),
            ("穏やか", "荒れ"),
            ("カラッと", "湿っぽい"),
            ("さわやか", "ムシムシ"),
            ("ひんやり", "汗ばむ"),
        ]
        
        comment_lower = comment_text.lower()
        for word1, word2 in contradiction_patterns:
            if word1 in comment_lower and word2 in comment_lower:
                logger.info(f"矛盾パターン検出: '{word1}' と '{word2}' が同時に含まれる")
                return False
        
        # より複雑な矛盾はLLMで判定
        try:
            prompt = f"""
以下のコメントが、指定された天気条件において矛盾や不適切な表現を含んでいないか判定してください。

【天気情報】
- 地点: {location_name}
- 日時: {target_datetime.strftime('%Y年%m月%d日 %H時')}
- 天気: {weather_data.weather_description}
- 気温: {weather_data.temperature}°C
- 湿度: {weather_data.humidity}%
- 降水量: {weather_data.precipitation}mm

【コメント】
{comment_text}

【判定基準】
1. コメント内に相反する表現が含まれていないか（例：「過ごしやすいが蒸し暑い」）
2. 気温と表現が矛盾していないか（例：34°Cで「涼しい」）
3. 天気と表現が矛盾していないか（例：雨なのに「カラッと」）
4. 季節感が適切か（例：7月に「残暑」）

矛盾がない場合は「OK」、矛盾がある場合は「NG」とだけ回答してください。
"""
            
            response = self.llm_manager.generate(prompt)
            response_clean = response.strip().upper()
            
            if "OK" in response_clean:
                return True
            elif "NG" in response_clean:
                logger.info(f"LLMが矛盾を検出: '{comment_text}'")
                return False
            else:
                # 判定が曖昧な場合は通す
                logger.warning(f"LLM矛盾チェックの応答が不明瞭: {response}")
                return True
                
        except Exception as e:
            logger.error(f"LLM矛盾チェックエラー: {e}")
            # エラー時は通す
            return True
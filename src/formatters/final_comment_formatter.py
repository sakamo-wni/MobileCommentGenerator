"""
最終コメントフォーマッター
"""

from typing import Optional, Any
import logging
import re

from src.data.comment_generation_state import CommentGenerationState

logger = logging.getLogger(__name__)


class FinalCommentFormatter:
    """最終コメントを整形・安全性チェックするクラス"""
    
    def determine_final_comment(self, state: CommentGenerationState) -> str:
        """
        最終コメントを確定
        
        優先順位:
        1. generated_comment（LLM生成）
        2. selected_pair の weather_comment
        3. エラーを発生させる
        """
        logger.debug("最終コメント確定処理開始")
        logger.debug(f"state.generated_comment = '{getattr(state, 'generated_comment', None)}'")
        logger.debug(f"state.selected_pair = {getattr(state, 'selected_pair', None)}")
        
        # 最終安全チェック用データ
        weather_data = state.weather_data
        final_comment = None
        
        # LLM生成コメントがある場合
        if state.generated_comment:
            final_comment = state.generated_comment
            logger.info(f"LLM生成コメント使用: '{final_comment}'")
        else:
            # 選択されたペアがある場合 - 正しい形式で構成
            selected_pair = state.selected_pair
            if selected_pair:
                weather_comment = ""
                advice_comment = ""
                
                if hasattr(selected_pair, "weather_comment") and selected_pair.weather_comment:
                    weather_comment = selected_pair.weather_comment.comment_text
                    
                if hasattr(selected_pair, "advice_comment") and selected_pair.advice_comment:
                    advice_comment = selected_pair.advice_comment.comment_text
                
                logger.debug(f"選択されたペア: weather='{weather_comment}', advice='{advice_comment}'")
                
                # 正しい形式で結合（weather + 全角スペース + advice）
                if weather_comment and advice_comment:
                    final_comment = f"{weather_comment}　{advice_comment}"
                    logger.info(f"ペア結合コメント使用: '{final_comment}'")
                elif weather_comment:
                    final_comment = weather_comment
                    logger.info(f"天気コメントのみ使用: '{final_comment}'")
                elif advice_comment:
                    final_comment = advice_comment
                    logger.info(f"アドバイスコメントのみ使用: '{final_comment}'")
        
        if not final_comment:
            # コメントが生成できなかった場合はエラー
            raise ValueError(
                "コメントの生成に失敗しました。LLMまたは過去データから適切なコメントを取得できませんでした。"
            )
        
        # 最終安全チェック
        final_comment = self._apply_safety_checks(final_comment, weather_data)
        
        logger.info(f"最終コメント確定: '{final_comment}'")
        return final_comment
    
    def _apply_safety_checks(self, final_comment: str, weather_data: Optional[Any]) -> str:
        """最終安全チェック：特殊気象条件に対する不適切なコメント組み合わせの修正"""
        if not weather_data or not final_comment:
            return final_comment
        
        current_weather = weather_data.weather_description.lower()
        temperature = weather_data.temperature if hasattr(weather_data, 'temperature') else 20.0
        weather_condition = weather_data.weather_condition.value
        
        # 特殊気象条件ごとの文脈保持型安全性チェック
        if weather_condition == "thunder" or "雷" in current_weather:
            final_comment = self._check_thunder_safety(final_comment)
            
        elif weather_condition == "fog" or "霧" in current_weather:
            final_comment = self._check_fog_safety(final_comment)
            
        elif weather_condition in ["storm", "severe_storm"] or any(word in current_weather for word in ["嵐", "暴風"]):
            final_comment = self._check_storm_safety(final_comment)
            
        elif weather_condition == "heavy_rain" or "大雨" in current_weather:
            final_comment = self._check_heavy_rain_safety(final_comment)
            
        # 雨天で不適切なコメント全般の修正（文脈保持版）
        elif "雨" in current_weather:
            final_comment = self._check_rain_safety(final_comment)
        
        return final_comment
    
    def _check_thunder_safety(self, comment: str) -> str:
        """雷天候の安全性チェック"""
        logger.info(f"雷天候検出: '{comment}'")
        if "　" in comment:
            parts = comment.split("　")
            # 文脈を保持しながら安全性を確保
            if not any(word in comment for word in ["雷", "屋内", "危険", "注意"]):
                # アドバイス部分に安全情報を追加
                parts[1] = f"{parts[1]}（雷注意・屋内へ）"
                comment = "　".join(parts)
                logger.info(f"雷天候安全性強化: '{comment}'")
        return comment
    
    def _check_fog_safety(self, comment: str) -> str:
        """霧天候の安全性チェック"""
        logger.info(f"霧天候検出: '{comment}'")
        if "　" in comment:
            parts = comment.split("　")
            if not any(word in comment for word in ["霧", "視界", "運転", "注意"]):
                # 文脈を保持して視界注意を追加
                parts[1] = f"{parts[1]}（視界注意）"
                comment = "　".join(parts)
                logger.info(f"霧天候安全性強化: '{comment}'")
        return comment
    
    def _check_storm_safety(self, comment: str) -> str:
        """嵐天候の安全性チェック"""
        logger.info(f"嵐天候検出: '{comment}'")
        if "　" in comment:
            parts = comment.split("　")
            if not any(word in comment for word in ["嵐", "暴風", "強風", "危険"]):
                # 文脈を保持して強風注意を追加
                parts[1] = f"{parts[1]}（強風危険・外出注意）"
                comment = "　".join(parts)
                logger.info(f"嵐天候安全性強化: '{comment}'")
        return comment
    
    def _check_heavy_rain_safety(self, comment: str) -> str:
        """大雨天候の安全性チェック"""
        logger.info(f"大雨天候検出: '{comment}'")
        if "　" in comment:
            parts = comment.split("　")
            if not any(word in comment for word in ["大雨", "洪水", "冠水", "危険"]):
                # 文脈を保持して大雨注意を追加
                parts[1] = f"{parts[1]}（大雨・冠水注意）"
                comment = "　".join(parts)
                logger.info(f"大雨天候安全性強化: '{comment}'")
        return comment
    
    def _check_rain_safety(self, comment: str) -> str:
        """雨天候の安全性チェック"""
        logger.info(f"雨天コメント検証: '{comment}'")
        
        inappropriate_keywords = ["熱中症", "暑い", "ムシムシ", "花粉", "日焼け", "紫外線", "散歩", "ピクニック", "外遊び"]
        needs_correction = any(keyword in comment for keyword in inappropriate_keywords)
        
        if needs_correction:
            logger.info(f"雨天不適切コメント検出: '{comment}'")
            
            if "　" in comment:  # 複合コメントの場合
                parts = comment.split("　")
                
                # 文脈を保持しながら安全な修正（単語境界考慮）
                if any(word in parts[0] for word in inappropriate_keywords):
                    # 安全な単語置換（前後の文字を考慮）
                    weather_part = parts[0]
                    
                    # 完全一致または単語境界での置換
                    if re.search(r'\b熱中症\b', weather_part):
                        weather_part = re.sub(r'\b熱中症\b', '雨模様', weather_part)
                    if re.search(r'\b暑い\b', weather_part):
                        weather_part = re.sub(r'\b暑い\b', '涼しい', weather_part)
                    if re.search(r'\bムシムシ\b', weather_part):
                        weather_part = re.sub(r'\bムシムシ\b', 'しっとり', weather_part)
                    if re.search(r'\b花粉\b', weather_part):
                        weather_part = re.sub(r'\b花粉\b', '雨', weather_part)
                    
                    # 日焼け・紫外線関連の慎重な置換
                    for keyword in ["日焼け", "紫外線"]:
                        pattern = rf'\b{re.escape(keyword)}\b'
                        if re.search(pattern, weather_part):
                            weather_part = re.sub(pattern, '雨', weather_part)
                    
                    parts[0] = weather_part
                
                # アドバイス部分も安全な修正
                if any(word in parts[1] for word in inappropriate_keywords):
                    advice_part = parts[1]
                    
                    # 外出活動の安全な置換
                    if re.search(r'\b散歩\b', advice_part):
                        advice_part = re.sub(r'\b散歩\b', '室内活動', advice_part)
                        advice_part = f"{advice_part}（雨天のため）"
                    elif re.search(r'\bピクニック\b', advice_part):
                        advice_part = re.sub(r'\bピクニック\b', '屋内', advice_part)
                        advice_part = f"{advice_part}（雨天のため）"
                    elif re.search(r'\b外遊び\b', advice_part):
                        advice_part = re.sub(r'\b外遊び\b', '室内遊び', advice_part)
                        advice_part = f"{advice_part}（雨天のため）"
                    elif any(re.search(rf'\b{word}\b', advice_part) for word in ["熱中症", "暑い", "ムシムシ"]):
                        advice_part = "傘をお忘れなく"
                    else:
                        advice_part = f"{advice_part}（雨にご注意）"
                    
                    parts[1] = advice_part
                
                comment = "　".join(parts)
            else:
                # 単体コメントは最小限の調整
                comment = f"{comment}（雨天注意）"
            
            logger.info(f"雨天修正後: '{comment}'")
        
        return comment
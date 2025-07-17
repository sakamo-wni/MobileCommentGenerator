"""
コメント重複除去ユーティリティ

天気コメントとアドバイスコメントを結合する際に、
類似した内容の重複を検出し、適切に除去する機能を提供します。
"""

import re
import logging
from typing import Tuple, List, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class CommentDeduplicator:
    """コメントの重複を除去するクラス"""
    
    # 重複パターンの定義
    DUPLICATE_PATTERNS = [
        # 熱中症関連
        {
            "keywords": ["熱中症"],
            "variations": ["熱中症に警戒", "熱中症に注意", "熱中症対策を", "熱中症に気をつけて"],
            "priority_order": ["熱中症に警戒", "熱中症に注意", "熱中症対策を", "熱中症に気をつけて"]
        },
        # 雨関連
        {
            "keywords": ["雨", "傘"],
            "variations": ["雨に注意", "雨に警戒", "傘をお忘れなく", "傘の準備を", "雨具の準備を"],
            "priority_order": ["雨に警戒", "雨に注意", "傘をお忘れなく", "傘の準備を", "雨具の準備を"]
        },
        # 風関連
        {
            "keywords": ["風", "強風"],
            "variations": ["強風に注意", "風に注意", "強風に警戒", "風に気をつけて"],
            "priority_order": ["強風に警戒", "強風に注意", "風に注意", "風に気をつけて"]
        },
        # 寒さ関連
        {
            "keywords": ["寒", "冷"],
            "variations": ["寒さ対策を", "防寒対策を", "暖かくして", "冷え込みに注意"],
            "priority_order": ["寒さ対策を", "防寒対策を", "暖かくして", "冷え込みに注意"]
        }
    ]
    
    @classmethod
    def deduplicate_comment(cls, weather_comment: str, advice_comment: str) -> Tuple[str, str]:
        """
        天気コメントとアドバイスコメントの重複を除去
        
        Args:
            weather_comment: 天気コメント
            advice_comment: アドバイスコメント
            
        Returns:
            重複除去後の (天気コメント, アドバイスコメント) のタプル
        """
        logger.debug(f"重複除去前 - 天気: '{weather_comment}', アドバイス: '{advice_comment}'")
        
        # 各パターンをチェック
        for pattern in cls.DUPLICATE_PATTERNS:
            weather_comment, advice_comment = cls._check_and_remove_duplicate_pattern(
                weather_comment, advice_comment, pattern
            )
        
        # 完全一致の重複チェック
        if weather_comment == advice_comment:
            logger.info(f"完全一致の重複を検出: '{weather_comment}'")
            # アドバイスコメントを汎用的なものに変更
            advice_comment = "今日も一日頑張りましょう"
        
        # 部分一致の重複チェック（80%以上の類似度）
        similarity = cls._calculate_similarity(weather_comment, advice_comment)
        if similarity > 0.8:
            logger.info(f"高い類似度({similarity:.2f})を検出: 天気='{weather_comment}', アドバイス='{advice_comment}'")
            # アドバイスコメントを変更
            if "熱中症" in advice_comment:
                advice_comment = "水分補給をお忘れなく"
            elif "雨" in advice_comment or "傘" in advice_comment:
                advice_comment = "足元にご注意ください"
            elif "風" in advice_comment:
                advice_comment = "飛ばされ物にご注意を"
            elif "寒" in advice_comment or "冷" in advice_comment:
                advice_comment = "体調管理にご注意を"
            else:
                advice_comment = "今日も一日頑張りましょう"
        
        logger.debug(f"重複除去後 - 天気: '{weather_comment}', アドバイス: '{advice_comment}'")
        return weather_comment, advice_comment
    
    @classmethod
    def _check_and_remove_duplicate_pattern(
        cls, 
        weather_comment: str, 
        advice_comment: str, 
        pattern: dict
    ) -> Tuple[str, str]:
        """特定のパターンの重複をチェックして除去"""
        # 両方のコメントに同じキーワードが含まれているかチェック
        has_keyword_in_weather = any(keyword in weather_comment for keyword in pattern["keywords"])
        has_keyword_in_advice = any(keyword in advice_comment for keyword in pattern["keywords"])
        
        if has_keyword_in_weather and has_keyword_in_advice:
            # 両方に含まれている場合、優先度の高いものを残す
            weather_variation = cls._find_variation(weather_comment, pattern["variations"])
            advice_variation = cls._find_variation(advice_comment, pattern["variations"])
            
            if weather_variation and advice_variation:
                weather_priority = cls._get_priority(weather_variation, pattern["priority_order"])
                advice_priority = cls._get_priority(advice_variation, pattern["priority_order"])
                
                logger.info(f"重複パターン検出: 天気='{weather_variation}', アドバイス='{advice_variation}'")
                
                # 同じパターンのバリエーションがある場合は常に重複として扱う
                logger.info(f"重複を除去します: 優先度 天気={weather_priority}, アドバイス={advice_priority}")
                
                # キーワードに応じた代替コメントに変更
                if "熱中症" in pattern["keywords"]:
                    advice_comment = cls._replace_heatstroke_advice(advice_comment)
                elif "雨" in pattern["keywords"]:
                    advice_comment = cls._replace_rain_advice(advice_comment)
                elif "風" in pattern["keywords"]:
                    advice_comment = cls._replace_wind_advice(advice_comment)
                elif "寒" in pattern["keywords"]:
                    advice_comment = cls._replace_cold_advice(advice_comment)
        
        return weather_comment, advice_comment
    
    @classmethod
    def _find_variation(cls, text: str, variations: List[str]) -> Optional[str]:
        """テキスト内に含まれるバリエーションを検索"""
        for variation in variations:
            if variation in text:
                return variation
        return None
    
    @classmethod
    def _get_priority(cls, variation: str, priority_order: List[str]) -> int:
        """バリエーションの優先度を取得（低い数値ほど高優先度）"""
        try:
            return priority_order.index(variation)
        except ValueError:
            return len(priority_order)
    
    @classmethod
    def _calculate_similarity(cls, text1: str, text2: str) -> float:
        """2つのテキストの類似度を計算"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    @classmethod
    def _replace_heatstroke_advice(cls, advice_comment: str) -> str:
        """熱中症関連のアドバイスを代替コメントに変更"""
        replacements = [
            ("熱中症に警戒", "こまめな水分補給を"),
            ("熱中症に注意", "涼しい場所で休憩を"),
            ("熱中症対策を", "無理せず休憩を"),
            ("熱中症に気をつけて", "体調管理に気をつけて")
        ]
        
        for original, replacement in replacements:
            if original in advice_comment:
                return advice_comment.replace(original, replacement)
        
        # 一般的な置換
        return re.sub(r'熱中症[にをで]\S+', '水分補給をお忘れなく', advice_comment)
    
    @classmethod
    def _replace_rain_advice(cls, advice_comment: str) -> str:
        """雨関連のアドバイスを代替コメントに変更"""
        replacements = [
            ("雨に警戒", "足元にご注意を"),
            ("雨に注意", "濡れないようにご注意を"),
            ("傘をお忘れなく", "雨具の準備をしっかりと"),
            ("傘の準備を", "レインコートも便利です"),
            ("雨具の準備を", "防水対策をしっかりと")
        ]
        
        for original, replacement in replacements:
            if original in advice_comment:
                return advice_comment.replace(original, replacement)
        
        return advice_comment
    
    @classmethod
    def _replace_wind_advice(cls, advice_comment: str) -> str:
        """風関連のアドバイスを代替コメントに変更"""
        replacements = [
            ("強風に警戒", "飛ばされ物にご注意を"),
            ("強風に注意", "しっかりと物を固定して"),
            ("風に注意", "髪や帽子が飛ばされないように"),
            ("風に気をつけて", "自転車は特にご注意を")
        ]
        
        for original, replacement in replacements:
            if original in advice_comment:
                return advice_comment.replace(original, replacement)
        
        return advice_comment
    
    @classmethod
    def _replace_cold_advice(cls, advice_comment: str) -> str:
        """寒さ関連のアドバイスを代替コメントに変更"""
        replacements = [
            ("寒さ対策を", "暖かい飲み物でほっと一息"),
            ("防寒対策を", "マフラーや手袋も忘れずに"),
            ("暖かくして", "重ね着で調節を"),
            ("冷え込みに注意", "朝晩は特に暖かく")
        ]
        
        for original, replacement in replacements:
            if original in advice_comment:
                return advice_comment.replace(original, replacement)
        
        return advice_comment
    
    @classmethod
    def _adjust_weather_comment(cls, weather_comment: str, keywords: List[str]) -> str:
        """天気コメントを調整（必要に応じて）"""
        # 現在は調整せずそのまま返す
        # 将来的に必要に応じて実装
        return weather_comment


def deduplicate_final_comment(final_comment: str) -> str:
    """
    最終コメント全体から重複を除去
    
    Args:
        final_comment: 結合済みの最終コメント
        
    Returns:
        重複除去後のコメント
    """
    if "　" not in final_comment:
        return final_comment
    
    parts = final_comment.split("　", 1)
    if len(parts) != 2:
        return final_comment
    
    weather_part, advice_part = CommentDeduplicator.deduplicate_comment(parts[0], parts[1])
    return f"{weather_part}　{advice_part}"
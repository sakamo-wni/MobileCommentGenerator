"""重複チェック共通ユーティリティ"""

import logging
import re
from typing import Tuple, Set

logger = logging.getLogger(__name__)

# 定数
PUNCTUATION_PATTERN = re.compile(r'[、。・！？｢｣「」『』（）［］【】\s]+')


class DuplicationChecker:
    """重複チェックの共通ロジックを提供するユーティリティクラス"""
    
    @staticmethod
    def check_repetitive_concepts(weather_text: str, advice_text: str) -> bool:
        """同じ概念の繰り返しをチェック"""
        repetitive_patterns = [
            {
                "concept": "気温差",
                "expressions": ["気温差大", "寒暖差大", "温度差大", "朝昼の気温差", 
                              "朝晩と昼間の気温差", "朝と夜の気温差", "日中と朝晩の気温差",
                              "気温差に注意", "寒暖差に注意", "温度差に注意"]
            },
            {
                "concept": "雨注意",
                "expressions": ["雨が降りやすく", "急な雨に注意", "雨に注意", "雨具を持参",
                              "傘を持参", "傘が必要", "傘を忘れずに", "雨対策を"]
            },
            {
                "concept": "暑さ注意",
                "expressions": ["暑さに注意", "熱中症に注意", "暑さ対策", "暑さを避け",
                              "暑さが心配", "暑さに警戒", "熱中症対策", "暑さに備え"]
            },
            {
                "concept": "日差し注意",
                "expressions": ["日差しに注意", "紫外線対策", "UV対策", "日焼け対策",
                              "日差しが強い", "紫外線が強い", "日差しを避け"]
            }
        ]
        
        for pattern in repetitive_patterns:
            concept = pattern["concept"]
            expressions = pattern["expressions"]
            
            weather_expressions = [expr for expr in expressions if expr in weather_text]
            advice_expressions = [expr for expr in expressions if expr in advice_text]
            
            if weather_expressions and advice_expressions:
                logger.debug(f"同一概念の繰り返し検出 [{concept}]: 天気={weather_expressions}, アドバイス={advice_expressions}")
                return True
        
        return False

    @staticmethod
    def check_text_similarity(weather_text: str, advice_text: str) -> bool:
        """テキストの類似性をチェック（完全一致・ほぼ一致）"""
        # 完全一致
        if weather_text == advice_text:
            return True
            
        # ほぼ同じ内容の検出（語尾の微差を無視）
        weather_normalized = weather_text.replace("です", "").replace("だ", "").replace("である", "").replace("。", "").strip()
        advice_normalized = advice_text.replace("です", "").replace("だ", "").replace("である", "").replace("。", "").strip()
        
        if weather_normalized == advice_normalized:
            logger.debug(f"ほぼ完全一致検出: '{weather_text}' ≈ '{advice_text}'")
            return True
            
        # 句読点や助詞の差のみの場合も検出
        weather_core = PUNCTUATION_PATTERN.sub('', weather_text)
        advice_core = PUNCTUATION_PATTERN.sub('', advice_text)
        
        if weather_core == advice_core:
            logger.debug(f"句読点差のみ検出: '{weather_text}' ≈ '{advice_text}'")
            return True
        
        return False

    @staticmethod
    def check_keyword_duplication(weather_text: str, advice_text: str) -> bool:
        """重要キーワードの重複をチェック"""
        duplicate_keywords = [
            "にわか雨", "熱中症", "紫外線", "雷", "強風", "大雨", "猛暑", "酷暑",
            "注意", "警戒", "対策", "気をつけ", "備え", "準備",
            "傘",  # 傘関連の重複を防ぐ
            "気温差", "寒暖差", "温度差"  # 気温差関連の重複を防ぐ
        ]
        
        weather_keywords = []
        advice_keywords = []
        
        for keyword in duplicate_keywords:
            if keyword in weather_text:
                weather_keywords.append(keyword)
            if keyword in advice_text:
                advice_keywords.append(keyword)
        
        common_keywords = set(weather_keywords) & set(advice_keywords)
        if common_keywords:
            critical_duplicates = {"にわか雨", "熱中症", "紫外線", "雷", "強風", "大雨", "猛暑", "酷暑"}
            if any(keyword in critical_duplicates for keyword in common_keywords):
                logger.debug(f"重複キーワード検出: {common_keywords}")
                return True
        
        return False

    @staticmethod
    def check_semantic_contradiction(weather_text: str, advice_text: str) -> bool:
        """意味的矛盾パターンをチェック"""
        contradiction_patterns = [
            # 日差し・太陽関連の矛盾
            (["日差しの活用", "日差しを楽しん", "陽射しを活用", "太陽を楽しん", "日光浴", "日向"], 
             ["紫外線対策", "日焼け対策", "日差しに注意", "陽射しに注意", "UV対策", "日陰"]),
            # 外出関連の矛盾  
            (["外出推奨", "お出かけ日和", "散歩日和", "外出には絶好", "外で過ごそう"], 
             ["外出時は注意", "外出を控え", "屋内にいよう", "外出は危険"]),
            # 暑さ関連の矛盾
            (["暑さを楽しん", "夏を満喫", "暑いけど気持ち"], 
             ["暑さに注意", "熱中症対策", "暑さを避け"]),
            # 雨関連の矛盾
            (["雨を楽しん", "雨音が心地", "恵みの雨"], 
             ["雨に注意", "濡れないよう", "雨対策"])
        ]
        
        for positive_patterns, negative_patterns in contradiction_patterns:
            has_positive = any(pattern in weather_text for pattern in positive_patterns)
            has_negative = any(pattern in advice_text for pattern in negative_patterns)
            
            has_positive_advice = any(pattern in advice_text for pattern in positive_patterns)
            has_negative_weather = any(pattern in weather_text for pattern in negative_patterns)
            
            if (has_positive and has_negative) or (has_positive_advice and has_negative_weather):
                logger.debug(f"意味的矛盾検出: ポジティブ={positive_patterns}, ネガティブ={negative_patterns}")
                logger.debug(f"天気コメント: '{weather_text}', アドバイス: '{advice_text}'")
                return True
        
        return False

    @staticmethod
    def check_similar_expressions(weather_text: str, advice_text: str) -> bool:
        """類似表現パターンをチェック"""
        similarity_patterns = [
            (["雨が心配", "雨に注意"], ["雨", "注意"]),
            (["暑さが心配", "暑さに注意"], ["暑", "注意"]),
            (["風が強い", "風に注意"], ["風", "注意"]),
            (["紫外線が強い", "紫外線対策"], ["紫外線"]),
            (["雷が心配", "雷に注意"], ["雷", "注意"]),
            (["傘が必須", "傘を忘れずに", "傘をお忘れなく"], ["傘", "必要", "お守り", "安心"]),
            (["傘がお守り", "傘が安心"], ["傘", "必要", "必須", "忘れずに"]),
            (["気温差大", "寒暖差大", "朝昼の気温差", "朝晩と昼間の気温差"], 
             ["気温差", "寒暖差", "温度差", "朝晩", "昼間", "注意"]),
        ]
        
        for weather_patterns, advice_patterns in similarity_patterns:
            weather_match = any(pattern in weather_text for pattern in weather_patterns)
            advice_match = any(pattern in advice_text for pattern in advice_patterns)
            if weather_match and advice_match:
                logger.debug(f"類似表現検出: 天気パターン={weather_patterns}, アドバイスパターン={advice_patterns}")
                return True
        
        return False

    @staticmethod
    def check_umbrella_duplication(weather_text: str, advice_text: str) -> bool:
        """傘関連の重複を特別チェック"""
        umbrella_expressions = [
            "傘が必須", "傘がお守り", "傘を忘れずに", "傘をお忘れなく",
            "傘の準備", "傘が活躍", "折り畳み傘", "傘があると安心",
            "傘をお持ちください", "傘の携帯"
        ]
        
        weather_has_umbrella = any(expr in weather_text for expr in umbrella_expressions) or "傘" in weather_text
        advice_has_umbrella = any(expr in advice_text for expr in umbrella_expressions) or "傘" in advice_text
        
        if weather_has_umbrella and advice_has_umbrella:
            logger.debug(f"傘関連の重複候補検出: 天気='{weather_text}', アドバイス='{advice_text}'")
            
            similar_umbrella_meanings = [
                ["必須", "お守り", "必要", "忘れずに", "お忘れなく", "携帯", "準備", "活躍", "安心"],
            ]
            
            for meaning_group in similar_umbrella_meanings:
                weather_meanings = [m for m in meaning_group if m in weather_text]
                advice_meanings = [m for m in meaning_group if m in advice_text]
                
                if weather_meanings and advice_meanings:
                    logger.debug(f"傘関連の意味的重複検出: 天気側={weather_meanings}, アドバイス側={advice_meanings}")
                    return True
        
        return False

    @staticmethod
    def check_character_similarity(weather_text: str, advice_text: str, threshold: float = 0.7) -> bool:
        """短いテキストの文字列類似度をチェック"""
        if len(weather_text) <= 10 and len(advice_text) <= 10:
            min_length = min(len(weather_text), len(advice_text))
            if min_length == 0:
                return False
                
            max_length = max(len(weather_text), len(advice_text))
            if max_length / min_length > 2.0:
                return False
            
            common_chars = set(weather_text) & set(advice_text)
            similarity_ratio = len(common_chars) / max_length
            
            if similarity_ratio > threshold:
                logger.debug(f"高い文字列類似度検出: {similarity_ratio:.2f}")
                return True
        
        return False
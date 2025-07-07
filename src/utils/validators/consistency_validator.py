"""一貫性バリデータ - コメントペアの一貫性を検証"""

import logging
import re
from typing import Tuple, List

from src.config.weather_constants import (
    HEATSTROKE_WARNING_TEMP,
    COLD_WARNING_TEMP,
    SUNNY_WEATHER_KEYWORDS,
)
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)

# 正規表現パターンのプリコンパイル（パフォーマンス最適化）
PUNCTUATION_PATTERN = re.compile(r'[。、！？\s　]')


class ConsistencyValidator(BaseValidator):
    """天気コメントとアドバイスの一貫性を検証"""
    
    def __init__(self):
        super().__init__()
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """単一コメントの検証（ConsistencyValidatorでは実装しない）"""
        # ConsistencyValidatorはペアの一貫性をチェックするため、
        # 単一コメントの検証は常にTrueを返す
        return True, "単一コメントのチェックは他のバリデータで実施"
    
    def validate_comment_pair_consistency(
        self, 
        weather_comment: str, 
        advice_comment: str, 
        weather_data: WeatherForecast
    ) -> Tuple[bool, str]:
        """
        天気コメントとアドバイスの一貫性を包括的にチェック
        
        Returns:
            (is_consistent, reason): 一貫性チェック結果とその理由
        """
        # 1. 天気と現実の矛盾チェック
        weather_reality_check = self._check_weather_reality_contradiction(
            weather_comment, weather_data
        )
        if not weather_reality_check[0]:
            return weather_reality_check
        
        # 2. 温度と症状の矛盾チェック
        temp_symptom_check = self._check_temperature_symptom_contradiction(
            weather_comment, advice_comment, weather_data
        )
        if not temp_symptom_check[0]:
            return temp_symptom_check
        
        # 3. 重複・類似表現チェック
        duplication_check = self._check_content_duplication(
            weather_comment, advice_comment
        )
        if not duplication_check[0]:
            return duplication_check
        
        # 4. 矛盾する態度・トーンチェック
        tone_contradiction_check = self._check_tone_contradiction(
            weather_comment, advice_comment, weather_data
        )
        if not tone_contradiction_check[0]:
            return tone_contradiction_check
        
        # 5. 傘コメントの重複チェック
        umbrella_check = self._check_umbrella_redundancy(
            weather_comment, advice_comment
        )
        if not umbrella_check[0]:
            return umbrella_check
        
        return True, "コメントペアの一貫性OK"
    
    def _check_weather_reality_contradiction(
        self, 
        weather_comment: str, 
        weather_data: WeatherForecast
    ) -> Tuple[bool, str]:
        """天気の現実と表現の矛盾をチェック"""
        weather_desc = weather_data.weather_description.lower()
        temp = weather_data.temperature
        
        # 晴れまたは薄曇りなのに雲が優勢と言っている矛盾
        # 注: うすぐもり/薄曇りは曇りの一種として扱うため、SUNNY_WEATHER_KEYWORDSには含まれません
        # これにより、うすぐもり時には「雲が優勢」などの表現が許可されます
        if any(sunny_word in weather_desc for sunny_word in SUNNY_WEATHER_KEYWORDS):
            cloud_dominant_phrases = [
                "雲が優勢", "雲が多い", "雲に覆われ", "厚い雲", "雲がち",
                "どんより", "スッキリしない", "曇りがち"
            ]
            for phrase in cloud_dominant_phrases:
                if phrase in weather_comment:
                    return False, f"晴天時に雲優勢表現「{phrase}」は矛盾（天気: {weather_data.weather_description}）"

            rain_phrases = ["雨", "降雨", "雨が", "雨降り", "雨模様"]
            for phrase in rain_phrases:
                if phrase in weather_comment:
                    return False, f"晴天時に雨表現「{phrase}」は矛盾（天気: {weather_data.weather_description}）"
        
        # 9, 12, 15, 18時の矛盾パターンチェック
        hour = weather_data.datetime.hour
        if hour in [9, 12, 15, 18]:
            # 一般的にこれらの時間帯で特定の条件下では不適切な表現
            if hour in [9, 15, 18] and any(sunny in weather_desc for sunny in ["晴", "快晴"]):
                inappropriate_phrases = [
                    "日差しが厳しい", "強烈な日射", "灼熱の太陽", "猛烈な暑さ"
                ]
                for phrase in inappropriate_phrases:
                    if phrase in weather_comment and temp < 30:
                        return False, f"{hour}時・{temp}°C・晴天時に過度な暑さ表現「{phrase}」は不適切"
        
        return True, "天気現実チェックOK"
    
    def _check_temperature_symptom_contradiction(
        self, 
        weather_comment: str, 
        advice_comment: str, 
        weather_data: WeatherForecast
    ) -> Tuple[bool, str]:
        """温度と症状・対策の矛盾をチェック"""
        temp = weather_data.temperature
        
        # 34°C未満で熱中症対策を強く推奨する矛盾
        if temp < HEATSTROKE_WARNING_TEMP:
            excessive_heat_measures = [
                "熱中症対策必須", "熱中症に厳重注意", "熱中症の危険", "熱中症リスク高",
                "水分補給を頻繁に", "クーラー必須", "冷房を強めに", "氷で冷やして"
            ]
            for measure in excessive_heat_measures:
                if measure in advice_comment:
                    return False, f"{HEATSTROKE_WARNING_TEMP}°C未満（{temp}°C）で過度な熱中症対策「{measure}」は不適切"
        
        # 15°C以上で防寒対策を強く推奨する矛盾
        if temp >= COLD_WARNING_TEMP:
            excessive_cold_measures = [
                "厚着必須", "防寒対策必須", "暖房を強めに", "厚手のコートを",
                "マフラー必須", "手袋が必要", "暖かい飲み物を頻繁に"
            ]
            for measure in excessive_cold_measures:
                if measure in advice_comment:
                    return False, f"{COLD_WARNING_TEMP}°C以上（{temp}°C）で過度な防寒対策「{measure}」は不適切"
        
        return True, "温度症状チェックOK"
    
    def _check_content_duplication(
        self, 
        weather_comment: str, 
        advice_comment: str
    ) -> Tuple[bool, str]:
        """コンテンツの重複をより厳格にチェック"""
        # 既存の_is_duplicate_contentをベースに拡張
        if self._is_duplicate_content(weather_comment, advice_comment):
            return False, "重複コンテンツ検出"
        
        # 追加の特別なパターン
        special_duplication_patterns = [
            # 同じ動作を両方で推奨
            (["傘を持参", "傘の携帯", "傘を忘れずに"], ["傘を持参", "傘の携帯", "傘を忘れずに"]),
            (["水分補給", "水分摂取", "こまめに水分"], ["水分補給", "水分摂取", "こまめに水分"]),
            (["紫外線対策", "UV対策", "日焼け対策"], ["紫外線対策", "UV対策", "日焼け対策"]),
            # 同じ状況説明の重複
            (["雨が降りそう", "雨の予感", "降雨の可能性"], ["雨が降りそう", "雨の予感", "降雨の可能性"]),
            (["暑くなりそう", "気温上昇", "暖かくなる"], ["暑くなりそう", "気温上昇", "暖かくなる"]),
        ]
        
        for weather_patterns, advice_patterns in special_duplication_patterns:
            weather_match = any(pattern in weather_comment for pattern in weather_patterns)
            advice_match = any(pattern in advice_comment for pattern in advice_patterns)
            
            if weather_match and advice_match:
                return False, f"特別重複パターン検出: 天気パターン={weather_patterns}, アドバイス={advice_patterns}"
        
        return True, "重複チェックOK"
    
    def _check_tone_contradiction(
        self, 
        weather_comment: str, 
        advice_comment: str, 
        weather_data: WeatherForecast
    ) -> Tuple[bool, str]:
        """天気コメントとアドバイスのトーン・態度の矛盾をチェック"""
        # 空の状態と外出推奨の矛盾
        unstable_weather_phrases = [
            "空が不安定", "変わりやすい天気", "空模様が怪しい", "雲行きが怪しい",
            "お天気が心配", "天候が不安定", "空がすっきりしない"
        ]
        
        outing_encouragement_phrases = [
            "お出かけ日和", "外出推奨", "散歩日和", "ピクニック日和", 
            "外で過ごそう", "外出には絶好", "お出かけにぴったり",
            "外での活動を楽しん", "アウトドア日和"
        ]
        
        # 天気で不安定と言いながら、アドバイスで外出推奨
        weather_has_unstable = any(phrase in weather_comment for phrase in unstable_weather_phrases)
        advice_has_outing = any(phrase in advice_comment for phrase in outing_encouragement_phrases)
        
        if weather_has_unstable and advice_has_outing:
            return False, "不安定な空模様なのに外出推奨の矛盾"
        
        # 逆パターン: 天気で良好と言いながら、アドバイスで警戒
        stable_good_weather_phrases = [
            "穏やかな天気", "安定した晴天", "良好な天気", "快適な天候",
            "過ごしやすい", "心地よい天気", "気持ちいい天気"
        ]
        
        caution_advice_phrases = [
            "注意が必要", "気をつけて", "警戒して", "用心して",
            "慎重に", "避けた方が", "控えめに"
        ]
        
        weather_has_good = any(phrase in weather_comment for phrase in stable_good_weather_phrases)
        advice_has_caution = any(phrase in advice_comment for phrase in caution_advice_phrases)
        
        if weather_has_good and advice_has_caution:
            return False, "良好な天気なのに警戒アドバイスの矛盾"
        
        return True, "トーン一貫性OK"
    
    def _check_umbrella_redundancy(
        self, 
        weather_comment: str, 
        advice_comment: str
    ) -> Tuple[bool, str]:
        """傘関連表現の重複を特別にチェック"""
        # 傘関連キーワードの検出
        umbrella_keywords = ["傘", "雨具", "レインコート", "カッパ"]
        
        weather_has_umbrella = any(keyword in weather_comment for keyword in umbrella_keywords)
        advice_has_umbrella = any(keyword in advice_comment for keyword in umbrella_keywords)
        
        if not (weather_has_umbrella and advice_has_umbrella):
            return True, "傘の重複なし"
        
        # 傘関連の具体的な表現パターン
        umbrella_necessity_patterns = [
            "傘が必須", "傘が必要", "傘は必需品", "傘を忘れずに",
            "傘をお忘れなく", "傘の携帯", "傘を持参"
        ]
        
        umbrella_comfort_patterns = [
            "傘がお守り", "傘があると安心", "傘があれば安心", "傘がお役立ち",
            "傘が頼もしい", "傘がお供"
        ]
        
        # 同じカテゴリの表現が両方に含まれている場合は重複
        weather_necessity = any(pattern in weather_comment for pattern in umbrella_necessity_patterns)
        advice_necessity = any(pattern in advice_comment for pattern in umbrella_necessity_patterns)
        
        weather_comfort = any(pattern in weather_comment for pattern in umbrella_comfort_patterns)
        advice_comfort = any(pattern in advice_comment for pattern in umbrella_comfort_patterns)
        
        if weather_necessity and advice_necessity:
            return False, "傘の必要性を両方で強調（重複）"
        
        if weather_comfort and advice_comfort:
            return False, "傘の安心感を両方で表現（重複）"
        
        # 対立する表現のチェック（必須 vs お守り）
        if (weather_necessity and advice_comfort) or (weather_comfort and advice_necessity):
            # これは重複ではなく、補完的な関係なので許可
            return True, "傘表現は補完的"
        
        return True, "傘表現OK"
    
    def _is_duplicate_content(self, weather_text: str, advice_text: str) -> bool:
        """天気コメントとアドバイスの重複をチェック"""
        # 基本的な重複パターンをチェック
        
        # 1. 完全一致・ほぼ完全一致
        if weather_text == advice_text:
            return True
            
        # 1.5. ほぼ同じ内容の検出（語尾の微差を無視）
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
        
        # 2. 主要キーワードの重複チェック
        # 同じ重要キーワードが両方に含まれている場合は重複と判定
        duplicate_keywords = [
            "にわか雨", "熱中症", "紫外線", "雷", "強風", "大雨", "猛暑", "酷暑",
            "注意", "警戒", "対策", "気をつけ", "備え", "準備",
            "傘"  # 傘関連の重複を防ぐ
        ]
        
        weather_keywords = []
        advice_keywords = []
        
        for keyword in duplicate_keywords:
            if keyword in weather_text:
                weather_keywords.append(keyword)
            if keyword in advice_text:
                advice_keywords.append(keyword)
        
        # 3. 重要キーワードが重複している場合
        common_keywords = set(weather_keywords) & set(advice_keywords)
        if common_keywords:
            # 特に以下のキーワードは重複を強く示唆
            critical_duplicates = {"にわか雨", "熱中症", "紫外線", "雷", "強風", "大雨", "猛暑", "酷暑"}
            if any(keyword in critical_duplicates for keyword in common_keywords):
                logger.debug(f"重複キーワード検出: {common_keywords}")
                return True
        
        # 4. 意味的矛盾パターンのチェック（新機能）
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
            
            # 逆パターンもチェック
            has_positive_advice = any(pattern in advice_text for pattern in positive_patterns)
            has_negative_weather = any(pattern in weather_text for pattern in negative_patterns)
            
            if (has_positive and has_negative) or (has_positive_advice and has_negative_weather):
                logger.debug(f"意味的矛盾検出: ポジティブ={positive_patterns}, ネガティブ={negative_patterns}")
                logger.debug(f"天気コメント: '{weather_text}', アドバイス: '{advice_text}'")
                return True
        
        # 5. 類似表現のチェック
        similarity_patterns = [
            (["雨が心配", "雨に注意"], ["雨", "注意"]),
            (["暑さが心配", "暑さに注意"], ["暑", "注意"]),
            (["風が強い", "風に注意"], ["風", "注意"]),
            (["紫外線が強い", "紫外線対策"], ["紫外線"]),
            (["雷が心配", "雷に注意"], ["雷", "注意"]),
            # 傘関連の類似表現を追加
            (["傘が必須", "傘を忘れずに", "傘をお忘れなく"], ["傘", "必要", "お守り", "安心"]),
            (["傘がお守り", "傘が安心"], ["傘", "必要", "必須", "忘れずに"]),
        ]
        
        for weather_patterns, advice_patterns in similarity_patterns:
            weather_match = any(pattern in weather_text for pattern in weather_patterns)
            advice_match = any(pattern in advice_text for pattern in advice_patterns)
            if weather_match and advice_match:
                logger.debug(f"類似表現検出: 天気パターン={weather_patterns}, アドバイスパターン={advice_patterns}")
                return True
        
        # 6. 傘関連の特別チェック（より厳格な判定）
        umbrella_expressions = [
            "傘が必須", "傘がお守り", "傘を忘れずに", "傘をお忘れなく",
            "傘の準備", "傘が活躍", "折り畳み傘", "傘があると安心",
            "傘をお持ちください", "傘の携帯"
        ]
        
        # 両方のコメントに傘関連の表現が含まれている場合
        weather_has_umbrella = any(expr in weather_text for expr in umbrella_expressions) or "傘" in weather_text
        advice_has_umbrella = any(expr in advice_text for expr in umbrella_expressions) or "傘" in advice_text
        
        if weather_has_umbrella and advice_has_umbrella:
            # 傘という単語が両方に含まれていたら、より詳細にチェック
            logger.debug(f"傘関連の重複候補検出: 天気='{weather_text}', アドバイス='{advice_text}'")
            
            # 同じような意味の傘表現は重複とみなす
            similar_umbrella_meanings = [
                ["必須", "お守り", "必要", "忘れずに", "お忘れなく", "携帯", "準備", "活躍", "安心"],
            ]
            
            for meaning_group in similar_umbrella_meanings:
                weather_meanings = [m for m in meaning_group if m in weather_text]
                advice_meanings = [m for m in meaning_group if m in advice_text]
                
                # 同じ意味グループの単語が両方に含まれている場合は重複
                if weather_meanings and advice_meanings:
                    logger.debug(f"傘関連の意味的重複検出: 天気側={weather_meanings}, アドバイス側={advice_meanings}")
                    return True
        
        # 7. 文字列の類似度チェック（最適化版）
        # 短いコメントのみ対象とし、計算コストを削減
        if len(weather_text) <= 10 and len(advice_text) <= 10:
            # 最小長による早期判定
            min_length = min(len(weather_text), len(advice_text))
            if min_length == 0:
                return False
                
            # 長さ差が大きい場合は類似度が低いと判定
            max_length = max(len(weather_text), len(advice_text))
            if max_length / min_length > 2.0:  # 長さが2倍以上違う場合
                return False
            
            # 文字集合の重複計算（set演算は効率的）
            common_chars = set(weather_text) & set(advice_text)
            similarity_ratio = len(common_chars) / max_length
            
            if similarity_ratio > 0.7:
                logger.debug(f"高い文字列類似度検出: {similarity_ratio:.2f}")
                return True
        
        return False
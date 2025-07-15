"""一貫性バリデータ - コメントペアの一貫性を検証"""

import logging
from typing import Tuple, List

from src.config.config import get_weather_constants
from src.constants.validation_constants import SIMILARITY_THRESHOLD
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from src.utils.validators.duplication_checker import DuplicationChecker
from .base_validator import BaseValidator

# 定数を取得
_weather_const = get_weather_constants()
HEATSTROKE_WARNING_TEMP = _weather_const.HEATSTROKE_WARNING_TEMP
COLD_WARNING_TEMP = _weather_const.COLD_WARNING_TEMP
SUNNY_WEATHER_KEYWORDS = _weather_const.SUNNY_WEATHER_KEYWORDS

logger = logging.getLogger(__name__)


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
        
        # 6. 時間帯と温度の矛盾チェック
        time_temp_check = self._check_time_temperature_contradiction(
            weather_comment, advice_comment, weather_data
        )
        if not time_temp_check[0]:
            return time_temp_check
        
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
            # 気温差の重複表現
            (["気温差大", "気温差に注意", "寒暖差大", "寒暖差に注意", "温度差大"], 
             ["気温差に注意", "寒暖差に注意", "温度差に注意", "朝晩と昼間の気温差", "朝と夜の気温差"]),
            # 時間帯と気温の重複
            (["朝晩", "朝夜", "朝と夜", "朝晩の"], ["朝晩", "朝夜", "朝と夜", "朝晩の"]),
            (["昼間の暑さ", "日中の暑さ", "昼の暑さ"], ["昼間の暑さ", "日中の暑さ", "昼の暑さ"]),
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
    
    def _check_time_temperature_contradiction(
        self,
        weather_comment: str,
        advice_comment: str,
        weather_data: WeatherForecast
    ) -> Tuple[bool, str]:
        """時間帯に関する温度の矛盾をチェック"""
        combined_text = weather_comment + " " + advice_comment
        
        # 同一時間帯で矛盾する温度表現のパターン
        time_temp_contradictions = [
            # 昼間の矛盾
            {
                "time_words": ["昼間", "日中", "昼", "正午", "真昼"],
                "cold_words": ["涼しい", "肌寒い", "ひんやり", "冷える", "寒い"],
                "hot_words": ["蒸し暑い", "暑い", "猛暑", "厳しい暑さ", "灼熱"]
            },
            # 朝の矛盾
            {
                "time_words": ["朝", "早朝", "朝方", "明け方"],
                "cold_words": ["冷え込む", "寒い", "冷たい", "ひんやり"],
                "hot_words": ["蒸す", "暑い", "熱帯夜明け"]
            },
            # 夜の矛盾
            {
                "time_words": ["夜", "夜間", "深夜", "晩"],
                "cold_words": ["冷える", "寒い", "冷え込む"],
                "hot_words": ["熱帯夜", "寝苦しい", "蒸し暑い"]
            }
        ]
        
        # 各時間帯について矛盾をチェック
        for pattern in time_temp_contradictions:
            time_words = pattern["time_words"]
            cold_words = pattern["cold_words"]
            hot_words = pattern["hot_words"]
            
            # 同じ時間帯を指しているか確認
            has_time = any(word in combined_text for word in time_words)
            if not has_time:
                continue
                
            # 寒暖両方の表現があるか確認
            has_cold = any(word in combined_text for word in cold_words)
            has_hot = any(word in combined_text for word in hot_words)
            
            if has_cold and has_hot:
                time_word = next(word for word in time_words if word in combined_text)
                cold_word = next(word for word in cold_words if word in combined_text)
                hot_word = next(word for word in hot_words if word in combined_text)
                return False, f"同一時間帯（{time_word}）で温度の矛盾：「{cold_word}」と「{hot_word}」"
        
        # 一般的な温度矛盾（時間帯を明示しない場合）
        general_contradictions = [
            {
                "pattern1": ["涼しい", "涼やか", "爽やか", "さわやか", "過ごしやすい"],
                "pattern2": ["蒸し暑い", "ムシムシ", "じめじめ", "ジメジメ"]
            },
            {
                "pattern1": ["寒い", "冷える", "肌寒い"],
                "pattern2": ["暑い", "猛暑", "酷暑", "熱い"]
            }
        ]
        
        for contradiction in general_contradictions:
            has_pattern1 = any(word in combined_text for word in contradiction["pattern1"])
            has_pattern2 = any(word in combined_text for word in contradiction["pattern2"])
            
            if has_pattern1 and has_pattern2:
                word1 = next(word for word in contradiction["pattern1"] if word in combined_text)
                word2 = next(word for word in contradiction["pattern2"] if word in combined_text)
                return False, f"温度感覚の矛盾：「{word1}」と「{word2}」が同時に存在"
        
        return True, "時間帯温度チェックOK"
    
    def _check_repetitive_concepts(self, weather_text: str, advice_text: str) -> bool:
        """同じ概念の繰り返しをチェック"""
        return DuplicationChecker.check_repetitive_concepts(weather_text, advice_text)

    def _check_text_similarity(self, weather_text: str, advice_text: str) -> bool:
        """テキストの類似性をチェック（完全一致・ほぼ一致）"""
        return DuplicationChecker.check_text_similarity(weather_text, advice_text)

    def _check_keyword_duplication(self, weather_text: str, advice_text: str) -> bool:
        """重要キーワードの重複をチェック"""
        return DuplicationChecker.check_keyword_duplication(weather_text, advice_text)

    def _check_semantic_contradiction(self, weather_text: str, advice_text: str) -> bool:
        """意味的矛盾パターンをチェック"""
        return DuplicationChecker.check_semantic_contradiction(weather_text, advice_text)

    def _check_similar_expressions(self, weather_text: str, advice_text: str) -> bool:
        """類似表現パターンをチェック"""
        return DuplicationChecker.check_similar_expressions(weather_text, advice_text)

    def _check_umbrella_duplication(self, weather_text: str, advice_text: str) -> bool:
        """傘関連の重複を特別チェック"""
        return DuplicationChecker.check_umbrella_duplication(weather_text, advice_text)

    def _check_character_similarity(self, weather_text: str, advice_text: str) -> bool:
        """短いテキストの文字列類似度をチェック"""
        return DuplicationChecker.check_character_similarity(weather_text, advice_text, SIMILARITY_THRESHOLD)

    def _is_duplicate_content(self, weather_text: str, advice_text: str) -> bool:
        """天気コメントとアドバイスの重複をチェック"""
        # 各チェック関数を順番に呼び出す
        if self._check_repetitive_concepts(weather_text, advice_text):
            return True
            
        if self._check_text_similarity(weather_text, advice_text):
            return True
            
        if self._check_keyword_duplication(weather_text, advice_text):
            return True
            
        if self._check_semantic_contradiction(weather_text, advice_text):
            return True
            
        if self._check_similar_expressions(weather_text, advice_text):
            return True
            
        if self._check_umbrella_duplication(weather_text, advice_text):
            return True
            
        if self._check_character_similarity(weather_text, advice_text):
            return True
        
        return False
"""天気コメント検証システム - 天気条件に不適切なコメントを検出・除外"""

import logging
from typing import List, Dict, Any, Tuple, Optional

from src.config.weather_constants import (
    HEATSTROKE_WARNING_TEMP,
    HEATSTROKE_SEVERE_TEMP,
    COLD_WARNING_TEMP,
)

SUNNY_WEATHER_KEYWORDS = ["晴", "快晴", "晴天", "薄曇", "うすぐもり", "薄ぐもり"]
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.past_comment import PastComment, CommentType

logger = logging.getLogger(__name__)


class WeatherCommentValidator:
    """天気条件に基づいてコメントの適切性を検証"""
    
    def __init__(self):
        # 天気別禁止ワードの定義
        self.weather_forbidden_words = {
            # 雨天時（全レベル）
            "rain": {
                "weather_comment": [
                    "青空", "晴れ", "快晴", "日差し", "太陽", "陽射し", "眩しい",
                    "穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "のどか",
                    "お出かけ日和", "散歩日和", "ピクニック", "外出推奨",
                    "スッキリ", "気持ちいい", "清々しい",
                    # 雨天時に矛盾する表現を追加
                    "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み",
                    "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下"
                ],
                "advice": [
                    "日焼け止め", "帽子", "サングラス", "日傘", "紫外線",
                    "お出かけ", "外出", "散歩", "ピクニック", "日光浴",
                    "過ごしやすい", "快適", "心地良い", "爽やか",
                    # 雨天時の生活関連アドバイスを追加
                    "洗濯物を外に", "布団を干す", "外干しを", "窓を開けて", "ベランダ作業"
                ]
            },
            # 大雨・豪雨・嵐
            "heavy_rain": {
                "weather_comment": [
                    # 雨天時の禁止ワード全て
                    "青空", "晴れ", "快晴", "日差し", "太陽", "陽射し", "眩しい",
                    "穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "のどか",
                    "お出かけ日和", "散歩日和", "ピクニック", "外出推奨",
                    "スッキリ", "気持ちいい", "清々しい",
                    # 軽微な表現（大雨時は特に禁止）
                    "にわか雨", "ニワカ雨", "変わりやすい", "スッキリしない",
                    "蒸し暑い", "厳しい暑さ", "体感", "心地",
                    "雲の多い", "どんより", "じめじめ", "湿っぽい",
                    # 大雨時に特に不適切な表現を追加
                    "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み",
                    "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下"
                ],
                "advice": [
                    # 基本的な外出系
                    "日焼け止め", "帽子", "サングラス", "日傘", "紫外線",
                    "お出かけ", "外出", "散歩", "ピクニック", "日光浴",
                    "過ごしやすい", "快適", "心地良い", "爽やか",
                    # 軽い対策（大雨時は不適切）
                    "折り畳み傘", "軽い雨具", "短時間の外出"
                ]
            },
            # 晴天時
            "sunny": {
                "weather_comment": [
                    "雨", "じめじめ", "湿った", "どんより", "曇り", "雲が厚い",
                    "傘", "雨具", "濡れ", "湿気", "降水",
                    # 晴天時に不適切な空の状態表現を追加
                    "スッキリしない", "すっきりしない", "はっきりしない", "ぼんやり",
                    "もやもや", "重い空", "厚い雲", "灰色の空",  # 重複「どんより」を削除
                    "曇りがち", "雲多め", "変わりやすい天気", "不安定",
                    # 安定した晴れ天気に不適切な表現を追加
                    "変わりやすい空", "変わりやすい", "気まぐれ", "移ろいやすい",
                    "一定しない", "変化しやすい", "変動", "不規則"
                ],
                "advice": [
                    "傘", "レインコート", "濡れ", "雨具", "長靴"
                ]
            },
            # 曇天時
            "cloudy": {
                "weather_comment": [
                    "青空", "快晴", "眩しい", "強い日差し", "ギラギラ",
                    # 雨天時の生活関連表現を追加
                    "洗濯日和", "布団干し日和", "外干し", "窓を開けて", "ベランダで"
                ],
                "advice": [
                    "強い日差し対策", "紫外線対策必須"
                ]
            }
        }
        
        # 温度別禁止ワード（詳細な温度範囲に基づく）
        self.temperature_forbidden_words = {
            "moderate_warm": {  # 25-33°C（中程度の暖かさ）
                "forbidden": [
                    "寒い", "冷える", "肌寒い", "防寒", "厚着",
                    # 25°C以上で「涼しい」は不適切
                    "涼しい", "涼やか", "爽やか", "ひんやり", "冷たい",
                    # 31°Cで「厳しい暑さ」は過大
                    "厳しい暑さ", "酷暑", "激しい暑さ", "耐え難い暑さ",
                    "猛烈な暑さ", "危険な暑さ"
                ]
            },
            "very_hot": {  # 34°C以上（猛暑日）
                "forbidden": [
                    "寒い", "冷える", "肌寒い", "防寒", "暖かく", "厚着",
                    "涼しい", "涼やか", "爽やか", "ひんやり", "冷たい",
                    "過ごしやすい", "快適", "心地良い"
                ]
            },
            "extreme_hot": {  # 37°C以上（危険な暑さ）
                "forbidden": [
                    "寒い", "冷える", "肌寒い", "防寒", "暖かく", "厚着",
                    "涼しい", "涼やか", "爽やか", "ひんやり", "冷たい",
                    "過ごしやすい", "快適", "心地良い", "穏やか"
                ]
            },
            "cold": {  # 12°C未満
                "forbidden": [
                    "暑い", "猛暑", "酷暑", "熱中症", "クーラー", "冷房",
                    "厳しい暑さ", "激しい暑さ", "蒸し暑い", "汗ばむ"
                ]
            },
            "mild": {  # 12-25°C（快適域）
                "forbidden": [
                    "極寒", "凍える", "猛暑", "酷暑", 
                    "厳しい暑さ", "激しい暑さ", "耐え難い暑さ"
                ]
            }
        }
        
        # 必須キーワード（悪天候時）
        self.required_keywords = {
            "heavy_rain": {
                "weather_comment": ["注意", "警戒", "危険", "荒れ", "激しい", "強い", "本格的"],
                "advice": ["傘", "雨具", "安全", "注意", "室内", "控え", "警戒", "備え", "準備"]
            },
            "storm": {
                "weather_comment": ["嵐", "暴風", "警戒", "危険", "荒天", "大荒れ"],
                "advice": ["危険", "外出控え", "安全確保", "警戒", "室内", "備え", "準備"]
            }
        }
    
    def validate_comment(self, comment: PastComment, weather_data: WeatherForecast, 
                        state: Optional[Any] = None) -> Tuple[bool, str]:
        """
        コメントが天気条件に適しているか検証
        
        Returns:
            (is_valid, reason): 検証結果とその理由
        """
        comment_text = comment.comment_text
        comment_type = comment.comment_type.value
        
        # 0. 雨予報時の事前チェック（最優先）
        if state and hasattr(state, 'generation_metadata') and state.generation_metadata:
            period_forecasts = state.generation_metadata.get('period_forecasts', [])
            for forecast in period_forecasts:
                if forecast.precipitation > 0:
                    rain_forbidden_words = ["穏やか", "のどか", "快適", "過ごしやすい"]
                    for word in rain_forbidden_words:
                        if word in comment_text:
                            return False, f"雨予報時（{forecast.datetime.strftime('%H時')}）の禁止ワード「{word}」を含む"
        
        # 1. 天気条件チェック
        weather_check = self._check_weather_conditions(comment_text, comment_type, weather_data)
        if not weather_check[0]:
            return weather_check
        
        # 2. 温度条件チェック
        temp_check = self._check_temperature_conditions(comment_text, weather_data)
        if not temp_check[0]:
            return temp_check
        
        # 2.5. 地域特性チェック（位置情報がある場合）
        if hasattr(weather_data, 'location') and weather_data.location:
            regional_check = self._check_regional_specifics(comment_text, weather_data.location)
            if not regional_check[0]:
                return regional_check
        
        # 3. 湿度条件チェック
        humidity_check = self._check_humidity_conditions(comment_text, weather_data)
        if not humidity_check[0]:
            return humidity_check
        
        # 4. 必須キーワードチェック（悪天候時）
        required_check = self._check_required_keywords(comment_text, comment_type, weather_data)
        if not required_check[0]:
            return required_check
        
        # 5. 雨天時の矛盾表現チェック
        contradiction_check = self._check_rainy_weather_contradictions(comment_text, weather_data)
        if not contradiction_check[0]:
            return contradiction_check
        
        return True, "OK"
    
    def _check_weather_conditions(self, comment_text: str, comment_type: str, 
                                 weather_data: WeatherForecast) -> Tuple[bool, str]:
        """天気条件に基づく検証"""
        weather_desc = weather_data.weather_description.lower()
        comment_lower = comment_text.lower()
        precipitation = weather_data.precipitation
        
        # 降水量レベルを取得
        precipitation_severity = weather_data.get_precipitation_severity()
        
        # 大雨・嵐チェック
        if any(severe in weather_desc for severe in ["大雨", "豪雨", "嵐", "暴風", "台風"]):
            forbidden_words = self.weather_forbidden_words["heavy_rain"][comment_type]
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"悪天候時の禁止ワード「{word}」を含む"
        
        # 雷の特別チェック（降水量を考慮）
        elif "雷" in weather_desc:
            # 設定ファイルから雷の降水量閾値を取得
            try:
                from src.config.config_loader import load_config
                config = load_config('weather_thresholds', validate=False)
                thunder_threshold = config.get('precipitation', {}).get('thunder_severe_threshold', 5.0)
            except (FileNotFoundError, KeyError, ValueError) as e:
                logger.warning(f"Failed to load thunder threshold: {e}")
                thunder_threshold = 5.0  # デフォルト値：気象庁の「やや強い雨」基準
            
            if precipitation >= thunder_threshold:
                # 強い雷（設定された閾値以上）- 気象庁基準でやや強い雨レベル
                forbidden_words = self.weather_forbidden_words["heavy_rain"][comment_type]
                for word in forbidden_words:
                    if word in comment_text:
                        return False, f"強い雷雨時の禁止ワード「{word}」を含む"
            else:
                # 軽微な雷（閾値未満）
                if comment_type == "weather_comment":
                    # 軽微な雷では強い警戒表現を禁止
                    strong_warning_words = ["激しい", "警戒", "危険", "大荒れ", "本格的", "強雨"]
                    for word in strong_warning_words:
                        if word in comment_text:
                            return False, f"軽微な雷（{precipitation}mm）で過度な警戒表現「{word}」を含む"
                elif comment_type == "advice":
                    # 軽微な雷では強い警戒アドバイスを禁止
                    strong_warning_advice = ["避難", "危険", "中止", "延期", "控える"]
                    for word in strong_warning_advice:
                        if word in comment_text:
                            return False, f"軽微な雷（{precipitation}mm）で過度な警戒アドバイス「{word}」を含む"
        
        # 通常の雨チェック（降水量レベルで判定）
        elif any(rain in weather_desc for rain in ["雨", "rain"]):
            if precipitation_severity in ["heavy", "very_heavy"]:
                # 大雨・激しい雨
                forbidden_words = self.weather_forbidden_words["heavy_rain"][comment_type]
            else:
                # 軽い雨～中程度の雨
                forbidden_words = self.weather_forbidden_words["rain"][comment_type]
            
            for word in forbidden_words:
                if word in comment_text:
                    severity_desc = "大雨" if precipitation_severity in ["heavy", "very_heavy"] else "雨天"
                    return False, f"{severity_desc}時の禁止ワード「{word}」を含む"
            
            # 軽い雨では強い警戒表現を禁止
            if precipitation_severity == "light" and comment_type == "weather_comment":
                strong_warning_words = ["激しい", "警戒", "危険", "大荒れ", "本格的", "強雨"]
                for word in strong_warning_words:
                    if word in comment_text:
                        return False, f"軽い雨（{precipitation}mm）で過度な警戒表現「{word}」を含む"
        
        # 晴天チェック（厳密な判定 - 強化版）
        elif any(sunny in weather_desc for sunny in ["晴", "快晴", "猛暑", "晴天"]):
            forbidden_words = self.weather_forbidden_words["sunny"][comment_type]
            for word in forbidden_words:
                if word in comment_text:
                    logger.info(f"晴天時禁止ワード除外: '{comment_text}' - 理由: 晴天時の禁止ワード「{word}」を含む")
                    return False, f"晴天時の禁止ワード「{word}」を含む"
            
            # 晴れ・快晴時の特別な「変わりやすい」表現チェック（強化）
            changeable_patterns = [
                "変わりやすい空", "変わりやすい天気", "変わりやすい", "変化しやすい空",
                "移ろいやすい空", "気まぐれな空", "一定しない空", "不安定な空模様"
            ]
            for pattern in changeable_patterns:
                if pattern in comment_text:
                    logger.info(f"晴天時に不適切な表現を強制除外: '{comment_text}' - 「{pattern}」は晴れ・快晴に不適切")
                    return False, f"晴天時に不適切な表現「{pattern}」を含む（晴れ・快晴時は安定した天気）"
        
        # 曇天チェック（晴天でない場合のみ）
        elif "曇" in weather_desc or "くもり" in weather_desc:
            forbidden_words = self.weather_forbidden_words["cloudy"][comment_type]
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"曇天時の禁止ワード「{word}」を含む"
            
            # 曇天時でも「天気急変」「変わりやすい」系の表現をチェック
            # 全ての天気が曇りで安定している場合は不適切
            if self._is_stable_cloudy_weather(weather_data):
                weather_change_expressions = [
                    "天気急変", "急変", "天気が急に", "急に変わる",
                    "変わりやすい天気", "不安定な空模様", "変化しやすい",
                    "天候不安定", "激しい変化", "急激な変化"
                ]
                for expr in weather_change_expressions:
                    if expr in comment_text:
                        logger.info(f"安定した曇天時に不適切な表現を除外: '{comment_text}' - 「{expr}」は不適切")
                        return False, f"安定した曇天時に不適切な急変表現「{expr}」を含む"
            
            # 曇天時のみ「スッキリしない」を許可
            logger.debug(f"曇天時コメント許可: '{comment_text}'")
        
        # その他の天気（明確でない場合）
        else:
            # 「スッキリしない」は曇天時のみ許可
            if "スッキリしない" in comment_text and not any(cloudy in weather_desc for cloudy in ["曇", "くもり"]):
                return False, f"不明確な天気時の禁止ワード「スッキリしない」を含む"
        
        return True, "天気条件OK"
    
    def _check_temperature_conditions(self, comment_text: str, 
                                    weather_data: WeatherForecast) -> Tuple[bool, str]:
        """温度条件に基づく検証（詳細な温度範囲）"""
        temp = weather_data.temperature
        
        # 詳細な温度範囲による分類
        if temp >= 37:
            forbidden = self.temperature_forbidden_words["extreme_hot"]["forbidden"]
            temp_category = "危険な暑さ"
        elif temp >= HEATSTROKE_WARNING_TEMP:  # 34°C以上
            forbidden = self.temperature_forbidden_words["very_hot"]["forbidden"]
            temp_category = "猛暑日"
        elif temp >= 25:
            forbidden = self.temperature_forbidden_words["moderate_warm"]["forbidden"]
            temp_category = "中程度の暖かさ"
            # 34°C未満で熱中症は控えめに
            if temp < HEATSTROKE_WARNING_TEMP and "熱中症" in comment_text:
                logger.info(
                    f"温度不適切表現除外: '{comment_text}' - 理由: {temp}°C（{HEATSTROKE_WARNING_TEMP}°C未満）で「熱中症」表現は過大"
                )
                return False, f"温度{temp}°C（{HEATSTROKE_WARNING_TEMP}°C未満）で「熱中症」表現は過大"
        elif temp < 12:
            forbidden = self.temperature_forbidden_words["cold"]["forbidden"]
            temp_category = "寒い"
        else:
            forbidden = self.temperature_forbidden_words["mild"]["forbidden"]
            temp_category = "快適域"
        
        for word in forbidden:
            if word in comment_text:
                logger.info(f"温度不適切表現除外: '{comment_text}' - 理由: {temp}°C（{temp_category}）で禁止ワード「{word}」を含む")
                return False, f"温度{temp}°C（{temp_category}）で禁止ワード「{word}」を含む"
        
        return True, "温度条件OK"
    
    def _check_humidity_conditions(self, comment_text: str, 
                                  weather_data: WeatherForecast) -> Tuple[bool, str]:
        """湿度条件に基づく検証"""
        humidity = weather_data.humidity
        
        # 高湿度時（80%以上）の乾燥関連コメントを除外
        if humidity >= 80:
            dry_words = ["乾燥注意", "乾燥対策", "乾燥しやすい", "乾燥した空気", 
                        "からっと", "さっぱり", "湿度低下"]
            for word in dry_words:
                if word in comment_text:
                    return False, f"高湿度（{humidity}%）で乾燥関連表現「{word}」を含む"
        
        # 低湿度時（30%未満）の除湿関連コメントを除外
        if humidity < 30:
            humid_words = ["除湿対策", "除湿", "ジメジメ", "湿気対策", "湿っぽい"]
            for word in humid_words:
                if word in comment_text:
                    return False, f"低湿度（{humidity}%）で除湿関連表現「{word}」を含む"
        
        return True, "湿度条件OK"
    
    def _check_required_keywords(self, comment_text: str, comment_type: str,
                                weather_data: WeatherForecast) -> Tuple[bool, str]:
        """必須キーワードチェック（悪天候時）"""
        weather_desc = weather_data.weather_description.lower()
        
        # 大雨・豪雨時
        if any(heavy in weather_desc for heavy in ["大雨", "豪雨"]):
            if comment_type in self.required_keywords["heavy_rain"]:
                required = self.required_keywords["heavy_rain"][comment_type]
                if not any(keyword in comment_text for keyword in required):
                    return False, f"大雨時の必須キーワード不足（{', '.join(required)}のいずれか必要）"
        
        # 嵐・暴風時
        elif any(storm in weather_desc for storm in ["嵐", "暴風", "台風"]):
            if comment_type in self.required_keywords["storm"]:
                required = self.required_keywords["storm"][comment_type]
                if not any(keyword in comment_text for keyword in required):
                    return False, f"嵐時の必須キーワード不足（{', '.join(required)}のいずれか必要）"
        
        return True, "必須キーワードOK"
    
    def _check_rainy_weather_contradictions(self, comment_text: str, 
                                          weather_data: WeatherForecast) -> Tuple[bool, str]:
        """雨天時の矛盾表現を特別にチェック"""
        weather_desc = weather_data.weather_description.lower()
        
        # 雨天チェック
        if any(rain_word in weather_desc for rain_word in ["雨", "小雨", "中雨", "大雨", "豪雨"]):
            # 雨天時に矛盾する表現のリスト
            contradictory_phrases = [
                "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み", 
                "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下",
                "晴天", "好天", "快晴の", "青空が"
            ]
            
            for phrase in contradictory_phrases:
                if phrase in comment_text:
                    return False, f"雨天時の矛盾表現「{phrase}」を含む（天気：{weather_data.weather_description}）"
        
        return True, "矛盾表現チェックOK"
    
    def _check_regional_specifics(self, comment_text: str, location: str) -> Tuple[bool, str]:
        """地域特性に基づく検証（改善版）"""
        # 地域判定の改善：都道府県と市町村の適切な判定
        location_lower = location.lower()
        
        # 沖縄県関連の判定（県名・市町村名を包括）
        okinawa_keywords = ["沖縄", "那覇", "石垣", "宮古", "名護", "うるま", "沖縄市", "浦添", "糸満", "豊見城", "南城"]
        is_okinawa = any(keyword in location_lower for keyword in okinawa_keywords)
        
        if is_okinawa:
            # 雪関連のコメントを除外
            snow_words = ["雪", "雪景色", "粉雪", "新雪", "雪かき", "雪道", "雪が降る", "雪化粧", "雪だるま"]
            for word in snow_words:
                if word in comment_text:
                    return False, f"沖縄地域で雪関連表現「{word}」は不適切"
            
            # 低温警告の閾値を緩和（沖縄は寒くならない）
            strong_cold_words = ["極寒", "凍える", "凍結", "防寒対策必須", "暖房必須", "厚着必要"]
            for word in strong_cold_words:
                if word in comment_text:
                    return False, f"沖縄地域で強い寒さ表現「{word}」は不適切"
        
        # 北海道関連の判定（道名・主要都市名を包括）
        hokkaido_keywords = ["北海道", "札幌", "函館", "旭川", "釧路", "帯広", "北見", "小樽", "室蘭", "苫小牧"]
        is_hokkaido = any(keyword in location_lower for keyword in hokkaido_keywords)
        
        if is_hokkaido:
            # 高温警告の閾値を上げ（北海道は暑くなりにくい）
            strong_heat_words = ["酷暑", "猛暑", "危険な暑さ", "熱帯夜", "猛烈な暑さ"]
            for word in strong_heat_words:
                if word in comment_text:
                    return False, f"北海道地域で強い暑さ表現「{word}」は不適切"
        
        # その他の地域特性チェック（今後拡張可能）
        # 山間部・海岸部などの特性も将来的に追加可能
        
        return True, "地域特性OK"
    
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
        
        # 熱中症チェックは_check_temperature_conditionsで行うため、ここでは削除
        
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
        import re
        weather_core = re.sub(r'[。、！？\s　]', '', weather_text)
        advice_core = re.sub(r'[。、！？\s　]', '', advice_text)
        
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
    
    def filter_comments(self, comments: List[PastComment], 
                       weather_data: WeatherForecast,
                       state: Optional[Any] = None) -> List[PastComment]:
        """
        コメントリストから不適切なものを除外
        
        Returns:
            適切なコメントのみのリスト
        """
        valid_comments = []
        
        # stateから全時間帯の予報データを取得して雨予報を確認
        has_rain_forecast = False
        if state and hasattr(state, 'generation_metadata') and state.generation_metadata:
            period_forecasts = state.generation_metadata.get('period_forecasts', [])
            logger.info(f"🌧️ 降水予報チェック: {len(period_forecasts)}件の予報データ")
            for forecast in period_forecasts:
                if forecast.precipitation > 0:
                    has_rain_forecast = True
                    logger.info(f"🌧️ 雨予報検出: {forecast.datetime.strftime('%H時')} - {forecast.precipitation}mm")
                    break
        else:
            logger.warning(f"🌧️ stateまたはperiod_forecastsが利用できません: state={state is not None}, has_metadata={hasattr(state, 'generation_metadata') if state else False}")
        
        for comment in comments:
            is_valid, reason = self.validate_comment(comment, weather_data, state)
            
            # 追加の雨予報チェック
            if is_valid and has_rain_forecast:
                rain_forbidden_words = [
                    "穏やか", "のどか", "快適", "過ごしやすい", "心地良い",
                    "晴れ", "青空", "日差し", "太陽", "陽射し",
                    "お出かけ日和", "散歩日和"
                ]
                for word in rain_forbidden_words:
                    if word in comment.comment_text:
                        is_valid = False
                        reason = f"雨予報時の禁止ワード「{word}」を含む"
                        logger.info(f"🌧️ 雨予報時禁止: '{comment.comment_text}' - 禁止ワード「{word}」")
                        break
            
            if is_valid:
                valid_comments.append(comment)
            else:
                logger.info(f"コメント除外: '{comment.comment_text}' - 理由: {reason}")
        
        # 有効なコメントが少なすぎる場合の警告
        if len(valid_comments) < len(comments) * 0.1:  # 90%以上除外された場合
            logger.warning(f"大量のコメントが除外されました: {len(comments)}件中{len(valid_comments)}件のみ有効")
        
        return valid_comments
    
    def get_weather_appropriate_comments(self, comments: List[PastComment],
                                       weather_data: WeatherForecast,
                                       comment_type: CommentType,
                                       limit: int = 30,
                                       state: Optional[Any] = None) -> List[PastComment]:
        """
        天気に最も適したコメントを優先順位付けして取得
        
        Returns:
            優先順位付けされたコメントリスト（最大limit件）
        """
        # まず不適切なコメントを除外（stateも渡す）
        valid_comments = self.filter_comments(comments, weather_data, state)
        
        # スコアリング
        scored_comments = []
        for comment in valid_comments:
            score = self._calculate_appropriateness_score(comment, weather_data)
            scored_comments.append((score, comment))
        
        # スコア順にソート
        scored_comments.sort(key=lambda x: x[0], reverse=True)
        
        # 上位limit件を返す
        return [comment for _, comment in scored_comments[:limit]]
    
    def _calculate_appropriateness_score(self, comment: PastComment, 
                                       weather_data: WeatherForecast) -> float:
        """コメントの適切性スコアを計算"""
        score = 100.0  # 基本スコア
        comment_text = comment.comment_text
        weather_desc = weather_data.weather_description.lower()
        
        # 悪天候時のスコアリング
        if any(severe in weather_desc for severe in ["大雨", "豪雨", "嵐", "暴風"]):
            # 強い警戒表現にボーナス
            strong_warning_words = ["警戒", "危険", "激しい", "本格的", "荒れ", "大荒れ"]
            for word in strong_warning_words:
                if word in comment_text:
                    score += 20.0
            
            # 軽い表現にペナルティ
            mild_words = ["にわか雨", "変わりやすい", "スッキリしない", "どんより"]
            for word in mild_words:
                if word in comment_text:
                    score -= 30.0
        
        # 季節との一致度
        if 'season' in comment.raw_data:
            current_month = weather_data.datetime.month
            expected_season = self._get_season_from_month(current_month)
            if comment.raw_data['season'] == expected_season:
                score += 10.0
        
        # 使用回数によるスコア（人気度）
        if 'count' in comment.raw_data:
            count = comment.raw_data['count']
            score += min(count / 1000, 10.0)  # 最大10点のボーナス
        
        # 高温時（35度以上）のスコアリング
        if weather_data.temperature >= 35.0:
            heat_keywords = ["熱中症", "水分補給", "涼しい", "冷房", "暑さ対策", "猛暑", "高温", "酷暑"]
            for keyword in heat_keywords:
                if keyword in comment_text:
                    score += 30.0  # 高温時は大幅にスコアを上げる
                    break  # 複数マッチしても加算は1回のみ
            
            # 高温時に不適切な表現にペナルティ
            cold_keywords = ["肌寒い", "冷える", "防寒", "暖房", "あたたか"]
            for keyword in cold_keywords:
                if keyword in comment_text:
                    score -= 40.0
                    break
        
        # 雨天時のスコアリング強化
        if weather_data.precipitation > 0:
            rain_keywords = ["雨", "傘", "濡れ", "降水", "にわか雨", "雷雨", "レインコート"]
            for keyword in rain_keywords:
                if keyword in comment_text:
                    score += 25.0  # 雨天時はスコアを上げる
                    break
            
            # 雨天時に不適切な表現にペナルティ
            sunny_keywords = ["快晴", "日差し", "紫外線", "カラッと"]
            for keyword in sunny_keywords:
                if keyword in comment_text:
                    score -= 35.0
                    break
        
        return score
    
    def _get_season_from_month(self, month: int) -> str:
        """月から季節を判定"""
        if month in [3, 4, 5]:
            return "春"
        elif month == 6:
            return "梅雨"
        elif month in [7, 8]:
            return "夏"
        elif month == 9:
            return "台風"
        elif month in [10, 11]:
            return "秋"
        else:  # 12, 1, 2
            return "冬"
    
    def _is_stable_cloudy_weather(self, weather_data: WeatherForecast) -> bool:
        """安定した曇天かどうかを判定（翌日の1日分のデータを考慮）"""
        # 現在の天気が曇りでない場合はFalse
        weather_desc = weather_data.weather_description.lower()
        if not any(cloudy in weather_desc for cloudy in ["曇", "くもり"]):
            return False
        
        # 設定ファイルから闾値を取得
        try:
            from src.config.config_loader import load_config
            config = load_config('weather_thresholds', validate=False)
            stability_config = config.get('weather_stability', {})
            precipitation_threshold = stability_config.get('cloudy_precipitation_threshold', 1.0)
            wind_threshold = stability_config.get('cloudy_wind_threshold', 5.0)
        except (FileNotFoundError, KeyError, ValueError) as e:
            logger.debug(f"Failed to load stability thresholds: {e}")
            # デフォルト値を使用
            precipitation_threshold = 1.0  # 1mm/h
            wind_threshold = 5.0  # 5m/s
        
        # 降水量が多い場合は不安定と判定
        if weather_data.precipitation > precipitation_threshold:
            return False
        
        # 風速が強い場合は不安定と判定
        if weather_data.wind_speed > wind_threshold:
            return False
        
        # 雷を含む場合は不安定と判定
        if "雷" in weather_desc or "thunder" in weather_desc.lower():
            return False
        
        # 霧を含む場合も変化の可能性があるため不安定と判定
        if "霧" in weather_desc or "fog" in weather_desc.lower():
            return False
        
        # 上記の条件をクリアした場合は安定した曇天と判定
        return True

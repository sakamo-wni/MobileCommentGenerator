"""コメントバリデーションロジック"""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple, List

from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.utils.common_utils import SEVERE_WEATHER_PATTERNS, FORBIDDEN_PHRASES

logger = logging.getLogger(__name__)


class CommentValidator:
    """コメントバリデーションクラス"""
    
    def __init__(self, validator: WeatherCommentValidator, severe_config):
        self.validator = validator
        self.severe_config = severe_config
    
    def validate_comment_pair(
        self, 
        weather_comment: PastComment, 
        advice_comment: PastComment, 
        weather_data: WeatherForecast
    ) -> bool:
        """コメントペアの最終バリデーション（包括的一貫性チェック含む）"""
        weather_valid, weather_reason = self.validator.validate_comment(weather_comment, weather_data)
        advice_valid, advice_reason = self.validator.validate_comment(advice_comment, weather_data)
        
        if not weather_valid or not advice_valid:
            logger.critical("個別バリデーション失敗:")
            logger.critical(f"  天気コメント: '{weather_comment.comment_text}' - {weather_reason}")
            logger.critical(f"  アドバイス: '{advice_comment.comment_text}' - {advice_reason}")
            return False
        
        # 包括的一貫性チェック（新機能）
        consistency_valid, consistency_reason = self.validator.validate_comment_pair_consistency(
            weather_comment.comment_text, advice_comment.comment_text, weather_data
        )
        
        if not consistency_valid:
            logger.warning(f"一貫性チェック失敗: {consistency_reason}")
            logger.warning(f"  天気コメント: '{weather_comment.comment_text}'")
            logger.warning(f"  アドバイス: '{advice_comment.comment_text}'")
            return False
        
        # 従来の重複チェック（後方互換）
        if self._is_duplicate_content(weather_comment.comment_text, advice_comment.comment_text):
            logger.warning(f"重複コンテンツ検出: 天気='{weather_comment.comment_text}', アドバイス='{advice_comment.comment_text}'")
            return False
            
        logger.info(f"コメントペア一貫性チェック成功: {consistency_reason}")
        return True
    
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
    
    def is_sunny_weather_with_changeable_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """晴天時に「変わりやすい」系のコメントが含まれているかチェック（強化）"""
        weather_desc = weather_data.weather_description.lower()
        
        # 晴れ・快晴・猛暑の判定
        if not any(sunny in weather_desc for sunny in ["晴", "快晴", "晴れ", "晴天", "猛暑"]):
            return False
        
        # 不適切な「変わりやすい」表現パターン
        inappropriate_patterns = [
            "変わりやすい空", "変わりやすい天気", "変わりやすい",
            "変化しやすい空", "変化しやすい天気", "変化しやすい",
            "移ろいやすい空", "移ろいやすい天気", "移ろいやすい",
            "気まぐれな空", "気まぐれな天気", "気まぐれ",
            "一定しない空", "一定しない天気", "一定しない",
            "不安定な空模様", "不安定な天気", "不安定",
            "変動しやすい", "不規則な空", "コロコロ変わる"
        ]
        
        for pattern in inappropriate_patterns:
            if pattern in comment_text:
                logger.info(f"晴天時に不適切な表現検出: '{comment_text}' - パターン「{pattern}」")
                return True
        
        return False
    
    def is_cloudy_weather_with_sunshine_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """曇り天気時に日差し関連のコメントが含まれているかチェック"""
        weather_desc = weather_data.weather_description.lower()
        
        # 曇り・薄曇りの判定
        if not any(cloudy in weather_desc for cloudy in ["曇", "くもり", "うすぐもり", "薄曇"]):
            return False
        
        # 不適切な日差し関連表現パターン
        sunshine_patterns = [
            "強い日差し", "日差しが強", "強烈な日差し", "照りつける太陽",
            "燦々と", "さんさんと", "ギラギラ", "まぶしい太陽",
            "日光が強", "紫外線が強", "日焼け注意", "サングラス必須",
            "太陽が照り", "陽射しが強", "日向は暑", "カンカン照り",
            "ジリジリ", "じりじり", "日差しジリジリ", "照りつけ",
            "日差しの威力", "太陽の威力", "焼けつく"
        ]
        
        for pattern in sunshine_patterns:
            if pattern in comment_text:
                logger.info(f"曇り天気時に不適切な日差し表現検出: '{comment_text}' - パターン「{pattern}」")
                return True
        
        return False
    
    def is_no_rain_weather_with_rain_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """降水なしの天気時に雨・雷関連のコメントが含まれているかチェック"""
        # 降水量が0または極めて少ない場合（0.5mm未満）
        if weather_data.precipitation >= 0.5:
            return False
        
        # 不適切な雨・雷関連表現パターン
        rain_patterns = [
            "強雨", "雷雨", "大雨", "豪雨", "激しい雨",
            "雷に注意", "雷雨に注意", "落雷", "雷鳴",
            "土砂降り", "どしゃ降り", "ザーザー", "バケツをひっくり返した",
            "雨脚が強", "雨が激し", "傘が役に立たない", "ずぶ濡れ",
            "洪水", "冠水", "浸水", "雨量が多"
        ]
        
        for pattern in rain_patterns:
            if pattern in comment_text:
                logger.info(f"降水なし天気時に不適切な雨・雷表現検出: '{comment_text}' - パターン「{pattern}」")
                return True
        
        return False
    
    def is_inappropriate_seasonal_comment(self, comment_text: str, target_datetime) -> bool:
        """月に不適切な季節表現が含まれているかチェック"""
        from datetime import datetime
        month = target_datetime.month
        
        if month in [6, 7, 8]:  # 夏
            # 7月に不適切な表現
            inappropriate_patterns = [
                "残暑", "晩夏", "初秋", "秋めく", "秋の気配",
                "秋晴れ", "秋風", "涼秋", "仲秋", "晩秋"
            ]
            if month == 6:
                # 6月特有の不適切表現を追加
                inappropriate_patterns.extend(["盛夏", "真夏日", "猛暑日", "酷暑"])
            elif month == 7:
                # 7月特有の不適切表現
                inappropriate_patterns.extend(["初夏", "残暑"])
                
            for pattern in inappropriate_patterns:
                if pattern in comment_text:
                    logger.info(f"{month}月に不適切な季節表現検出: '{comment_text}' - パターン「{pattern}」")
                    return True
                    
        elif month == 9:
            # 9月に不適切な表現
            inappropriate_patterns = ["真夏", "盛夏", "初夏", "梅雨"]
            for pattern in inappropriate_patterns:
                if pattern in comment_text:
                    logger.info(f"9月に不適切な季節表現検出: '{comment_text}' - パターン「{pattern}」")
                    return True
                    
        return False
    
    def is_stable_weather_with_unstable_comment(self, comment_text: str, weather_data: WeatherForecast, state: Optional[CommentGenerationState] = None) -> bool:
        """安定した天気時に急変・不安定表現が含まれているかチェック"""
        # 翌日の全データから安定性を判定
        is_stable = self._check_full_day_stability(weather_data, state)
        if not is_stable:
            return False
        
        # 不適切な急変・不安定表現パターン
        unstable_patterns = [
            "天気急変", "急変", "天気が急に", "急に変わる",
            "変わりやすい天気", "変わりやすい空", "不安定な空模様", "変化しやすい",
            "天候不安定", "激しい変化", "急激な変化",
            "予想外の", "突然の", "一転して", "コロコロ変わる",
            "変わりやすい", "移ろいやすい", "気まぐれな"
        ]
        
        for pattern in unstable_patterns:
            if pattern in comment_text:
                logger.info(f"安定天気時に不適切な表現検出: '{comment_text}' - パターン「{pattern}」")
                return True
        
        return False
    
    def _check_full_day_stability(self, weather_data: WeatherForecast, state: Optional[CommentGenerationState] = None) -> bool:
        """翌日の全データから安定性を判定（現在の天気は無視）"""
        if not state:
            # stateがない場合はデフォルトで不安定とする
            return False
        
        # forecast_collectionを取得
        forecast_collection = state.generation_metadata.get('forecast_collection')
        if not forecast_collection or not hasattr(forecast_collection, 'forecasts'):
            # 翌日のデータがない場合は不安定とする
            return False
        
        # 翌日の予報データを取得（9:00-18:00）
        import pytz
        from datetime import datetime, timedelta
        
        jst = pytz.timezone("Asia/Tokyo")
        tomorrow = datetime.now(jst).date() + timedelta(days=1)
        target_hours = [9, 12, 15, 18]
        
        next_day_forecasts = []
        for forecast in forecast_collection.forecasts:
            forecast_dt = forecast.datetime
            if forecast_dt.tzinfo is None:
                forecast_dt = jst.localize(forecast_dt)
            
            # 翌日の9:00-18:00の予報のみ抽出
            if forecast_dt.date() == tomorrow and forecast_dt.hour in target_hours:
                next_day_forecasts.append(forecast)
        
        if len(next_day_forecasts) < 4:
            # 4つの時間帯のデータが揃わない場合は不安定とする
            logger.info(f"翌日のデータが不足: {len(next_day_forecasts)}件のみ")
            return False
        
        # 全ての時間帯が同じ天気か確認
        weather_types = set()
        for forecast in next_day_forecasts:
            desc = forecast.weather_description.lower()
            if any(sunny in desc for sunny in ["晴", "快晴"]):
                weather_types.add("sunny")
            elif any(cloudy in desc for cloudy in ["曇", "くもり", "うすぐもり", "薄曇"]):
                weather_types.add("cloudy")
            elif any(rainy in desc for rainy in ["雨", "rain"]):
                weather_types.add("rainy")
            else:
                weather_types.add("other")
        
        # 天気タイプの時系列を作成
        weather_type_sequence = []
        for forecast in next_day_forecasts:
            desc = forecast.weather_description.lower()
            if any(sunny in desc for sunny in ["晴", "快晴"]):
                weather_type_sequence.append("sunny")
            elif any(cloudy in desc for cloudy in ["曇", "くもり", "うすぐもり", "薄曇"]):
                weather_type_sequence.append("cloudy")
            elif any(rainy in desc for rainy in ["雨", "rain"]):
                weather_type_sequence.append("rainy")
            else:
                weather_type_sequence.append("other")
        
        # 変化回数をカウント
        type_changes = 0
        for i in range(1, len(weather_type_sequence)):
            if weather_type_sequence[i] != weather_type_sequence[i-1]:
                type_changes += 1
        
        # 2回以上変化する場合は不安定（例：曇り→晴れ→曇り→晴れ）
        if type_changes >= 2:
            logger.info(f"翌日の天気が頻繁に変化: {weather_type_sequence}, 変化回数: {type_changes}")
            return False
        
        # 異なる天気タイプが複数ある場合でも、変化が1回だけなら追加チェック
        if len(weather_types) > 1:
            # 朝だけ違って、その後同じ天気が続く場合は安定とみなす
            if type_changes == 1 and len(weather_type_sequence) >= 4:
                if weather_type_sequence[1] == weather_type_sequence[2] == weather_type_sequence[3]:
                    logger.info(f"朝だけ天気が異なるが、その後安定: {weather_type_sequence}")
                    # 朝が曇りで日中晴れ続きなら安定
                    if weather_type_sequence[0] == "cloudy" and weather_type_sequence[1] == "sunny":
                        return True
                    # 朝が晴れで日中曇り続きなら、追加条件確認へ
                    elif weather_type_sequence[0] == "sunny" and weather_type_sequence[1] == "cloudy":
                        # 曇りの安定性を確認（下の曇り判定へ）
                        pass
                else:
                    logger.info(f"翌日の天気が変化: {weather_types}")
                    return False
            else:
                logger.info(f"翌日の天気が変化: {weather_types}")
                return False
        
        # 単一の天気タイプの場合、その種類に応じて判定
        if len(weather_types) == 1:
            weather_type = list(weather_types)[0]
            
            # 全てが晴れの場合は安定
            if weather_type == "sunny":
                logger.info("翌日は終日晴天で安定")
                return True
            
            # 全てが曇りの場合、追加条件を確認
            elif weather_type == "cloudy":
                # 降水量、風速、雷のチェック
                for forecast in next_day_forecasts:
                    if forecast.precipitation > 1.0 or forecast.wind_speed > 10.0:
                        logger.info(f"翌日の曇天が不安定: 降水量={forecast.precipitation}mm, 風速={forecast.wind_speed}m/s")
                        return False
                    if "雷" in forecast.weather_description or "thunder" in forecast.weather_description.lower():
                        logger.info("翌日に雷が含まれるため不安定")
                        return False
                logger.info("翌日は終日曇天で安定")
                return True
            
            # 雨の場合は不安定とする
            else:
                logger.info(f"翌日の天気タイプ「{weather_type}」は不安定")
                return False
        
        # その他の場合は不安定
        return False
    
    def should_exclude_weather_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """天気コメントを除外すべきかチェック（YAML設定ベース）"""
        try:
            # yamlモジュールのインポートを条件付きで実行
            try:
                import yaml
            except ImportError:
                logger.debug("PyYAMLがインストールされていません。基本チェックのみ実行")
                return False
            
            try:
                from src.config.weather_constants import TemperatureThresholds, HumidityThresholds, PrecipitationThresholds
            except ImportError:
                logger.debug("weather_constants.pyが見つかりません。基本チェックのみ実行")
                return False
            
            # YAML設定ファイル読み込み
            config_path = Path(__file__).parent.parent.parent / "config" / "comment_restrictions.yaml"
            if not config_path.exists():
                logger.debug("comment_restrictions.yaml が見つかりません。基本チェックのみ実行")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                restrictions = yaml.safe_load(f)
            
            # 天気条件による除外チェック
            weather_desc = weather_data.weather_description.lower()
            
            # 雨天時のチェック
            if any(keyword in weather_desc for keyword in ['雨', 'rain']):
                if weather_data.precipitation >= PrecipitationThresholds.HEAVY_RAIN:
                    forbidden_list = restrictions.get('weather_restrictions', {}).get('heavy_rain', {}).get('weather_comment_forbidden', [])
                else:
                    forbidden_list = restrictions.get('weather_restrictions', {}).get('rain', {}).get('weather_comment_forbidden', [])
                
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"雨天時の禁止ワード「{forbidden}」でコメント除外: {comment_text}")
                        return True
            
            # 晴天時のチェック
            elif any(keyword in weather_desc for keyword in ['晴', 'clear', 'sunny']):
                forbidden_list = restrictions.get('weather_restrictions', {}).get('sunny', {}).get('weather_comment_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"晴天時の禁止ワード「{forbidden}」でコメント除外: {comment_text}")
                        return True
            
            # 曇天時のチェック
            elif any(keyword in weather_desc for keyword in ['曇', 'cloud']):
                forbidden_list = restrictions.get('weather_restrictions', {}).get('cloudy', {}).get('weather_comment_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"曇天時の禁止ワード「{forbidden}」でコメント除外: {comment_text}")
                        return True
            
            # 気温による除外チェック
            temp = weather_data.temperature
            temp_restrictions = restrictions.get('temperature_restrictions', {})
            
            if temp >= TemperatureThresholds.HOT_WEATHER:
                forbidden_list = temp_restrictions.get('hot_weather', {}).get('forbidden_keywords', [])
            elif temp < TemperatureThresholds.COLD_COMMENT_THRESHOLD:
                forbidden_list = temp_restrictions.get('cold_weather', {}).get('forbidden_keywords', [])
            else:
                forbidden_list = temp_restrictions.get('mild_weather', {}).get('forbidden_keywords', [])
            
            for forbidden in forbidden_list:
                if forbidden in comment_text:
                    logger.debug(f"気温条件「{temp}°C」で禁止ワード「{forbidden}」によりコメント除外: {comment_text}")
                    return True
            
            # 湿度による除外チェック
            humidity = weather_data.humidity
            humidity_restrictions = restrictions.get('humidity_restrictions', {})
            
            if humidity >= HumidityThresholds.HIGH_HUMIDITY:
                forbidden_list = humidity_restrictions.get('high_humidity', {}).get('forbidden_keywords', [])
            elif humidity < HumidityThresholds.LOW_HUMIDITY:
                forbidden_list = humidity_restrictions.get('low_humidity', {}).get('forbidden_keywords', [])
            else:
                forbidden_list = []
            
            for forbidden in forbidden_list:
                if forbidden in comment_text:
                    logger.debug(f"湿度条件「{humidity}%」で禁止ワード「{forbidden}」によりコメント除外: {comment_text}")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"YAML設定チェック中にエラー: {e}")
            return False
    
    def should_exclude_advice_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """アドバイスコメントを除外すべきかチェック（YAML設定ベース）"""
        try:
            # yamlモジュールのインポートを条件付きで実行
            try:
                import yaml
            except ImportError:
                logger.debug("PyYAMLがインストールされていません。基本チェックのみ実行")
                return False
            
            try:
                from src.config.weather_constants import PrecipitationThresholds
            except ImportError:
                logger.debug("weather_constants.pyが見つかりません。基本チェックのみ実行")
                return False
            
            # YAML設定ファイル読み込み
            config_path = Path(__file__).parent.parent.parent / "config" / "comment_restrictions.yaml"
            if not config_path.exists():
                logger.debug("comment_restrictions.yaml が見つかりません。基本チェックのみ実行")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                restrictions = yaml.safe_load(f)
            
            # 天気条件による除外チェック
            weather_desc = weather_data.weather_description.lower()
            
            # 雨天時のチェック
            if any(keyword in weather_desc for keyword in ['雨', 'rain']):
                if weather_data.precipitation >= PrecipitationThresholds.HEAVY_RAIN:
                    forbidden_list = restrictions.get('weather_restrictions', {}).get('heavy_rain', {}).get('advice_forbidden', [])
                else:
                    forbidden_list = restrictions.get('weather_restrictions', {}).get('rain', {}).get('advice_forbidden', [])
                
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"雨天時の禁止ワード「{forbidden}」でアドバイス除外: {comment_text}")
                        return True
            
            # 晴天時のチェック
            elif any(keyword in weather_desc for keyword in ['晴', 'clear', 'sunny']):
                forbidden_list = restrictions.get('weather_restrictions', {}).get('sunny', {}).get('advice_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"晴天時の禁止ワード「{forbidden}」でアドバイス除外: {comment_text}")
                        return True
            
            # 曇天時のチェック
            elif any(keyword in weather_desc for keyword in ['曇', 'cloud']):
                forbidden_list = restrictions.get('weather_restrictions', {}).get('cloudy', {}).get('advice_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"曇天時の禁止ワード「{forbidden}」でアドバイス除外: {comment_text}")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"YAML設定チェック中にエラー: {e}")
            return False
    
    def is_severe_weather_appropriate(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """コメントが極端な天候に適切かチェック"""
        return any(pattern in comment_text for pattern in SEVERE_WEATHER_PATTERNS)
    
    def is_weather_matched(self, comment_condition: Optional[str], weather_description: str) -> bool:
        """コメントの天気条件と実際の天気が一致するかチェック"""
        if not comment_condition:
            return True
        return comment_condition.lower() in weather_description.lower()
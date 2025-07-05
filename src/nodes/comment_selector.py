"""コメント選択ロジックを分離したクラス"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import CommentType, PastCommentCollection, PastComment
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager
from src.config.comment_config import get_comment_config
from src.config.severe_weather_config import get_severe_weather_config
from src.data.forecast_cache import ForecastCache
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.utils.common_utils import SEVERE_WEATHER_PATTERNS, FORBIDDEN_PHRASES

logger = logging.getLogger(__name__)


class CommentSelector:
    """コメント選択クラス"""
    
    def __init__(self, llm_manager: LLMManager, validator: WeatherCommentValidator):
        self.llm_manager = llm_manager
        self.validator = validator
        self.severe_config = get_severe_weather_config()
    
    def select_optimal_comment_pair(
        self, 
        weather_comments: List[PastComment], 
        advice_comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None,
        exclude_weather_comment: Optional[str] = None,
        exclude_advice_comment: Optional[str] = None
    ) -> Optional[CommentPair]:
        """最適なコメントペアを選択"""
        
        # 事前フィルタリング
        filtered_weather = self.validator.get_weather_appropriate_comments(
            weather_comments, weather_data, CommentType.WEATHER_COMMENT, limit=100
        )
        filtered_advice = self.validator.get_weather_appropriate_comments(
            advice_comments, weather_data, CommentType.ADVICE, limit=100
        )
        
        # 除外対象のコメントを削除
        if exclude_weather_comment:
            original_count = len(filtered_weather)
            filtered_weather = [c for c in filtered_weather 
                             if c.comment_text.strip() != exclude_weather_comment.strip()]
            logger.info(f"天気コメントから前回の生成結果を除外: '{exclude_weather_comment}' (除外前: {original_count}件 → 除外後: {len(filtered_weather)}件)")
            
        if exclude_advice_comment:
            original_count = len(filtered_advice)
            filtered_advice = [c for c in filtered_advice 
                             if c.comment_text.strip() != exclude_advice_comment.strip()]
            logger.info(f"アドバイスコメントから前回の生成結果を除外: '{exclude_advice_comment}' (除外前: {original_count}件 → 除外後: {len(filtered_advice)}件)")
        
        logger.info(f"フィルタリング結果 - 天気: {len(weather_comments)} -> {len(filtered_weather)}")
        logger.info(f"フィルタリング結果 - アドバイス: {len(advice_comments)} -> {len(filtered_advice)}")
        
        # 最適なコメントを選択
        best_weather = self._select_best_weather_comment(
            filtered_weather, weather_data, location_name, target_datetime, state
        )
        best_advice = self._select_best_advice_comment(
            filtered_advice, weather_data, location_name, target_datetime, state
        )
        
        if not best_weather or not best_advice:
            return None
            
        # ペア作成前の最終バリデーション
        if not self._validate_comment_pair(best_weather, best_advice, weather_data):
            # 重複回避のための代替選択を試行
            alternative_pair = self._select_alternative_non_duplicate_pair(
                filtered_weather, filtered_advice, weather_data, location_name, target_datetime, state
            )
            if alternative_pair:
                return alternative_pair
            
            # 代替選択も失敗した場合はフォールバック処理
            return self._fallback_comment_selection(
                weather_comments, advice_comments, weather_data
            )
        
        return CommentPair(
            weather_comment=best_weather,
            advice_comment=best_advice,
            similarity_score=1.0,
            selection_reason="LLMによる最適選択",
        )
    
    def _select_best_weather_comment(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """最適な天気コメントを選択"""
        if not comments:
            logger.warning("天気コメントが空です")
            return None
            
        candidates = self._prepare_weather_candidates(comments, weather_data, state)
        if not candidates:
            logger.warning("天気コメント候補が空です")
            return None
            
        selected_comment = self._llm_select_comment(
            candidates, weather_data, location_name, target_datetime, 
            CommentType.WEATHER_COMMENT, state
        )
        
        return selected_comment

    def _select_best_advice_comment(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """最適なアドバイスコメントを選択"""
        if not comments:
            logger.warning("アドバイスコメントが空です")
            return None
            
        candidates = self._prepare_advice_candidates(comments, weather_data)
        if not candidates:
            logger.warning("アドバイスコメント候補が空です")
            return None
            
        selected_comment = self._llm_select_comment(
            candidates, weather_data, location_name, target_datetime, 
            CommentType.ADVICE, state
        )
        
        return selected_comment
    
    def _prepare_weather_candidates(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast,
        state: Optional[CommentGenerationState] = None
    ) -> List[Dict[str, Any]]:
        """天気コメント候補を準備"""
        candidates = []
        severe_matched = []
        weather_matched = []
        others = []
        
        for i, comment in enumerate(comments):
            # バリデーターによる除外チェック（強化版）
            is_valid, reason = self.validator.validate_comment(comment, weather_data)
            if not is_valid:
                logger.info(f"バリデーター除外: '{comment.comment_text}' - 理由: {reason}")
                continue
            
            # 晴天時の「変わりやすい」表現の追加チェック（強化）
            if self._is_sunny_weather_with_changeable_comment(comment.comment_text, weather_data):
                logger.info(f"晴天時不適切表現を強制除外: '{comment.comment_text}'")
                continue
            
            # 安定した天気での急変表現の追加チェック
            if self._is_stable_weather_with_unstable_comment(comment.comment_text, weather_data, state):
                logger.info(f"安定天気時の急変表現を強制除外: '{comment.comment_text}'")
                continue
                
            # 旧式の除外チェック（後方互換）
            if self._should_exclude_weather_comment(comment.comment_text, weather_data):
                logger.debug(f"天気条件不適合のため除外: '{comment.comment_text}'")
                continue
                
            candidate = self._create_candidate_dict(
                len(severe_matched) + len(weather_matched) + len(others), 
                comment, 
                original_index=i
            )
            
            # 悪天候時の特別な優先順位付け
            if self.severe_config.is_severe_weather(weather_data.weather_condition):
                if self._is_severe_weather_appropriate(comment.comment_text, weather_data):
                    severe_matched.append(candidate)
                elif self._is_weather_matched(comment.weather_condition, weather_data.weather_description):
                    weather_matched.append(candidate)
                else:
                    others.append(candidate)
            else:
                if self._is_weather_matched(comment.weather_condition, weather_data.weather_description):
                    weather_matched.append(candidate)
                else:
                    others.append(candidate)
        
        # 優先順位順に結合（設定ファイルから制限を取得）
        from src.config.config_loader import load_config
        try:
            config = load_config('weather_thresholds', validate=False)
            limit = config.get('generation', {}).get('weather_candidates_limit', 100)
        except:
            limit = 100  # デフォルト値
        
        # 設定ファイルから候補比率を取得
        try:
            ratios = config.get('generation', {}).get('candidate_ratios', {})
            severe_ratio = ratios.get('severe_weather', 0.4)
            weather_ratio = ratios.get('weather_matched', 0.4)
            others_ratio = ratios.get('others', 0.2)
        except:
            # デフォルト比率（悪天候40%, 天気マッチ40%, その他20%）
            severe_ratio, weather_ratio, others_ratio = 0.4, 0.4, 0.2
        
        # 各カテゴリの制限を計算
        severe_limit = int(limit * severe_ratio)
        weather_limit = int(limit * weather_ratio) 
        others_limit = limit - severe_limit - weather_limit
        
        candidates = (severe_matched[:severe_limit] + weather_matched[:weather_limit] + others[:others_limit])
        
        return candidates
    
    def _prepare_advice_candidates(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast
    ) -> List[Dict[str, Any]]:
        """アドバイスコメント候補を準備"""
        candidates = []
        
        for i, comment in enumerate(comments):
            # バリデーターによる除外チェック
            is_valid, reason = self.validator.validate_comment(comment, weather_data)
            if not is_valid:
                logger.info(f"アドバイスバリデーター除外: '{comment.comment_text}' - 理由: {reason}")
                continue
                
            # 旧式の除外チェック（後方互換）
            if self._should_exclude_advice_comment(comment.comment_text, weather_data):
                logger.debug(f"アドバイス条件不適合のため除外: '{comment.comment_text}'")
                continue
                
            candidate = self._create_candidate_dict(len(candidates), comment, original_index=i)
            candidates.append(candidate)
            
            # 設定ファイルから制限を取得
            from src.config.config_loader import load_config
            try:
                config = load_config('weather_thresholds', validate=False)
                limit = config.get('generation', {}).get('advice_candidates_limit', 100)
            except:
                limit = 100  # デフォルト値
            
            if len(candidates) >= limit:
                break
        
        return candidates
    
    def _validate_comment_pair(
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
    
    def _fallback_comment_selection(
        self, 
        weather_comments: List[PastComment], 
        advice_comments: List[PastComment], 
        weather_data: WeatherForecast
    ) -> Optional[CommentPair]:
        """フォールバック: 雨天時の代替コメント選択"""
        logger.critical("代替コメント選択を実行")
        
        rain_weather = self._find_rain_appropriate_weather_comment(weather_comments)
        rain_advice = self._find_rain_appropriate_advice_comment(advice_comments, weather_data)
        
        if rain_weather and rain_advice:
            logger.critical(f"代替選択完了 - 天気: '{rain_weather.comment_text}', アドバイス: '{rain_advice.comment_text}'")
            return CommentPair(
                weather_comment=rain_weather,
                advice_comment=rain_advice,
                similarity_score=1.0,
                selection_reason="雨天対応代替選択",
            )
        
        logger.error("代替選択も失敗")
        return None
    
    def _find_rain_appropriate_weather_comment(
        self, 
        comments: List[PastComment]
    ) -> Optional[PastComment]:
        """雨天に適した天気コメントを検索"""
        for comment in comments:
            if (any(keyword in comment.comment_text for keyword in ["雨", "荒れ", "心配", "警戒", "注意"]) and
                not any(forbidden in comment.comment_text for forbidden in ["穏やか", "過ごしやすい", "快適", "爽やか"])):
                return comment
        return None
    
    def _find_rain_appropriate_advice_comment(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast
    ) -> Optional[PastComment]:
        """雨天に適したアドバイスコメントを検索"""
        for comment in comments:
            if (any(keyword in comment.comment_text for keyword in ["傘", "雨", "濡れ", "注意", "安全", "室内"]) and
                not any(forbidden in comment.comment_text for forbidden in ["過ごしやすい", "快適", "お出かけ", "散歩"]) and
                not self._should_exclude_advice_comment(comment.comment_text, weather_data)):
                return comment
        return None
    
    # ヘルパーメソッド（既存のprivate関数から移行）
    def _is_sunny_weather_with_changeable_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
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
    
    def _is_stable_weather_with_unstable_comment(self, comment_text: str, weather_data: WeatherForecast, state: Optional[CommentGenerationState] = None) -> bool:
        """安定した天気時に急変・不安定表現が含まれているかチェック"""
        # 翌日の全データから安定性を判定
        is_stable = self._check_full_day_stability(weather_data, state)
        if not is_stable:
            return False
        
        # 不適切な急変・不安定表現パターン
        unstable_patterns = [
            "天気急変", "急変", "天気が急に", "急に変わる",
            "変わりやすい天気", "不安定な空模様", "変化しやすい",
            "天候不安定", "激しい変化", "急激な変化",
            "予想外の", "突然の", "一転して", "コロコロ変わる"
        ]
        
        for pattern in unstable_patterns:
            if pattern in comment_text:
                logger.info(f"安定天気時に不適切な表現検出: '{comment_text}' - パターン「{pattern}」")
                return True
        
        return False
    
    def _check_full_day_stability(self, weather_data: WeatherForecast, state: Optional[CommentGenerationState] = None) -> bool:
        """翌日の全データから安定性を判定"""
        if not state:
            # stateがない場合は現在の天気データのみで判定
            return weather_data.is_stable_weather()
        
        # forecast_collectionを取得
        forecast_collection = state.generation_metadata.get('forecast_collection')
        if not forecast_collection or not hasattr(forecast_collection, 'forecasts'):
            # 翌日のデータがない場合は現在のデータのみで判定
            return weather_data.is_stable_weather()
        
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
        
        if not next_day_forecasts:
            # 翌日のデータがない場合は現在のデータのみで判定
            return weather_data.is_stable_weather()
        
        # 全ての時間帯が同じ天気か確認
        weather_types = set()
        for forecast in next_day_forecasts:
            desc = forecast.weather_description.lower()
            if any(sunny in desc for sunny in ["晴", "快晴"]):
                weather_types.add("sunny")
            elif any(cloudy in desc for cloudy in ["曇", "くもり"]):
                weather_types.add("cloudy")
            elif any(rainy in desc for rainy in ["雨", "rain"]):
                weather_types.add("rainy")
            else:
                weather_types.add("other")
        
        # 異なる天気タイプが複数ある場合は不安定
        if len(weather_types) > 1:
            logger.info(f"翌日の天気が変化: {weather_types}")
            return False
        
        # 全てが曇りの場合、追加条件を確認
        if weather_types == {"cloudy"}:
            # 降水量、風速、雷のチェック
            for forecast in next_day_forecasts:
                if forecast.precipitation > 1.0 or forecast.wind_speed > 5.0:
                    logger.info(f"翌日の曇天が不安定: 降水量={forecast.precipitation}mm, 風速={forecast.wind_speed}m/s")
                    return False
                if "雷" in forecast.weather_description or "thunder" in forecast.weather_description.lower():
                    logger.info("翌日に雷が含まれるため不安定")
                    return False
            logger.info("翌日は安定した曇天")
            return True
        
        # 全てが晴れの場合は安定
        if weather_types == {"sunny"}:
            logger.info("翌日は安定した晴天")
            return True
        
        # その他の場合は不安定
        return False

    def _should_exclude_weather_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """天気コメントを除外すべきかチェック（YAML設定ベース）"""
        try:
            from pathlib import Path
            
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
            config_path = Path(__file__).parent.parent / "config" / "comment_restrictions.yaml"
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
    
    def _should_exclude_advice_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """アドバイスコメントを除外すべきかチェック（YAML設定ベース）"""
        try:
            from pathlib import Path
            
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
            config_path = Path(__file__).parent.parent / "config" / "comment_restrictions.yaml"
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
    
    def _is_severe_weather_appropriate(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """悪天候に適したコメントかチェック"""
        severe_keywords = ["雨", "荒れ", "心配", "警戒", "注意", "傘", "安全"]
        return any(keyword in comment_text for keyword in severe_keywords)
    
    def _is_weather_matched(self, comment_condition: Optional[str], weather_description: str) -> bool:
        """天気条件がマッチするかチェック"""
        if not comment_condition:
            return False
        return comment_condition.lower() in weather_description.lower()
    
    def _create_candidate_dict(self, index: int, comment: PastComment, original_index: int) -> Dict[str, Any]:
        """候補辞書を作成"""
        return {
            'index': index,
            'comment': comment.comment_text,
            'weather_condition': comment.weather_condition or "不明",
            'original_index': original_index,
            'usage_count': comment.usage_count or 0,
            'comment_object': comment  # 元のcommentオブジェクトを保持
        }
    
    def _llm_select_comment(
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
                candidates, weather_data, location_name, target_datetime, comment_type
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
        comment_type: CommentType
    ) -> Optional[Dict[str, Any]]:
        """LLMによる実際の選択処理"""
        # 候補リストを文字列として整形
        candidates_text = self._format_candidates_for_llm(candidates)
        
        # 天気情報を整形
        weather_context = self._format_weather_context(weather_data, location_name, target_datetime)
        
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
    
    def _format_weather_context(self, weather_data: WeatherForecast, location_name: str, target_datetime: datetime) -> str:
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
5. 季節感が適切
6. 自然で読みやすい表現

{sunny_warning}

特に以下を重視してください:
- 天気の安定性（晴れ・快晴は安定、雨・曇りは変化しやすい）
- 気温変化の傾向（上昇中、下降中、安定）
- 天気の変化予想（悪化、改善、安定）
- その地域の気候特性

【重要】選択した候補の番号のみを回答してください。
説明は不要です。数字のみを返してください。

例: 2
"""
    
    def _extract_selected_index(self, response: str, max_index: int) -> Optional[int]:
        """LLMレスポンスから選択インデックスを抽出（堅牢化）"""
        import re
        
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
    
    def _select_alternative_non_duplicate_pair(
        self,
        weather_comments: List[PastComment],
        advice_comments: List[PastComment],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[CommentPair]:
        """重複を回避する代替ペア選択"""
        logger.info("重複回避のための代替コメントペア選択を開始")
        
        # 複数の候補を生成して重複しないペアを探す
        weather_candidates = self._prepare_weather_candidates(weather_comments, weather_data)
        advice_candidates = self._prepare_advice_candidates(advice_comments, weather_data)
        
        # 上位候補から順に試行（最大10回）
        max_attempts = min(10, len(weather_candidates), len(advice_candidates))
        
        for attempt in range(max_attempts):
            try:
                # 天気コメント候補を選択（異なるものを順番に試す）
                weather_idx = attempt % len(weather_candidates)
                weather_candidate = weather_candidates[weather_idx]['comment_object']
                
                # アドバイス候補を選択
                advice_idx = attempt % len(advice_candidates)
                advice_candidate = advice_candidates[advice_idx]['comment_object']
                
                # 包括的バリデーションチェック（新しい一貫性チェック含む）
                if self._validate_comment_pair(weather_candidate, advice_candidate, weather_data):
                    logger.info(f"代替ペア選択成功 (試行{attempt+1}): 天気='{weather_candidate.comment_text}', アドバイス='{advice_candidate.comment_text}'")
                    return CommentPair(
                        weather_comment=weather_candidate,
                        advice_comment=advice_candidate,
                        similarity_score=0.8,  # 代替選択なので若干低めのスコア
                        selection_reason=f"重複回避代替選択（試行{attempt+1}回目）"
                    )
                
                logger.debug(f"試行{attempt+1}: 重複または無効 - 天気='{weather_candidate.comment_text}', アドバイス='{advice_candidate.comment_text}'")
                
            except Exception as e:
                logger.warning(f"代替選択試行{attempt+1}でエラー: {e}")
                continue
        
        logger.warning("重複しない代替ペアの選択に失敗")
        return None
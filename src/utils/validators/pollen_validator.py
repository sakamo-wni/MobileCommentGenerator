"""花粉関連のコメント検証"""

import logging
from datetime import datetime

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)


class PollenValidator(BaseValidator):
    """花粉関連のコメント検証クラス"""
    
    # 花粉飛散期間外の月（デフォルト：6月〜1月）
    NON_POLLEN_MONTHS = [6, 7, 8, 9, 10, 11, 12, 1]
    
    # 統計情報
    _validation_stats = {
        "total_checks": 0,
        "pollen_detected": 0,
        "seasonal_rejects": 0,
        "weather_rejects": 0,
        "dispersion_rejects": 0
    }
    
    # 地域別の花粉シーズン設定
    REGIONAL_POLLEN_SEASONS = {
        # 北海道・東北（シラカバ花粉が主）
        "北海道": {"start": 4, "end": 6, "main_types": ["シラカバ", "ハンノキ"]},
        "青森": {"start": 4, "end": 6, "main_types": ["シラカバ", "スギ"]},
        "岩手": {"start": 3, "end": 5, "main_types": ["スギ", "シラカバ"]},
        "宮城": {"start": 3, "end": 5, "main_types": ["スギ", "ヒノキ"]},
        "秋田": {"start": 3, "end": 5, "main_types": ["スギ", "シラカバ"]},
        "山形": {"start": 3, "end": 5, "main_types": ["スギ"]},
        "福島": {"start": 3, "end": 5, "main_types": ["スギ", "ヒノキ"]},
        
        # 関東（スギ・ヒノキが主）
        "茨城": {"start": 2, "end": 5, "main_types": ["スギ", "ヒノキ"]},
        "栃木": {"start": 2, "end": 5, "main_types": ["スギ", "ヒノキ"]},
        "群馬": {"start": 2, "end": 5, "main_types": ["スギ", "ヒノキ"]},
        "埼玉": {"start": 2, "end": 5, "main_types": ["スギ", "ヒノキ"]},
        "千葉": {"start": 2, "end": 5, "main_types": ["スギ", "ヒノキ"]},
        "東京": {"start": 2, "end": 5, "main_types": ["スギ", "ヒノキ"]},
        "神奈川": {"start": 2, "end": 5, "main_types": ["スギ", "ヒノキ"]},
        
        # 西日本（早めの飛散開始）
        "大阪": {"start": 2, "end": 4, "main_types": ["スギ", "ヒノキ"]},
        "京都": {"start": 2, "end": 4, "main_types": ["スギ", "ヒノキ"]},
        "兵庫": {"start": 2, "end": 4, "main_types": ["スギ", "ヒノキ"]},
        
        # 九州（最も早い飛散開始）
        "福岡": {"start": 1, "end": 4, "main_types": ["スギ", "ヒノキ"]},
        "熊本": {"start": 1, "end": 4, "main_types": ["スギ", "ヒノキ"]},
        "鹿児島": {"start": 1, "end": 4, "main_types": ["スギ"]},
        
        # 沖縄（ほぼ花粉なし）
        "沖縄": {"start": 0, "end": 0, "main_types": []},
    }
    
    # 花粉関連表現パターン
    POLLEN_PATTERNS = [
        "花粉", "花粉症", "花粉対策", "花粉飛散", "花粉情報",
        "マスクで花粉", "くしゃみ", "鼻水", "目のかゆみ",
        "花粉予報", "花粉量", "スギ花粉", "ヒノキ花粉", "シラカバ花粉"
    ]
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> tuple[bool, str]:
        """
        花粉関連コメントの妥当性を検証
        
        Args:
            comment: 検証対象のコメント
            weather_data: 天気データ
            
        Returns:
            (is_valid, reason): 検証結果とその理由
        """
        comment_text = comment.comment_text
        self._validation_stats["total_checks"] += 1
        
        # 花粉表現が含まれているかチェック
        if not self._contains_pollen_expression(comment_text):
            # 花粉表現が含まれていない場合は検証をパス
            return True, ""
        
        self._validation_stats["pollen_detected"] += 1
        
        # 1. 地域別の季節チェック
        location = getattr(comment, 'location', None) or getattr(weather_data, 'location', None)
        season_check = self._check_seasonal_validity(weather_data.datetime, location)
        if not season_check[0]:
            self._validation_stats["seasonal_rejects"] += 1
            self._log_validation_stats()
            return season_check
        
        # 2. 天気条件チェック（雨天時）
        weather_check = self._check_weather_validity(weather_data)
        if not weather_check[0]:
            if "飛散しにくい" in weather_check[1] or "飛び去る" in weather_check[1]:
                self._validation_stats["dispersion_rejects"] += 1
            else:
                self._validation_stats["weather_rejects"] += 1
            self._log_validation_stats()
            return weather_check
        
        return True, "花粉コメント検証OK"
    
    def _log_validation_stats(self):
        """統計情報を定期的にログ出力"""
        if self._validation_stats["total_checks"] % 100 == 0:
            logger.info(
                f"花粉バリデーション統計 - "
                f"総チェック数: {self._validation_stats['total_checks']}, "
                f"花粉検出: {self._validation_stats['pollen_detected']}, "
                f"季節除外: {self._validation_stats['seasonal_rejects']}, "
                f"天気除外: {self._validation_stats['weather_rejects']}, "
                f"飛散条件除外: {self._validation_stats['dispersion_rejects']}"
            )
    
    def _contains_pollen_expression(self, text: str) -> bool:
        """テキストに花粉関連表現が含まれているかチェック"""
        return any(pattern in text for pattern in self.POLLEN_PATTERNS)
    
    def _check_seasonal_validity(self, target_datetime: datetime, location: str = None) -> tuple[bool, str]:
        """地域別の季節的な妥当性をチェック"""
        month = target_datetime.month
        
        # 地域情報がある場合は地域別判定
        if location:
            regional_info = self._get_regional_pollen_info(location)
            if regional_info:
                start_month = regional_info["start"]
                end_month = regional_info["end"]
                
                # 沖縄の特殊処理
                if start_month == 0 and end_month == 0:
                    return False, f"{location}では花粉がほとんど飛散しない"
                
                # 地域別の花粉シーズンチェック
                if start_month <= month <= end_month:
                    main_types = regional_info.get("main_types", [])
                    logger.debug(f"{location}の{month}月は花粉シーズン（主な花粉: {', '.join(main_types)}）")
                    return True, ""
                else:
                    return False, f"{location}の{month}月は花粉飛散期間外"
        
        # デフォルトの判定
        if month in self.NON_POLLEN_MONTHS:
            return False, f"{month}月は花粉飛散期間外"
        
        return True, ""
    
    def _get_regional_pollen_info(self, location: str) -> dict:
        """地域名から花粉情報を取得"""
        # 都道府県名を抽出（例: "東京都中央区" → "東京"）
        for prefecture in self.REGIONAL_POLLEN_SEASONS.keys():
            if prefecture in location:
                return self.REGIONAL_POLLEN_SEASONS[prefecture]
        
        # 部分一致で再度検索
        location_lower = location.lower()
        for prefecture, info in self.REGIONAL_POLLEN_SEASONS.items():
            if prefecture.lower() in location_lower:
                return info
        
        return None
    
    def _check_weather_validity(self, weather_data: WeatherForecast) -> tuple[bool, str]:
        """天気条件での妥当性をチェック"""
        weather_desc = weather_data.weather_description.lower()
        
        # 雨天時は花粉が飛散しない
        if any(rain in weather_desc for rain in ["雨", "rain"]) or weather_data.precipitation > 0:
            return False, "雨天時は花粉が飛散しない"
        
        # 花粉飛散強度をチェック
        dispersion_suitable, reason = self._check_pollen_dispersion_conditions(weather_data)
        if not dispersion_suitable:
            return False, reason
        
        return True, ""
    
    def _check_pollen_dispersion_conditions(self, weather: WeatherForecast) -> tuple[bool, str]:
        """風速と湿度を考慮した花粉飛散条件の判定"""
        # 高湿度時（80%以上）は花粉が飛散しにくい
        if weather.humidity >= 80:
            return False, f"高湿度（{weather.humidity}%）のため花粉が飛散しにくい"
        
        # 風速による判定（ただし強風すぎる場合は花粉が飛び去る）
        if weather.wind_speed > 15.0:
            return False, f"強風（{weather.wind_speed}m/s）のため花粉が飛び去る"
        
        # 適度な風（2-10m/s）は花粉が飛散しやすい
        if 2.0 <= weather.wind_speed <= 10.0:
            logger.debug(f"適度な風速（{weather.wind_speed}m/s）で花粉飛散に適した条件")
        
        return True, ""
    
    def is_inappropriate_pollen_comment(self, comment_text: str, weather_data: WeatherForecast, 
                                       target_datetime: datetime, location: str = None) -> bool:
        """
        花粉コメントが不適切かどうかを判定
        
        Args:
            comment_text: コメントテキスト
            weather_data: 天気データ
            target_datetime: 対象日時
            location: 地域名（オプション）
            
        Returns:
            不適切な場合True
        """
        # 花粉表現が含まれていない場合はFalse
        if not self._contains_pollen_expression(comment_text):
            return False
        
        # 地域を取得
        if not location and weather_data:
            location = getattr(weather_data, 'location', None)
        
        # 地域別の季節チェック
        season_valid, reason = self._check_seasonal_validity(target_datetime, location)
        if not season_valid:
            logger.info(f"花粉コメント除外: {reason} - '{comment_text}'")
            return True
        
        # 天気条件チェック
        if weather_data:
            weather_valid, weather_reason = self._check_weather_validity(weather_data)
            if not weather_valid:
                logger.info(f"花粉コメント除外: {weather_reason} - '{comment_text}'")
                return True
        
        return False
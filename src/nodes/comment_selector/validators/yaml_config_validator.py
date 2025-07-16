"""YAML設定ベースのバリデーター"""

from __future__ import annotations
import logging
from pathlib import Path

from src.data.weather_data import WeatherForecast

logger = logging.getLogger(__name__)


class YamlConfigValidator:
    """YAML設定ファイルベースのコメント除外チェック"""
    
    def __init__(self):
        self.yaml = None
        self.restrictions = None
        self.weather_constants = None
        self._load_dependencies()
    
    def _load_dependencies(self):
        """依存モジュールの読み込み"""
        try:
            import yaml
            self.yaml = yaml
        except ImportError:
            logger.debug("PyYAMLがインストールされていません。基本チェックのみ実行")
            return
        
        try:
            from src.config.config import get_weather_constants
            self.weather_constants = get_weather_constants()
        except ImportError:
            logger.debug("config.pyが見つかりません。基本チェックのみ実行")
            return
        
        # YAML設定ファイル読み込み
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "comment_restrictions.yaml"
        if not config_path.exists():
            logger.debug("comment_restrictions.yaml が見つかりません。基本チェックのみ実行")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.restrictions = self.yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"設定ファイル読み込み時のエラー: {e}")
    
    def should_exclude_weather_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """天気コメントを除外すべきかチェック（YAML設定ベース）"""
        if not self.yaml or not self.restrictions or not self.weather_constants:
            return False
        
        try:
            # 天気条件による除外チェック
            weather_desc = weather_data.weather_description.lower()
            
            # 雨天時のチェック
            if any(keyword in weather_desc for keyword in ['雨', 'rain']):
                precip_thresh = self.weather_constants.precipitation
                if weather_data.precipitation >= precip_thresh.HEAVY_RAIN:
                    forbidden_list = self.restrictions.get('weather_restrictions', {}).get('heavy_rain', {}).get('weather_comment_forbidden', [])
                else:
                    forbidden_list = self.restrictions.get('weather_restrictions', {}).get('rain', {}).get('weather_comment_forbidden', [])
                
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"雨天時の禁止ワード「{forbidden}」でコメント除外: {comment_text}")
                        return True
            
            # 晴天時のチェック
            elif any(keyword in weather_desc for keyword in ['晴', 'clear', 'sunny']):
                forbidden_list = self.restrictions.get('weather_restrictions', {}).get('sunny', {}).get('weather_comment_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"晴天時の禁止ワード「{forbidden}」でコメント除外: {comment_text}")
                        return True
            
            # 曇天時のチェック
            elif any(keyword in weather_desc for keyword in ['曇', 'cloud']):
                forbidden_list = self.restrictions.get('weather_restrictions', {}).get('cloudy', {}).get('weather_comment_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"曇天時の禁止ワード「{forbidden}」でコメント除外: {comment_text}")
                        return True
            
            # 気温による除外チェック
            temp = weather_data.temperature
            temp_restrictions = self.restrictions.get('temperature_restrictions', {})
            temp_thresh = self.weather_constants.temperature
            
            if temp >= temp_thresh.HOT_WEATHER:
                forbidden_list = temp_restrictions.get('hot_weather', {}).get('forbidden_keywords', [])
            elif temp < temp_thresh.COLD_COMMENT_THRESHOLD:
                forbidden_list = temp_restrictions.get('cold_weather', {}).get('forbidden_keywords', [])
            else:
                forbidden_list = temp_restrictions.get('mild_weather', {}).get('forbidden_keywords', [])
            
            for forbidden in forbidden_list:
                if forbidden in comment_text:
                    logger.debug(f"気温条件「{temp}°C」で禁止ワード「{forbidden}」によりコメント除外: {comment_text}")
                    return True
            
            # 湿度による除外チェック
            humidity = weather_data.humidity
            humidity_restrictions = self.restrictions.get('humidity_restrictions', {})
            humidity_thresh = self.weather_constants.humidity
            
            if humidity >= humidity_thresh.HIGH_HUMIDITY:
                forbidden_list = humidity_restrictions.get('high_humidity', {}).get('forbidden_keywords', [])
            elif humidity < humidity_thresh.LOW_HUMIDITY:
                forbidden_list = humidity_restrictions.get('low_humidity', {}).get('forbidden_keywords', [])
            else:
                forbidden_list = []
            
            for forbidden in forbidden_list:
                if forbidden in comment_text:
                    logger.debug(f"湿度条件「{humidity}%」で禁止ワード「{forbidden}」によりコメント除外: {comment_text}")
                    return True
            
            return False
        
        except (KeyError, TypeError) as e:
            logger.error(f"データエラー: {e}")
            return False    
        except Exception as e:
            logger.warning(f"YAML設定チェック中にエラー: {e}")
            return False
    
    def should_exclude_advice_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """アドバイスコメントを除外すべきかチェック（YAML設定ベース）"""
        if not self.yaml or not self.restrictions or not self.weather_constants:
            return False
        
        try:
            # 天気条件による除外チェック
            weather_desc = weather_data.weather_description.lower()
            
            # 雨天時のチェック
            if any(keyword in weather_desc for keyword in ['雨', 'rain']):
                precip_thresh = self.weather_constants.precipitation
                if weather_data.precipitation >= precip_thresh.HEAVY_RAIN:
                    forbidden_list = self.restrictions.get('weather_restrictions', {}).get('heavy_rain', {}).get('advice_forbidden', [])
                else:
                    forbidden_list = self.restrictions.get('weather_restrictions', {}).get('rain', {}).get('advice_forbidden', [])
                
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"雨天時の禁止ワード「{forbidden}」でアドバイス除外: {comment_text}")
                        return True
            
            # 晴天時のチェック
            elif any(keyword in weather_desc for keyword in ['晴', 'clear', 'sunny']):
                forbidden_list = self.restrictions.get('weather_restrictions', {}).get('sunny', {}).get('advice_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"晴天時の禁止ワード「{forbidden}」でアドバイス除外: {comment_text}")
                        return True
            
            # 曇天時のチェック
            elif any(keyword in weather_desc for keyword in ['曇', 'cloud']):
                forbidden_list = self.restrictions.get('weather_restrictions', {}).get('cloudy', {}).get('advice_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"曇天時の禁止ワード「{forbidden}」でアドバイス除外: {comment_text}")
                        return True
            
            return False
        
        except (KeyError, TypeError) as e:
            logger.error(f"データエラー: {e}")
            return False    
        except Exception as e:
            logger.warning(f"YAML設定チェック中にエラー: {e}")
            return False
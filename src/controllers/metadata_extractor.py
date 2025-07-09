"""メタデータ抽出モジュール"""

import logging
from datetime import datetime
from typing import Dict
import pytz

from src.types import LocationResult, GenerationMetadata

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """結果からメタデータを抽出するクラス"""
    
    @staticmethod
    def format_forecast_time(forecast_time: str) -> str:
        """予報時刻をフォーマット"""
        try:
            # UTC時刻をパース
            dt = datetime.fromisoformat(forecast_time.replace('Z', '+00:00'))
            # JSTに変換
            jst = pytz.timezone('Asia/Tokyo')
            dt_jst = dt.astimezone(jst)
            return dt_jst.strftime('%Y年%m月%d日 %H時')
        except Exception as e:
            logger.warning(f"予報時刻のパース失敗: {e}, forecast_time={forecast_time}")
            return forecast_time
    
    @staticmethod
    def extract_weather_metadata(result: LocationResult) -> Dict[str, str | float | None]:
        """結果から天気メタデータを抽出"""
        metadata: Dict[str, str | float | None] = {}
        
        if result.get('result') and result['result'].get('generation_metadata'):
            gen_metadata: GenerationMetadata = result['result']['generation_metadata']
            
            # 基本情報
            metadata['forecast_time'] = gen_metadata.get('forecast_time')
            metadata['temperature'] = gen_metadata.get('temperature')
            metadata['weather_condition'] = gen_metadata.get('weather_condition')
            metadata['wind_speed'] = gen_metadata.get('wind_speed')
            metadata['humidity'] = gen_metadata.get('humidity')
            
            # 選択されたコメント情報
            selection_meta = gen_metadata.get('selection_metadata', {})
            if selection_meta:
                metadata['selected_weather_comment'] = selection_meta.get('selected_weather_comment')
                metadata['selected_advice_comment'] = selection_meta.get('selected_advice_comment')
                metadata['llm_provider'] = selection_meta.get('llm_provider')
        
        return metadata
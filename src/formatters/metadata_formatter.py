"""
メタデータフォーマッター
"""

from __future__ import annotations
from typing import Any
import logging
from datetime import datetime

from src.data.comment_generation_state import CommentGenerationState
from .weather_timeline_formatter import WeatherTimelineFormatter

logger = logging.getLogger(__name__)


class MetadataFormatter:
    """生成メタデータをフォーマットするクラス"""
    
    def __init__(self):
        self.weather_timeline_formatter = WeatherTimelineFormatter()
    
    def create_generation_metadata(
        self, state: CommentGenerationState, execution_time_ms: int
    ) -> dict[str, Any]:
        """
        生成メタデータを作成
        """
        metadata = {
            "execution_time_ms": execution_time_ms,
            "retry_count": state.retry_count,
            "request_id": state.generation_metadata.get("execution_context", {}).get(
                "request_id", "unknown"
            ),
            "generation_timestamp": datetime.now().isoformat(),
            "location_name": state.location_name,
            "target_datetime": state.target_datetime.isoformat() if state.target_datetime else None,
            "llm_provider": state.llm_provider or "none",
        }
        
        # 天気情報の追加
        weather_data = state.weather_data
        if weather_data:
            weather_info = self._format_weather_info(weather_data, state.location_name, state)
            if weather_info:
                logger.debug(f"weather_info keys before update: {list(weather_info.keys())}")
                if 'weather_timeline' in weather_info:
                    logger.info(f"weather_timeline is in weather_info! future_forecasts count: {len(weather_info['weather_timeline'].get('future_forecasts', []))}")
                metadata.update(weather_info)
                logger.debug(f"metadata keys after weather_info update: {list(metadata.keys())}")
        
        # 選択されたコメント情報
        selected_pair = state.selected_pair
        if selected_pair:
            metadata["selected_past_comments"] = self._extract_selected_comments(selected_pair)
            metadata["similarity_score"] = getattr(selected_pair, "similarity_score", 0.0)
            metadata["selection_reason"] = getattr(selected_pair, "selection_reason", "")
        
        # 検証結果
        validation_result = state.validation_result
        if validation_result:
            metadata["validation_passed"] = getattr(validation_result, "is_valid", False)
            metadata["validation_score"] = getattr(validation_result, "total_score", 0.0)
        
        # エラーと警告
        if state.errors:
            metadata["errors"] = state.errors
        if state.warnings:
            metadata["warnings"] = state.warnings
        
        # ユーザー設定
        user_preferences = state.generation_metadata.get("user_preferences", {})
        if user_preferences:
            metadata["style"] = user_preferences.get("style", "casual")
            metadata["length"] = user_preferences.get("length", "medium")
        
        # 最終確認
        logger.info(f"Final metadata keys: {list(metadata.keys())}")
        if 'weather_timeline' in metadata:
            logger.info("weather_timeline is in final metadata!")
        else:
            logger.warning("weather_timeline NOT in final metadata!")
        
        return metadata
    
    def _get_weather_pattern(self, forecasts: list[dict[str, Any]]) -> str:
        """天気パターンを簡易分析"""
        if not forecasts:
            return "データなし"
        
        weather_conditions = [f["weather"] for f in forecasts]
        
        # 雨や悪天候のチェック
        has_rain = any("雨" in w for w in weather_conditions)
        has_snow = any("雪" in w for w in weather_conditions)
        
        if has_snow:
            return "雪の予報あり"
        elif has_rain:
            return "雨の予報あり"
        elif len(set(weather_conditions)) == 1:
            return "安定した天気"
        else:
            return "変わりやすい天気"
    
    def _format_weather_info(self, weather_data: Any, location_name: str | None, state: CommentGenerationState) -> dict[str, Any]:
        """天気情報をフォーマット"""
        weather_info = {}
        
        # 天気状況（有効な値のみ追加）
        weather_condition = getattr(weather_data, "weather_description", None)
        if weather_condition and weather_condition != "不明":
            weather_info["weather_condition"] = weather_condition
        
        # 気温（有効な値のみ追加）
        temperature = getattr(weather_data, "temperature", None)
        if temperature is not None:
            weather_info["temperature"] = temperature
        
        # 湿度（有効な値のみ追加）
        humidity = getattr(weather_data, "humidity", None)
        if humidity is not None:
            weather_info["humidity"] = humidity
        
        # 風速（有効な値のみ追加）
        wind_speed = getattr(weather_data, "wind_speed", None)
        if wind_speed is not None:
            weather_info["wind_speed"] = wind_speed
        
        # 天気データの時刻（予報時刻）
        weather_datetime = getattr(weather_data, "datetime", None)
        if weather_datetime is not None:
            weather_info["weather_forecast_time"] = weather_datetime.isoformat()
            
            # 時系列の天気データを追加
            # period_forecastsから直接タイムラインを作成
            period_forecasts = state.generation_metadata.get("period_forecasts", [])
            logger.debug(f"period_forecasts type: {type(period_forecasts)}, length: {len(period_forecasts) if period_forecasts else 0}")
            if period_forecasts:
                logger.debug(f"First forecast type: {type(period_forecasts[0]) if period_forecasts else 'empty'}")
                try:
                    timeline_data = {
                        "future_forecasts": [],
                        "past_forecasts": [],
                        "base_time": weather_datetime.isoformat()
                    }
                    
                    # period_forecastsをタイムライン形式に変換
                    for forecast in period_forecasts:
                        # オブジェクトか辞書かを判定
                        if hasattr(forecast, 'datetime'):
                            # WeatherForecastオブジェクトの場合
                            timeline_data["future_forecasts"].append({
                                "time": forecast.datetime.strftime("%m/%d %H:%M"),
                                "label": forecast.datetime.strftime("%H:%M"),
                                "weather": forecast.weather_description,
                                "temperature": forecast.temperature,
                                "precipitation": forecast.precipitation
                            })
                        elif isinstance(forecast, dict):
                            # 辞書の場合
                            timeline_data["future_forecasts"].append({
                                "time": forecast.get('datetime', ''),
                                "label": forecast.get('datetime', '')[-5:] if forecast.get('datetime') else '',
                                "weather": forecast.get('weather_description', ''),
                                "temperature": forecast.get('temperature', 0),
                                "precipitation": forecast.get('precipitation', 0)
                            })
                    
                    # サマリー情報を追加
                    if timeline_data["future_forecasts"]:
                        temps = [f["temperature"] for f in timeline_data["future_forecasts"]]
                        precipitations = [f["precipitation"] for f in timeline_data["future_forecasts"]]
                        
                        timeline_data["summary"] = {
                            "temperature_range": f"{min(temps):.1f}°C〜{max(temps):.1f}°C",
                            "max_precipitation": f"{max(precipitations):.1f}mm",
                            "weather_pattern": self._get_weather_pattern(timeline_data["future_forecasts"])
                        }
                    
                    weather_info["weather_timeline"] = timeline_data
                    logger.info(
                        f"period_forecastsから時系列データを作成: {len(timeline_data['future_forecasts'])}件"
                    )
                except Exception as e:
                    logger.warning(f"時系列データ作成エラー: {e}")
                    weather_info["weather_timeline"] = {"error": str(e)}
        
        return weather_info
    
    def _extract_selected_comments(self, selected_pair: Any) -> list[dict[str, str]]:
        """
        選択されたコメント情報を抽出
        """
        comments = []
        
        # 天気コメント
        weather_comment = getattr(selected_pair, "weather_comment", None)
        if weather_comment and hasattr(weather_comment, "comment_text"):
            comment_dict = {
                "text": weather_comment.comment_text,
                "type": "weather_comment",
            }
            
            # 気温（有効な値のみ追加）
            temperature = getattr(weather_comment, "temperature", None)
            if temperature is not None:
                comment_dict["temperature"] = temperature
            
            # 天気状況（有効な値のみ追加）
            weather_condition = getattr(weather_comment, "weather_condition", None)
            if weather_condition and weather_condition != "不明":
                comment_dict["weather_condition"] = weather_condition
            
            comments.append(comment_dict)
        
        # アドバイスコメント
        advice_comment = getattr(selected_pair, "advice_comment", None)
        if advice_comment and hasattr(advice_comment, "comment_text"):
            comment_dict = {
                "text": advice_comment.comment_text,
                "type": "advice",
            }
            
            # 気温（有効な値のみ追加）
            temperature = getattr(advice_comment, "temperature", None)
            if temperature is not None:
                comment_dict["temperature"] = temperature
            
            # 天気状況（有効な値のみ追加）
            weather_condition = getattr(advice_comment, "weather_condition", None)
            if weather_condition and weather_condition != "不明":
                comment_dict["weather_condition"] = weather_condition
            
            comments.append(comment_dict)
        
        return comments
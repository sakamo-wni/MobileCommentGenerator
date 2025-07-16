"""
Rain comment selection strategy

雨に関連するコメント選択戦略
"""

from __future__ import annotations

import logging
from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast
from src.data.comment_generation_state import CommentGenerationState
from src.constants.weather_constants import COMMENT

logger = logging.getLogger(__name__)


class RainCommentStrategy:
    """雨に関連するコメント選択戦略"""
    
    @staticmethod
    def find_rain_appropriate_weather_comment(
        comments: list[PastComment],
        weather_data: WeatherForecast,
        state: CommentGenerationState | None = None
    ) -> PastComment | None:
        """雨に適した天気コメントを探す（降水量に応じた表現の妥当性をチェック）"""
        rain_keywords = ["雨", "降水", "にわか雨", "傘"]
        
        # 連続雨かどうかを判定
        is_continuous_rain = False
        rain_hours = 0
        period_forecasts = None
        
        # metadataからperiod_forecastsを取得
        if state and hasattr(state, 'generation_metadata') and state.generation_metadata:
            period_forecasts = state.generation_metadata.get('period_forecasts', [])
        
        if period_forecasts:
            # 天気が「雨」または降水量が0.1mm以上の時間をカウント
            rain_hours = sum(1 for f in period_forecasts 
                           if (hasattr(f, 'weather') and f.weather == "雨") or 
                              (hasattr(f, 'precipitation') and f.precipitation >= 0.1))
            is_continuous_rain = rain_hours >= COMMENT.CONTINUOUS_RAIN_HOURS
            
            if is_continuous_rain:
                logger.info(f"連続雨を検出: {rain_hours}時間の雨（9,12,15,18時）")
                # デバッグ用：各時間の天気情報をログ出力
                for f in period_forecasts:
                    # datetimeの安全な処理
                    if hasattr(f, 'datetime') and hasattr(f.datetime, 'strftime'):
                        time_str = f.datetime.strftime('%H時')
                    else:
                        time_str = '不明'
                    weather = f.weather if hasattr(f, 'weather') else '不明'
                    precip = f.precipitation if hasattr(f, 'precipitation') else 0
                    logger.debug(f"  {time_str}: {weather}, 降水量{precip}mm")
        
        # 降水量に基づく不適切な表現のチェック
        for comment in comments:
            if any(keyword in comment.comment_text for keyword in rain_keywords):
                # 降水量が10mm/h未満の場合、強雨表現は不適切
                if weather_data.precipitation < 10.0:
                    strong_rain_expressions = ["強雨", "激しい雨", "土砂降り", "豪雨", "大雨", "どしゃ降り", "ザーザー"]
                    if any(expr in comment.comment_text for expr in strong_rain_expressions):
                        logger.debug(f"降水量{weather_data.precipitation}mm/hに対して過度な表現のためスキップ: {comment.comment_text}")
                        continue
                
                # 降水量が5mm/h未満の場合、中程度の雨表現も不適切
                if weather_data.precipitation < 5.0:
                    moderate_rain_expressions = ["本降り", "しっかりとした雨", "まとまった雨"]
                    if any(expr in comment.comment_text for expr in moderate_rain_expressions):
                        logger.debug(f"降水量{weather_data.precipitation}mm/hに対して中程度の表現のためスキップ: {comment.comment_text}")
                        continue
                
                # 降水量が1mm/h未満の場合、一般的な雨表現も慎重に
                if weather_data.precipitation < 1.0:
                    light_rain_allowed = ["小雨", "パラパラ", "ぱらぱら", "弱い雨", "にわか雨", "通り雨"]
                    # 軽い雨の表現のみ許可
                    if not any(expr in comment.comment_text for expr in light_rain_allowed):
                        # 強い雨の表現でもなく、軽い雨の表現でもない場合はスキップ
                        if "雨" in comment.comment_text and not any(x in comment.comment_text for x in ["傘", "雨具"]):
                            logger.debug(f"降水量{weather_data.precipitation}mm/hに対して不適切な雨表現のためスキップ: {comment.comment_text}")
                            continue
                
                # 連続雨の場合の特別な処理
                if is_continuous_rain:
                    continuous_rain_positive = ["一日中", "長時間", "続く", "終日", "ずっと"]
                    if any(expr in comment.comment_text for expr in continuous_rain_positive):
                        logger.info(f"連続雨に適したコメントを優先選択: '{comment.comment_text}'")
                        return comment
                else:
                    # 連続雨でない場合、「一日中」などの表現は不適切
                    continuous_rain_negative = ["一日中", "終日", "ずっと雨"]
                    if any(expr in comment.comment_text for expr in continuous_rain_negative):
                        logger.debug(f"連続雨でないため不適切: {comment.comment_text}")
                        continue
                
                logger.info(f"雨関連コメント選択: '{comment.comment_text}'")
                return comment
        
        return None
    
    @staticmethod
    def find_rain_appropriate_advice_comment(
        comments: list[PastComment],
        weather_data: WeatherForecast,
        state: CommentGenerationState | None = None
    ) -> PastComment | None:
        """雨に適したアドバイスコメントを探す"""
        rain_keywords = ["傘", "雨具", "レインコート", "雨", "濡れ"]
        
        # metadataからperiod_forecastsを取得して連続雨を判定
        is_continuous_rain = False
        if state and hasattr(state, 'generation_metadata') and state.generation_metadata:
            period_forecasts = state.generation_metadata.get('period_forecasts', [])
            if period_forecasts:
                rain_hours = sum(1 for f in period_forecasts 
                               if (hasattr(f, 'weather') and f.weather == "雨") or 
                                  (hasattr(f, 'precipitation') and f.precipitation >= 0.1))
                is_continuous_rain = rain_hours >= COMMENT.CONTINUOUS_RAIN_HOURS
        
        for comment in comments:
            if any(keyword in comment.comment_text for keyword in rain_keywords):
                # 連続雨の場合の特別な処理
                if is_continuous_rain:
                    continuous_advice_positive = ["一日中", "長時間", "しっかり", "完全防水", "替えの"]
                    if any(expr in comment.comment_text for expr in continuous_advice_positive):
                        logger.info(f"連続雨に適したアドバイスを優先選択: '{comment.comment_text}'")
                        return comment
                
                # 降水量に応じたアドバイスの妥当性チェック
                if weather_data.precipitation < 1.0:
                    # 小雨の場合、過度な雨対策は不要
                    excessive_protection = ["完全防水", "長靴", "カッパ", "ずぶ濡れ"]
                    if any(expr in comment.comment_text for expr in excessive_protection):
                        logger.debug(f"小雨（{weather_data.precipitation}mm/h）に対して過度な対策のためスキップ: {comment.comment_text}")
                        continue
                
                logger.info(f"雨関連アドバイス選択: '{comment.comment_text}'")
                return comment
        
        return None
"""
天気予報統合ノード

LangGraphノードとして天気予報データの取得・処理を行う
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, START, StateGraph

from src.apis.wxtech_client import WxTechAPIClient, WxTechAPIError
from src.data.location_manager import LocationManager
from src.data.weather_data import WeatherForecast, WeatherForecastCollection
from src.data.weather_trend import WeatherTrend
from src.data.forecast_cache import save_forecast_to_cache, get_temperature_differences
from src.config.weather_config import get_config
from src.config.comment_config import get_comment_config

# ログ設定
logger = logging.getLogger(__name__)


class WeatherForecastNode:
    """天気予報統合ノード

    天気予報データの取得、処理、コメント生成への統合を行う
    """

    def __init__(self, api_key: str):
        """天気予報ノードを初期化

        Args:
            api_key: WxTech API キー
        """
        self.api_key = api_key
        self.location_manager = LocationManager()

    async def get_weather_forecast(self, state: dict[str, Any]) -> dict[str, Any]:
        """天気予報データを取得するノード

        Args:
            state: LangGraphの状態辞書
                - location: 地点名または緯度経度
                - forecast_hours: 予報時間数（デフォルト: 24）

        Returns:
            更新された状態辞書
                - weather_data: 天気予報データ
                - weather_summary: 天気概要
                - error_message: エラーメッセージ（エラー時のみ）
        """
        try:
            location = state.get("location")
            forecast_hours = state.get("forecast_hours", 24)

            if not location:
                return {**state, "error_message": "地点情報が指定されていません"}

            # 天気予報データを取得
            weather_collection = await self._fetch_weather_data(location)

            if not weather_collection or not weather_collection.forecasts:
                return {
                    **state,
                    "error_message": f"地点「{location}」の天気予報データを取得できませんでした",
                }

            # 指定時間内の予報データをフィルタリング
            filtered_forecasts = self._filter_forecasts_by_hours(
                weather_collection.forecasts,
                forecast_hours,
            )

            # 天気概要を生成
            weather_summary = self._generate_weather_summary(filtered_forecasts)

            return {
                **state,
                "weather_data": {
                    "location": weather_collection.location,
                    "forecasts": [f.to_dict() for f in filtered_forecasts],
                    "generated_at": weather_collection.generated_at.isoformat(),
                    "summary": weather_collection.get_daily_summary(),
                },
                "weather_summary": weather_summary,
                "error_message": None,
            }

        except Exception as e:
            logger.error(f"天気予報データ取得エラー: {e!s}")
            return {**state, "error_message": f"天気予報データの取得に失敗しました: {e!s}"}

    async def _fetch_weather_data(
        self,
        location: str | tuple,
    ) -> WeatherForecastCollection | None:
        """天気予報データを取得

        Args:
            location: 地点名または(緯度, 経度)のタプル

        Returns:
            天気予報コレクション
        """
        try:
            with WxTechAPIClient(self.api_key) as client:
                if isinstance(location, str):
                    # 地点名から座標を取得
                    location_obj = self.location_manager.find_exact_match(location)
                    if not location_obj or location_obj.latitude is None or location_obj.longitude is None:
                        # 地点検索を試行
                        search_results = self.location_manager.search_location(location)
                        if search_results:
                            location_obj = search_results[0]
                        else:
                            raise ValueError(f"地点「{location}」が見つかりません")

                    return await client.get_forecast_async(
                        location_obj.latitude,
                        location_obj.longitude,
                    )

                if isinstance(location, tuple) and len(location) == 2:
                    # 緯度経度から直接取得
                    lat, lon = location
                    return await client.get_forecast_async(lat, lon)

                raise ValueError("無効な地点情報です")

        except WxTechAPIError as e:
            logger.error(f"WxTech API エラー: {e!s}")
            raise
        except Exception as e:
            logger.error(f"天気予報データ取得エラー: {e!s}")
            raise

    def _filter_forecasts_by_hours(
        self,
        forecasts: list[WeatherForecast],
        hours: int,
    ) -> list[WeatherForecast]:
        """指定時間内の予報データをフィルタリング

        Args:
            forecasts: 天気予報リスト
            hours: 予報時間数

        Returns:
            フィルタリングされた天気予報リスト
        """
        if hours <= 0:
            return forecasts

        now = datetime.now()
        cutoff_time = now + timedelta(hours=hours)

        return [forecast for forecast in forecasts if forecast.datetime <= cutoff_time]

    def _generate_weather_summary(self, forecasts: list[WeatherForecast]) -> dict[str, Any]:
        """天気概要を生成

        Args:
            forecasts: 天気予報リスト

        Returns:
            天気概要辞書
        """
        if not forecasts:
            return {}

        # 指定時間後の天気
        from src.config.weather_config import WeatherConfig
        config = WeatherConfig()
        target_time = datetime.now() + timedelta(hours=config.forecast_hours_ahead)
        current_forecast = min(
            forecasts,
            key=lambda f: abs((f.datetime - target_time).total_seconds()),
        )
        
        # デバッグ情報
        logger.info(f"_generate_weather_summary - ターゲット時刻: {target_time}, 選択された予報時刻: {current_forecast.datetime}")
        logger.info(f"_generate_weather_summary - 選択された天気データ: {current_forecast.temperature}°C, {current_forecast.weather_description}")

        # 気温統計
        temperatures = [f.temperature for f in forecasts]
        precipitations = [f.precipitation for f in forecasts]

        # 天気パターン分析
        weather_conditions = [f.weather_condition for f in forecasts]
        condition_counts = {}
        for condition in weather_conditions:
            condition_counts[condition.value] = condition_counts.get(condition.value, 0) + 1

        # 主要な天気状況
        dominant_condition = max(condition_counts.items(), key=lambda x: x[1])

        # 雨の予測
        rain_forecasts = [f for f in forecasts if f.precipitation > 0.1]
        rain_probability = len(rain_forecasts) / len(forecasts) if forecasts else 0

        # 悪天候の判定
        severe_weather_forecasts = [f for f in forecasts if f.is_severe_weather()]
        has_severe_weather = len(severe_weather_forecasts) > 0

        return {
            "current_weather": {
                "temperature": current_forecast.temperature,
                "condition": current_forecast.weather_condition.value,
                "description": current_forecast.weather_description,
                "precipitation": current_forecast.precipitation,
                "comfort_level": current_forecast.get_comfort_level(),
            },
            "temperature_range": {
                "max": max(temperatures),
                "min": min(temperatures),
                "average": sum(temperatures) / len(temperatures),
            },
            "precipitation": {
                "total": sum(precipitations),
                "max_hourly": max(precipitations),
                "probability": rain_probability * 100,
            },
            "dominant_condition": {
                "condition": dominant_condition[0],
                "frequency": dominant_condition[1] / len(forecasts),
            },
            "alerts": {
                "has_severe_weather": has_severe_weather,
                "severe_weather_count": len(severe_weather_forecasts),
                "high_precipitation": max(precipitations) > 10.0,
                "extreme_temperature": any(t < 0 or t > 35 for t in temperatures),
            },
            "recommendations": self._generate_recommendations(forecasts),
        }

    def _generate_recommendations(self, forecasts: list[WeatherForecast]) -> list[str]:
        """天気に基づく推奨事項を生成

        Args:
            forecasts: 天気予報リスト

        Returns:
            推奨事項のリスト
        """
        recommendations = []

        if not forecasts:
            return recommendations

        # 雨の予測チェック
        rain_forecasts = [f for f in forecasts if f.precipitation > 0.1]
        if rain_forecasts:
            max_precipitation = max(f.precipitation for f in rain_forecasts)
            if max_precipitation > 10.0:
                recommendations.append("傘の携帯をおすすめします（強い雨の予報）")
            else:
                recommendations.append("念のため傘をお持ちください")

        # 気温チェック
        temperatures = [f.temperature for f in forecasts]
        max_temp = max(temperatures)
        min_temp = min(temperatures)

        if max_temp > 30:
            recommendations.append("暑くなる予報です。水分補給や熱中症対策をお忘れなく")
        elif max_temp < 5:
            recommendations.append("寒くなる予報です。防寒対策をしっかりと")
        elif min_temp < 0:
            recommendations.append("氷点下になる可能性があります。路面凍結にご注意ください")

        # 風速チェック
        strong_winds = [f for f in forecasts if f.wind_speed > 10.0]
        if strong_winds:
            recommendations.append("強風の予報があります。外出時はご注意ください")

        # 悪天候チェック
        severe_weather = [f for f in forecasts if f.is_severe_weather()]
        if severe_weather:
            recommendations.append("悪天候の予報があります。不要な外出は控えることをおすすめします")

        # 良い天気の場合
        good_weather = [f for f in forecasts if f.is_good_weather()]
        if len(good_weather) > len(forecasts) * 0.7:  # 70%以上が良い天気
            recommendations.append("良い天気が続く予報です。外出日和ですね")

        return recommendations


def create_weather_forecast_graph(api_key: str) -> StateGraph:
    """天気予報統合のLangGraphを作成

    Args:
        api_key: WxTech API キー

    Returns:
        天気予報統合のグラフ
    """
    # ノードインスタンス作成
    weather_node = WeatherForecastNode(api_key)

    # グラフ定義
    graph = StateGraph(dict[str, Any])

    # ノード追加
    graph.add_node("get_weather", weather_node.get_weather_forecast)

    # エッジ追加
    graph.add_edge(START, "get_weather")
    graph.add_edge("get_weather", END)

    return graph


# 単体でも使用可能な関数
async def get_weather_forecast_for_location(
    location: str | tuple,
    api_key: str,
    forecast_hours: int = 24,
) -> dict[str, Any]:
    """指定地点の天気予報を取得（単体使用可能）

    Args:
        location: 地点名または(緯度, 経度)
        api_key: WxTech API キー
        forecast_hours: 予報時間数

    Returns:
        天気予報データ
    """
    weather_node = WeatherForecastNode(api_key)

    state = {"location": location, "forecast_hours": forecast_hours}

    result = await weather_node.get_weather_forecast(state)
    return result


# メッセージベースの統合関数
async def integrate_weather_into_conversation(
    messages: list[BaseMessage],
    location: str | tuple,
    api_key: str,
) -> list[BaseMessage]:
    """会話に天気情報を統合

    Args:
        messages: 会話メッセージのリスト
        location: 地点名または座標
        api_key: WxTech API キー

    Returns:
        天気情報が追加されたメッセージリスト
    """
    try:
        # 天気予報データを取得
        weather_data = await get_weather_forecast_for_location(location, api_key)

        if weather_data.get("error_message"):
            # エラー時は元のメッセージをそのまま返す
            return messages

        # 天気情報メッセージを作成
        weather_summary = weather_data.get("weather_summary", {})
        current_weather = weather_summary.get("current_weather", {})
        recommendations = weather_summary.get("recommendations", [])

        weather_message_content = f"""
現在の天気情報:
- 地点: {weather_data["weather_data"]["location"]}
- 気温: {current_weather.get("temperature", "N/A")}°C
- 天気: {current_weather.get("description", "N/A")}
- 快適度: {current_weather.get("comfort_level", "N/A")}

推奨事項:
{chr(10).join(f"- {rec}" for rec in recommendations) if recommendations else "- 特になし"}
"""

        weather_message = AIMessage(
            content=weather_message_content.strip(),
            additional_kwargs={"weather_data": weather_data},
        )

        # 天気情報を会話に追加
        return messages + [weather_message]

    except Exception as e:
        logger.error(f"天気情報統合エラー: {e!s}")
        # エラー時は元のメッセージをそのまま返す
        return messages


# ワークフロー用の関数
def fetch_weather_forecast_node(state):
    """ワークフロー用の天気予報取得ノード関数（同期版）

    Args:
        state: CommentGenerationState

    Returns:
        更新されたCommentGenerationState
    """
    import logging
    import os

    from src.data.location_manager import get_location_manager

    logger = logging.getLogger(__name__)

    try:
        # 地点情報の取得
        location_name_raw = state.location_name
        if not location_name_raw:
            raise ValueError("location_name is required")

        # 地点名から座標を分離（"地点名,緯度,経度" 形式の場合）
        provided_lat = None
        provided_lon = None

        if "," in location_name_raw:
            parts = location_name_raw.split(",")
            location_name = parts[0].strip()
            if len(parts) >= 3:
                try:
                    provided_lat = float(parts[1].strip())
                    provided_lon = float(parts[2].strip())
                    logger.info(
                        f"Extracted location name '{location_name}' with coordinates ({provided_lat}, {provided_lon})",
                    )
                except ValueError:
                    logger.warning(
                        f"Invalid coordinates in '{location_name_raw}', will look up in LocationManager",
                    )
            else:
                logger.info(f"Extracted location name '{location_name}' from '{location_name_raw}'")
        else:
            location_name = location_name_raw.strip()

        # LocationManagerから地点データを取得
        location_manager = get_location_manager()
        location = location_manager.get_location(location_name)

        # LocationManagerで見つからない場合、提供された座標を使用
        if not location and provided_lat is not None and provided_lon is not None:
            logger.info(
                f"Location '{location_name}' not found in LocationManager, using provided coordinates",
            )
            # 疑似Locationオブジェクトを作成
            from src.data.location_manager import Location

            location = Location(
                name=location_name,
                normalized_name=location_name.lower(),
                latitude=provided_lat,
                longitude=provided_lon,
            )
        elif not location:
            error_msg = f"地点が見つかりません: {location_name}"
            logger.error(error_msg)
            state.add_error(error_msg, "weather_forecast")
            raise ValueError(error_msg)

        if not location.latitude or not location.longitude:
            error_msg = f"地点 '{location_name}' の緯度経度情報がありません"
            logger.error(error_msg)
            state.add_error(error_msg, "weather_forecast")
            raise ValueError(error_msg)

        lat, lon = location.latitude, location.longitude

        # APIキーの取得
        api_key = os.getenv("WXTECH_API_KEY")
        if not api_key:
            error_msg = "WXTECH_API_KEY環境変数が設定されていません。\n設定方法: export WXTECH_API_KEY='your-api-key' または .envファイルに記載"
            logger.error(error_msg)
            state.add_error(error_msg, "weather_forecast")
            raise ValueError(error_msg)

        # WxTech APIクライアントの初期化
        client = WxTechAPIClient(api_key)

        # 天気予報の取得
        try:
            forecast_collection = client.get_forecast(lat, lon)
        except WxTechAPIError as e:
            # エラータイプに基づいて適切なエラーメッセージを設定
            if e.error_type == 'api_key_invalid':
                error_msg = "気象APIキーが無効です。\nWXTECH_API_KEYが正しく設定されているか確認してください。"
            elif e.error_type == 'rate_limit':
                error_msg = "気象APIのレート制限に達しました。しばらく待ってから再試行してください。"
            elif e.error_type == 'network_error':
                error_msg = "気象APIサーバーに接続できません。ネットワーク接続を確認してください。"
            elif e.error_type == 'timeout':
                error_msg = f"気象APIへのリクエストがタイムアウトしました: {e}"
            elif e.error_type == 'server_error':
                error_msg = "気象APIサーバーでエラーが発生しました。しばらく待ってから再試行してください。"
            else:
                error_msg = f"気象API接続エラー: {e}"
            
            logger.error(f"気象APIエラー (type: {e.error_type}, status: {e.status_code}): {error_msg}")
            state.add_error(error_msg, "weather_forecast")
            raise

        # 設定から何時間後の予報を使用するか取得
        config = get_config()
        forecast_hours_ahead = config.weather.forecast_hours_ahead
        target_datetime = datetime.now() + timedelta(hours=forecast_hours_ahead)
        
        # 設定から気象変化分析期間を取得
        comment_config = get_comment_config()
        trend_hours = comment_config.trend_hours_ahead
        
        # 指定時間後から更に先の予報を取得（3時間ごと）
        import pytz
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        
        # 12-24時間の期間で予報を取得（3時間ごと）
        forecast_start = now_jst + timedelta(hours=forecast_hours_ahead)
        forecast_end = now_jst + timedelta(hours=forecast_hours_ahead + trend_hours)
        
        # 期間内の予報を抽出（3時間ごと）
        period_forecasts = []
        for forecast in forecast_collection.forecasts:
            # forecastのdatetimeがnaiveな場合はJSTとして扱う
            forecast_dt = forecast.datetime
            if forecast_dt.tzinfo is None:
                forecast_dt = jst.localize(forecast_dt)
            
            if forecast_start <= forecast_dt <= forecast_end:
                period_forecasts.append(forecast)
        
        # 期間内の予報から最も重要な天気条件を選択
        selected_forecast = _select_priority_forecast(period_forecasts, target_datetime)
        
        # 気象変化傾向の分析
        if len(period_forecasts) >= 2:
            weather_trend = WeatherTrend.from_forecasts(period_forecasts)
            state.update_metadata("weather_trend", weather_trend)
            logger.info(f"気象変化傾向: {weather_trend.get_summary()}")
        else:
            logger.warning(f"気象変化分析に十分な予報データがありません: {len(period_forecasts)}件")
        
        # デバッグ情報
        logger.info(f"fetch_weather_forecast_node - ターゲット時刻: {target_datetime}, 選択された予報時刻: {selected_forecast.datetime if selected_forecast else 'None'}")
        if selected_forecast:
            logger.info(f"fetch_weather_forecast_node - 選択された天気データ: {selected_forecast.temperature}°C, {selected_forecast.weather_description}")
            if selected_forecast.weather_condition.is_special_condition:
                logger.info(f"特殊気象条件が選択されました: {selected_forecast.weather_condition.value} (優先度: {selected_forecast.weather_condition.priority})")

        if not selected_forecast:
            error_msg = "指定時刻の天気予報データが取得できませんでした"
            logger.error(error_msg)
            state.add_error(error_msg, "weather_forecast")
            raise ValueError(error_msg)

        # 予報データをキャッシュに保存
        try:
            save_forecast_to_cache(selected_forecast, location_name)
            logger.info(f"予報データをキャッシュに保存: {location_name}")
        except Exception as e:
            logger.warning(f"キャッシュ保存に失敗: {e}")
            # キャッシュ保存の失敗は致命的エラーではないので続行

        # 気温差の計算（前日との比較、12時間前との比較）
        temperature_differences = {}
        try:
            temperature_differences = get_temperature_differences(selected_forecast, location_name)
            if temperature_differences.get("previous_day_diff") is not None:
                logger.info(f"前日との気温差: {temperature_differences['previous_day_diff']:.1f}℃")
            if temperature_differences.get("twelve_hours_ago_diff") is not None:
                logger.info(f"12時間前との気温差: {temperature_differences['twelve_hours_ago_diff']:.1f}℃")
            if temperature_differences.get("daily_range") is not None:
                logger.info(f"日較差: {temperature_differences['daily_range']:.1f}℃")
        except Exception as e:
            logger.warning(f"気温差の計算に失敗: {e}")
            # 気温差計算の失敗も致命的エラーではないので続行

        # 状態に追加
        state.weather_data = selected_forecast
        state.update_metadata("forecast_collection", forecast_collection)
        state.location = location
        state.update_metadata("location_coordinates", {"latitude": lat, "longitude": lon})
        state.update_metadata("temperature_differences", temperature_differences)

        logger.info(
            f"Weather forecast fetched for {location_name}: {selected_forecast.weather_description}",
        )

        return state

    except Exception as e:
        logger.error(f"Failed to fetch weather forecast: {e!s}")
        state.add_error(f"天気予報の取得に失敗しました: {e!s}", "weather_forecast")
        # エラーをそのまま再発生させて処理を停止
        raise


def _select_priority_forecast(forecasts, target_datetime):
    """期間内の予報から最も重要な気象条件を選択
    
    Args:
        forecasts: 期間内の予報リスト
        target_datetime: 基準となる目標日時
        
    Returns:
        選択された予報（特殊気象条件を優先）
    """
    if not forecasts:
        return None
    
    # 単一の予報の場合はそのまま返す
    if len(forecasts) == 1:
        return forecasts[0]
    
    # 特殊気象条件（雷、霧、嵐）を優先
    special_conditions = [f for f in forecasts if f.weather_condition.is_special_condition]
    if special_conditions:
        # 特殊気象条件の中で最も優先度が高いものを選択
        selected = max(special_conditions, key=lambda f: f.weather_condition.priority)
        logger.info(f"特殊気象条件を優先選択: {selected.weather_condition.value} ({selected.datetime})")
        return selected
    
    # 特殊気象条件がない場合、悪天候を優先
    severe_weather = [f for f in forecasts if f.is_severe_weather()]
    if severe_weather:
        # 悪天候の中で最も降水量が多いものを選択
        selected = max(severe_weather, key=lambda f: f.precipitation)
        logger.info(f"悪天候を優先選択: {selected.weather_description} ({selected.datetime})")
        return selected
    
    # 雨天を優先
    rainy_forecasts = [f for f in forecasts if f.precipitation > 0.1]
    if rainy_forecasts:
        # 雨天の中で最も降水量が多いものを選択
        selected = max(rainy_forecasts, key=lambda f: f.precipitation)
        logger.info(f"雨天を優先選択: {selected.weather_description} ({selected.datetime})")
        return selected
    
    # 晴れ以外の条件を優先
    non_clear_forecasts = [f for f in forecasts if f.weather_condition.value != "clear"]
    if non_clear_forecasts:
        # 晴れ以外の中で最も優先度が高いものを選択
        selected = max(non_clear_forecasts, key=lambda f: f.weather_condition.priority)
        logger.info(f"晴れ以外の条件を優先選択: {selected.weather_description} ({selected.datetime})")
        return selected
    
    # 全て晴れの場合は、目標時刻に最も近いものを選択
    selected = min(forecasts, key=lambda f: abs((f.datetime - target_datetime).total_seconds()))
    logger.info(f"目標時刻に最も近い予報を選択: {selected.weather_description} ({selected.datetime})")
    return selected


if __name__ == "__main__":
    # テスト用コード
    import os

    from dotenv import load_dotenv

    load_dotenv()

    async def test_weather_node():
        api_key = os.getenv("WXTECH_API_KEY")
        if not api_key:
            print("WXTECH_API_KEY環境変数が設定されていません")
            return

        # 東京の天気予報を取得
        result = await get_weather_forecast_for_location("東京", api_key)

        if result.get("error_message"):
            print(f"エラー: {result['error_message']}")
        else:
            print("天気予報データ取得成功:")
            print(f"地点: {result['weather_data']['location']}")
            print(f"現在の天気: {result['weather_summary']['current_weather']['description']}")
            print(f"気温: {result['weather_summary']['current_weather']['temperature']}°C")

            recommendations = result["weather_summary"]["recommendations"]
            if recommendations:
                print("推奨事項:")
                for rec in recommendations:
                    print(f"- {rec}")

    # テスト実行
    asyncio.run(test_weather_node())

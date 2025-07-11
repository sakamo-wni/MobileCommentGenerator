"""
天気予報統合ノード

LangGraphノードとして天気予報データの取得・処理を行う
巨大な関数を責務ごとのサービスに分割
"""

import asyncio
import logging
import os
import pytz
from datetime import datetime, timedelta
from typing import Any, Optional

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, START, StateGraph

from src.data.weather_trend import WeatherTrend
from src.data.weather_data import WeatherForecastCollection, WeatherForecast
from src.config.weather_config import get_config
from src.config.config import get_comment_config
from src.config.config_loader import load_config
from src.nodes.weather_forecast import WeatherDataFetcher, WeatherDataTransformer, WeatherDataValidator

# 新しいサービスクラスをインポート
from src.nodes.weather_forecast.services import (
    LocationService,
    WeatherAPIService,
    ForecastProcessingService,
    CacheService,
    TemperatureAnalysisService
)
from src.nodes.weather_forecast.service_factory import WeatherForecastServiceFactory

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
        self.data_fetcher = WeatherDataFetcher(api_key)
        self.data_transformer = WeatherDataTransformer()
        self.data_validator = WeatherDataValidator()

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
            weather_collection = await self.data_fetcher.fetch_weather_data(location)

            if not weather_collection or not weather_collection.forecasts:
                return {
                    **state,
                    "error_message": f"地点「{location}」の天気予報データを取得できませんでした",
                }

            # 指定時間内の予報データをフィルタリング
            filtered_forecasts = self.data_transformer.filter_forecasts_by_hours(
                weather_collection.forecasts,
                forecast_hours,
            )

            # 天気概要を生成
            weather_summary = self.data_transformer.generate_weather_summary(filtered_forecasts)

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


async def fetch_weather_forecast_node_async(
    state,
    service_factory: Optional[WeatherForecastServiceFactory] = None
):
    """非同期版: ワークフロー用の天気予報取得ノード関数

    巨大な関数を責務ごとのサービスに分割して実装
    
    Args:
        state: ワークフローの状態
        service_factory: サービスファクトリ（テスト用）
        
    Returns:
        更新された状態
    """
    try:
        # サービスファクトリの初期化
        if service_factory is None:
            config = get_config()
            weather_config = get_weather_config()
            api_key = os.getenv("WXTECH_API_KEY", "")
            service_factory = WeatherForecastServiceFactory(config, weather_config, api_key)
        
        # 各サービスを取得
        location_service = service_factory.get_location_service()
        weather_service = service_factory.get_weather_api_service()
        processor = service_factory.get_forecast_processor()
        cache_service = service_factory.get_cache_service()
        
        # 地点情報の取得
        location_name_raw = state.get("location", "")
        location_name, lat, lon = location_service.parse_location_input(location_name_raw)
        location = location_service.get_location_with_coordinates(location_name, lat, lon)
        
        # 天気予報データの取得（非同期版）
        forecast_collection = await weather_service.fetch_forecast_with_retry_async(
            location.latitude, 
            location.longitude,
            location.name
        )
        
        # 予報データの選択と最適化
        selected_forecast, forecasts_for_timeline = processor.select_forecast_with_priority(
            forecast_collection.forecasts
        )
        
        # タイムライン用データの抽出
        timeline_forecasts = processor.extract_forecasts_for_target_hours(
            forecast_collection,
            processor.target_date,
            processor.target_hours
        )
        
        # 天気傾向の分析
        weather_trend = processor.analyze_trend(timeline_forecasts)
        
        # キャッシュへの保存
        cache_service.save_forecasts(forecast_collection, location.name)
        
        # データの変換
        transformer = WeatherDataTransformer()
        transformed_data = transformer.transform_to_state_format(
            selected_forecast,
            forecasts_for_timeline,
            weather_trend,
            location
        )
        
        # ノード実行時間の記録
        metadata = state.get("generation_metadata", {})
        metadata["node_execution_times"] = metadata.get("node_execution_times", {})
        
        return {
            **state,
            **transformed_data,
            "generation_metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"天気予報データ取得エラー: {str(e)}", exc_info=True)
        return {
            **state,
            "error_message": f"天気予報データの取得に失敗しました: {str(e)}"
        }


def fetch_weather_forecast_node(
    state,
    service_factory: Optional[WeatherForecastServiceFactory] = None
):
    """ワークフロー用の天気予報取得ノード関数

    巨大な関数を責務ごとのサービスに分割して実装

    Args:
        state: CommentGenerationState

    Returns:
        更新されたCommentGenerationState
    """
    import logging
    import os

    logger = logging.getLogger(__name__)

    try:
        # === 1. 初期化フェーズ ===
        
        # 地点情報の取得
        location_name_raw = state.location_name
        if not location_name_raw:
            raise ValueError("location_name is required")
        
        # APIキーの取得
        api_key = os.getenv("WXTECH_API_KEY")
        if not api_key:
            error_msg = (
                "WXTECH_API_KEY環境変数が設定されていません。\n"
                "設定方法: export WXTECH_API_KEY='your-api-key' または .envファイルに記載"
            )
            logger.error(error_msg)
            state.add_error(error_msg, "weather_forecast")
            raise ValueError(error_msg)
        
        # サービスファクトリーの初期化
        if service_factory is None:
            service_factory = WeatherForecastServiceFactory()
            service_factory.set_api_key(api_key)
        
        # サービスの取得
        location_service = service_factory.get_location_service()
        weather_api_service = service_factory.get_weather_api_service()
        forecast_processing_service = service_factory.get_forecast_processing_service()
        cache_service = service_factory.get_cache_service()
        temperature_analysis_service = service_factory.get_temperature_analysis_service()
        
        # === 2. 地点情報の処理 ===
        
        # 地点名と座標を分離
        location_name, provided_lat, provided_lon = location_service.parse_location_string(
            location_name_raw
        )
        
        # 地点情報を取得
        try:
            location = location_service.get_location_with_coordinates(
                location_name, 
                provided_lat, 
                provided_lon
            )
        except ValueError as e:
            logger.error(str(e))
            state.add_error(str(e), "weather_forecast")
            raise
        
        lat, lon = location.latitude, location.longitude
        
        # === 3. 天気予報の取得 ===
        
        try:
            forecast_collection = weather_api_service.fetch_forecast_with_retry(
                lat, lon, location_name
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"天気予報取得エラー: {error_msg}")
            state.add_error(error_msg, "weather_forecast")
            raise
        
        # === 4. 予報データの処理 ===
        
        # 設定の読み込み
        config = get_config()
        forecast_hours_ahead = config.weather.forecast_hours_ahead
        target_datetime = datetime.now() + timedelta(hours=forecast_hours_ahead)
        
        comment_config = get_comment_config()
        trend_hours = comment_config.trend_hours_ahead
        
        # 対象日の計算
        weather_config = load_config('weather_thresholds', validate=False)
        date_boundary_hour = weather_config.get('generation', {}).get('date_boundary_hour', 6)
        
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = datetime.now(jst)
        target_date = forecast_processing_service.get_target_date(now_jst, date_boundary_hour)
        
        logger.info(f"対象日: {target_date} (現在時刻: {now_jst.strftime('%Y-%m-%d %H:%M')})")
        
        # 指定時刻の予報を抽出
        period_forecasts = forecast_processing_service.extract_period_forecasts(
            forecast_collection,
            target_date
        )
        
        # period_forecastsが空でないことを確認
        if not period_forecasts:
            error_msg = "指定時刻の天気予報データが取得できませんでした"
            logger.error(f"{error_msg} - period_forecasts is empty")
            state.add_error(error_msg, "weather_forecast")
            raise ValueError(error_msg)
        
        # 優先度に基づいて予報を選択（雨・猛暑日を優先）
        logger.info("優先度ベースの予報選択を開始")
        selected_forecast = forecast_processing_service.select_priority_forecast(
            period_forecasts
        )
        if selected_forecast:
            logger.info(
                f"優先度選択結果: {selected_forecast.datetime.strftime('%H:%M')} - "
                f"{selected_forecast.weather_description}, {selected_forecast.temperature}°C, "
                f"降水量{selected_forecast.precipitation}mm"
            )
        
        if not selected_forecast:
            error_msg = "指定時刻の天気予報データが取得できませんでした"
            logger.error(error_msg)
            state.add_error(error_msg, "weather_forecast")
            raise ValueError(error_msg)
        
        # デバッグ情報
        logger.info(
            f"fetch_weather_forecast_node - ターゲット時刻: {target_datetime}, "
            f"選択された予報時刻: {selected_forecast.datetime}"
        )
        logger.info(
            f"fetch_weather_forecast_node - 選択された天気データ: "
            f"{selected_forecast.temperature}°C, {selected_forecast.weather_description}"
        )
        
        if selected_forecast.weather_condition.is_special_condition:
            logger.info(
                f"特殊気象条件が選択されました: {selected_forecast.weather_condition.value} "
                f"(優先度: {selected_forecast.weather_condition.priority})"
            )
        
        # === 5. 追加処理 ===
        
        # 4時点の予報データをstateに保存（コメント選択時に使用）
        state.update_metadata("period_forecasts", period_forecasts)
        logger.info(f"4時点の予報データを保存: {len(period_forecasts)}件")
        
        # デバッグ: 保存した予報データの詳細をログ出力
        for forecast in period_forecasts:
            logger.info(
                f"  - {forecast.datetime.strftime('%H:%M')}: {forecast.weather_description}, "
                f"{forecast.temperature}°C, 降水量{forecast.precipitation}mm"
            )
        
        # 気象変化傾向の分析
        weather_trend = forecast_processing_service.analyze_weather_trend(period_forecasts)
        if weather_trend:
            state.update_metadata("weather_trend", weather_trend)
        
        # キャッシュに保存
        cache_service.save_forecasts(
            selected_forecast,
            forecast_collection.forecasts,
            location_name
        )
        
        # 気温差の計算
        temperature_differences = temperature_analysis_service.calculate_temperature_differences(
            selected_forecast, 
            location_name
        )
        
        # === 6. 状態の更新 ===
        
        state.weather_data = selected_forecast
        state.update_metadata("forecast_collection", forecast_collection)
        state.location = location
        state.update_metadata("location_coordinates", {"latitude": lat, "longitude": lon})
        state.update_metadata("temperature_differences", temperature_differences)

        logger.info(
            f"Weather forecast fetched for {location_name}: {selected_forecast.weather_description}"
        )

        return state

    except Exception as e:
        logger.error(f"Failed to fetch weather forecast: {e!s}")
        state.add_error(f"天気予報の取得に失敗しました: {e!s}", "weather_forecast")
        # エラーをそのまま再発生させて処理を停止
        raise


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
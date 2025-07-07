"""
天気予報統合ノード

LangGraphノードとして天気予報データの取得・処理を行う
"""

import asyncio
import logging
import os
import pytz
from datetime import datetime, timedelta
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, START, StateGraph

from src.apis.wxtech import WxTechAPIError
from src.apis.wxtech.client import WxTechAPIClient
from src.data.weather_trend import WeatherTrend
from src.data.weather_data import WeatherForecastCollection, WeatherForecast
from src.data.forecast_cache import save_forecast_to_cache, get_temperature_differences, get_forecast_cache
from src.config.weather_config import get_config
from src.config.comment_config import get_comment_config
from src.config.config_loader import load_config
from src.nodes.weather_forecast import WeatherDataFetcher, WeatherDataTransformer, WeatherDataValidator

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
# リファクタリング版のインポート
from src.nodes.weather_forecast_node_refactored import fetch_weather_forecast_node_refactored

# 互換性のため、元の関数名でエイリアスを作成
fetch_weather_forecast_node = fetch_weather_forecast_node_refactored


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

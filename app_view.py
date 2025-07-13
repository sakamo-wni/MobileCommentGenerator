"""天気コメント生成システム - ビュー（UI定義）"""

import time
from datetime import datetime
from typing import Any, Optional

import streamlit as st

from app_constants import UIConstants
from app_interfaces import ICommentGenerationView
from src.types import BatchGenerationResult, LocationResult
from src.ui.streamlit_components import (
    generation_history_display,
    llm_provider_selector,
    location_selector,
    result_display,
    settings_panel,
)
from src.ui.streamlit_utils import format_timestamp
from src.config.config import Config


class CommentGenerationView(ICommentGenerationView):
    """UIの表示を管理するビュークラス

    Streamlitを使用したユーザーインターフェースの表示と管理を担当します。
    MVCパターンのViewレイヤーとして、ビジネスロジックから分離されたUI処理を実装します。

    主な責務:
    - ページレイアウトの構築
    - ユーザー入力の収集
    - 生成結果の表示
    - プログレス表示
    - エラーメッセージの表示
    """

    @staticmethod
    def setup_page_config(config: Config) -> None:
        """ページ設定"""
        st.set_page_config(
            page_title=config.ui_settings.page_title,
            page_icon=config.ui_settings.page_icon,
            layout=config.ui_settings.layout,
            initial_sidebar_state=config.ui_settings.sidebar_state
        )

    @staticmethod
    def display_header() -> None:
        """ヘッダー表示"""
        st.markdown('<h1 class="main-header">☀️ 天気コメント生成システム ☀️</h1>', unsafe_allow_html=True)

    @staticmethod
    def display_api_key_warning(validation_results: dict[str, Any]) -> None:
        """APIキーの警告表示"""
        if not validation_results["api_keys"]["wxtech"]:
            st.error("⚠️ WXTECH_API_KEYが設定されていません。天気予報データの取得ができません。")

    @staticmethod
    def display_debug_info(config: Config) -> None:
        """デバッグ情報表示"""
        if config.debug and config.ui_settings.show_debug_info:
            with st.expander("デバッグ情報", expanded=False):
                st.json(config.to_dict())

    @staticmethod
    def setup_sidebar(generation_history: list[dict[str, Any]]) -> None:
        """サイドバーのセットアップ"""
        with st.sidebar:
            st.header("設定")

            # APIキー設定
            with st.expander("APIキー設定", expanded=False):
                settings_panel()

            # 生成履歴
            st.header("生成履歴")
            generation_history_display(generation_history)

    @staticmethod
    def display_input_panel() -> tuple[list[str], str]:
        """入力パネルの表示"""
        st.header(f"{UIConstants.ICON_LOCATION} 入力設定")

        # 地点選択
        location = location_selector()

        # LLMプロバイダー選択
        llm_provider = llm_provider_selector()

        # 現在時刻表示
        st.info(f"🕐 生成時刻: {format_timestamp(datetime.now())}")

        return location, llm_provider

    @staticmethod
    def display_generation_button(is_generating: bool) -> bool:
        """生成ボタンの表示"""
        return st.button(
            "🎯 コメント生成",
            type="primary",
            disabled=is_generating,
            use_container_width=True
        )

    @staticmethod
    def display_location_warning(max_locations: int) -> None:
        """地点数超過の警告"""
        st.warning(f"⚠️ 選択された地点数が上限（{max_locations}地点）を超えています。")

    @staticmethod
    def display_no_location_error() -> None:
        """地点未選択エラー"""
        st.error("地点が選択されていません")

    @staticmethod
    def display_single_result(result: LocationResult, metadata: dict[str, Any]) -> None:
        """個別の結果を表示"""
        location = result['location']
        success = result['success']
        comment = result.get('comment', '')
        error = result.get('error', '')

        if success:
            st.success(f"{UIConstants.ICON_SUCCESS} **{location}**: {comment}")

            # メタデータがある場合は天気情報も表示
            if metadata:
                with st.expander(f"📊 {location}の詳細情報"):
                    # 予報時刻の表示
                    if metadata.get('forecast_time'):
                        st.info(f"{UIConstants.ICON_TIME} 予報時刻: {metadata['forecast_time']}")

                    # 天気データの表示
                    col1, col2 = st.columns(2)
                    with col1:
                        temp = metadata.get('temperature')
                        if temp is not None:
                            st.text(f"{UIConstants.ICON_TEMPERATURE} 気温: {temp}°C")

                        weather = metadata.get('weather_condition')
                        if weather and weather != '不明':
                            st.text(f"☁️ 天気: {weather}")

                    with col2:
                        wind = metadata.get('wind_speed')
                        if wind is not None:
                            st.text(f"{UIConstants.ICON_WIND} 風速: {wind}m/s")

                        humidity = metadata.get('humidity')
                        if humidity is not None:
                            st.text(f"{UIConstants.ICON_HUMIDITY} 湿度: {humidity}%")

                    # 選択されたコメントペア
                    if any(k in metadata for k in ['selected_weather_comment', 'selected_advice_comment']):
                        st.markdown("**🎯 選択されたコメント:**")

                        weather_comment = metadata.get('selected_weather_comment')
                        advice_comment = metadata.get('selected_advice_comment')

                        if weather_comment:
                            st.text(f"天気: {weather_comment}")
                        if advice_comment:
                            st.text(f"アドバイス: {advice_comment}")

                        # LLMプロバイダー情報
                        provider = metadata.get('llm_provider')
                        if provider:
                            st.text(f"選択方法: LLM ({provider})")
        else:
            st.error(f"{UIConstants.ICON_ERROR} **{location}**: {error}")

    @staticmethod
    def create_progress_ui() -> tuple[Any, Any]:
        """プログレスバーとステータステキストを作成"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        return progress_bar, status_text

    @staticmethod
    def update_progress(progress_bar: Any, status_text: Any, current: int, total: int, location: str) -> None:
        """進捗状況を更新"""
        progress = current / total
        progress_bar.progress(progress)
        status_text.text(f"生成中... {location} ({current + 1}/{total})")

    @staticmethod
    def complete_progress(progress_bar: Any, status_text: Any, success_count: int, total_count: int) -> None:
        """進捗完了時の表示"""
        progress_bar.progress(1.0)

        if success_count > 0:
            status_text.text(f"完了！{success_count}/{total_count}地点の生成が成功しました")
        else:
            status_text.text("エラー：すべての地点でコメント生成に失敗しました")

        time.sleep(UIConstants.PROGRESS_COMPLETE_DELAY)
        progress_bar.empty()
        status_text.empty()

    @staticmethod
    def display_generation_complete(result: BatchGenerationResult) -> None:
        """生成完了時の表示"""
        if result and result['success']:
            st.success(f"{UIConstants.ICON_SUCCESS} コメント生成が完了しました！ ({result['success_count']}/{result['total_locations']}地点成功)")
            if result['success_count'] == result['total_locations']:
                st.balloons()

            # 一部失敗した場合のエラー表示
            if result.get('errors'):
                with st.expander(f"{UIConstants.ICON_WARNING} エラー詳細"):
                    for error in result['errors']:
                        st.warning(error)
        elif result:
            # すべて失敗した場合
            if result.get('errors'):
                for error in result['errors']:
                    st.error(error)

    @staticmethod
    def display_results_section(current_result: Optional[BatchGenerationResult], is_generating: bool) -> None:
        """結果セクションの表示"""
        st.header(f"{UIConstants.ICON_WEATHER} 生成結果")

        # 生成中でない場合のみ固定の結果を表示
        if not is_generating:
            if current_result:
                result_display(current_result)
            else:
                st.info("👈 左側のパネルから地点とLLMプロバイダーを選択して、「コメント生成」ボタンをクリックしてください。")

            # サンプル表示
            with st.expander("サンプルコメント"):
                st.markdown("""
                **晴れの日**: 爽やかな朝ですね
                **雨の日**: 傘をお忘れなく
                **曇りの日**: 過ごしやすい一日です
                **雪の日**: 足元にお気をつけて
                """)

    @staticmethod
    def display_footer() -> None:
        """フッター表示"""
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Version**: 1.0.0")
        with col2:
            st.markdown("**Last Updated**: 2025-06-06")
        with col3:
            st.markdown("**By**: WNI Team")

    @staticmethod
    def display_error_with_hint(error_message: str, hint: Optional[str] = None) -> None:
        """エラーメッセージとヒントの表示"""
        st.error(error_message)
        if hint:
            st.info(f"💡 ヒント: {hint}")

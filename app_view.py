"""天気コメント生成システム - ビュー（UI定義）"""

import time
from datetime import datetime
from typing import Any

import streamlit as st

from app_constants import (
    API_KEY_WARNING,
    DEBUG_INFO_HEADER,
    FOOTER_BY,
    FOOTER_LAST_UPDATED,
    FOOTER_VERSION,
    GENERATION_ALL_FAILED,
    GENERATION_BUTTON_TEXT,
    GENERATION_COMPLETE,
    GENERATION_COMPLETE_SUCCESS,
    GENERATION_PROGRESS,
    GENERATION_TIME_FORMAT,
    INPUT_HEADER,
    LOCATION_LIMIT_WARNING,
    NO_LOCATION_ERROR,
    PROGRESS_MAX,
    RESULT_SECTION_HEADER,
    SAMPLE_COMMENTS,
    SIDEBAR_API_KEY_HEADER,
    SIDEBAR_HISTORY_HEADER,
    SIDEBAR_SETTINGS_HEADER,
    UI_SLEEP_DURATION,
)
from src.types import BatchGenerationResult, LocationResult
from src.ui.streamlit_components import (
    generation_history_display,
    llm_provider_selector,
    location_selector,
    result_display,
    settings_panel,
)
from src.ui.streamlit_utils import format_timestamp


class CommentGenerationView:
    """UIの表示を管理するビュークラス
    
    Streamlitを使用した天気コメント生成システムのUI表示を担当します。
    ビジネスロジックはControllerに委譲し、純粋に表示とユーザーインタラクションの
    処理に専念します。
    
    主な責務:
    - ページレイアウトとスタイルの管理
    - ユーザー入力の受け取りと表示
    - 生成結果の表示
    - 進捗状況の可視化
    - エラーメッセージとフィードバックの表示
    
    注意:
    - このクラスのメソッドは全て静的メソッドとして実装されています
    - ビジネスロジックは含まず、純粋な表示ロジックのみを扱います
    """

    @staticmethod
    def setup_page_config(config):
        """ページ設定"""
        st.set_page_config(
            page_title=config.ui_settings.page_title,
            page_icon=config.ui_settings.page_icon,
            layout=config.ui_settings.layout,
            initial_sidebar_state=config.ui_settings.sidebar_state
        )

    @staticmethod
    def display_header():
        """ヘッダー表示"""
        st.markdown('<h1 class="main-header">☀️ 天気コメント生成システム ☀️</h1>', unsafe_allow_html=True)

    @staticmethod
    def display_api_key_warning(validation_results: dict[str, Any]):
        """APIキーの警告表示"""
        if not validation_results["api_keys"]["wxtech"]:
            st.error(API_KEY_WARNING)

    @staticmethod
    def display_debug_info(config):
        """デバッグ情報表示"""
        if config.debug and config.ui_settings.show_debug_info:
            with st.expander(DEBUG_INFO_HEADER, expanded=False):
                st.json(config.to_dict())

    @staticmethod
    def setup_sidebar(generation_history: list[dict[str, Any]]):
        """サイドバーのセットアップ"""
        with st.sidebar:
            st.header(SIDEBAR_SETTINGS_HEADER)

            # APIキー設定
            with st.expander(SIDEBAR_API_KEY_HEADER, expanded=False):
                settings_panel()

            # 生成履歴
            st.header(SIDEBAR_HISTORY_HEADER)
            generation_history_display(generation_history)

    @staticmethod
    def display_input_panel() -> tuple[list[str], str]:
        """入力パネルの表示"""
        st.header(INPUT_HEADER)

        # 地点選択
        location = location_selector()

        # LLMプロバイダー選択
        llm_provider = llm_provider_selector()

        # 現在時刻表示
        st.info(GENERATION_TIME_FORMAT.format(format_timestamp(datetime.now())))

        return location, llm_provider

    @staticmethod
    def display_generation_button(is_generating: bool) -> bool:
        """生成ボタンの表示"""
        return st.button(
            GENERATION_BUTTON_TEXT,
            type="primary",
            disabled=is_generating,
            use_container_width=True
        )

    @staticmethod
    def display_location_warning(max_locations: int):
        """地点数超過の警告"""
        st.warning(LOCATION_LIMIT_WARNING.format(max_locations))

    @staticmethod
    def display_no_location_error():
        """地点未選択エラー"""
        st.error(NO_LOCATION_ERROR)

    @staticmethod
    def display_single_result(result: LocationResult, metadata: dict[str, Any]):
        """個別の結果を表示"""
        location = result['location']
        success = result['success']
        comment = result.get('comment', '')
        error = result.get('error', '')

        if success:
            st.success(f"✅ **{location}**: {comment}")

            # メタデータがある場合は天気情報も表示
            if metadata:
                with st.expander(f"📊 {location}の詳細情報"):
                    # 予報時刻の表示
                    if metadata.get('forecast_time'):
                        st.info(f"⏰ 予報時刻: {metadata['forecast_time']}")

                    # 天気データの表示
                    col1, col2 = st.columns(2)
                    with col1:
                        temp = metadata.get('temperature')
                        if temp is not None:
                            st.text(f"🌡️ 気温: {temp}°C")

                        weather = metadata.get('weather_condition')
                        if weather and weather != '不明':
                            st.text(f"☁️ 天気: {weather}")

                    with col2:
                        wind = metadata.get('wind_speed')
                        if wind is not None:
                            st.text(f"💨 風速: {wind}m/s")

                        humidity = metadata.get('humidity')
                        if humidity is not None:
                            st.text(f"💧 湿度: {humidity}%")

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
            st.error(f"❌ **{location}**: {error}")

    @staticmethod
    def create_progress_ui():
        """プログレスバーとステータステキストを作成"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        return progress_bar, status_text

    @staticmethod
    def update_progress(progress_bar, status_text, current: int, total: int, location: str):
        """進捗状況を更新"""
        progress = current / total
        progress_bar.progress(progress)
        status_text.text(GENERATION_PROGRESS.format(location, current + 1, total))

    @staticmethod
    def complete_progress(progress_bar, status_text, success_count: int, total_count: int):
        """進捗完了時の表示"""
        progress_bar.progress(PROGRESS_MAX)

        if success_count > 0:
            status_text.text(GENERATION_COMPLETE.format(success_count, total_count))
        else:
            status_text.text(GENERATION_ALL_FAILED)

        time.sleep(UI_SLEEP_DURATION)
        progress_bar.empty()
        status_text.empty()

    @staticmethod
    def display_generation_complete(result: BatchGenerationResult):
        """生成完了時の表示"""
        if result and result['success']:
            st.success(GENERATION_COMPLETE_SUCCESS.format(f"{result['success_count']}/{result['total_locations']}"))
            if result['success_count'] == result['total_locations']:
                st.balloons()

            # 一部失敗した場合のエラー表示
            if result.get('errors'):
                with st.expander("⚠️ エラー詳細"):
                    for error in result['errors']:
                        st.warning(error)
        elif result:
            # すべて失敗した場合
            if result.get('errors'):
                for error in result['errors']:
                    st.error(error)

    @staticmethod
    def display_results_section(current_result: BatchGenerationResult | None, is_generating: bool):
        """結果セクションの表示"""
        st.header(RESULT_SECTION_HEADER)

        # 生成中でない場合のみ固定の結果を表示
        if not is_generating:
            if current_result:
                result_display(current_result)
            else:
                st.info("👈 左側のパネルから地点とLLMプロバイダーを選択して、「コメント生成」ボタンをクリックしてください。")

            # サンプル表示
            with st.expander("サンプルコメント"):
                st.markdown(SAMPLE_COMMENTS)

    @staticmethod
    def display_footer():
        """フッター表示"""
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(FOOTER_VERSION)
        with col2:
            st.markdown(FOOTER_LAST_UPDATED)
        with col3:
            st.markdown(FOOTER_BY)

    @staticmethod
    def display_error_with_hint(error_message: str, hint: str | None = None):
        """エラーメッセージとヒントの表示"""
        st.error(error_message)
        if hint:
            st.info(f"💡 ヒント: {hint}")

"""天気コメント生成システム - Streamlit UIエントリーポイント"""


import streamlit as st

from app_constants import MAIN_COLUMN_RATIO, RESULT_HEADER
from app_controller import CommentGenerationController
from app_view import CommentGenerationView


def initialize_session_state(controller: CommentGenerationController):
    """セッション状態の初期化"""
    defaults = {
        'generation_history': controller.generation_history,
        'selected_location': controller.get_default_locations(),
        'llm_provider': controller.get_default_llm_provider(),
        'current_result': None,
        'is_generating': False,
        'config': controller.config
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value




def main(controller: CommentGenerationController | None = None,
         view: CommentGenerationView | None = None):
    """メインアプリケーション
    
    Args:
        controller: コントローラーインスタンス（テスト用のモック注入用）
        view: ビューインスタンス（テスト用のモック注入用）
    """
    # コントローラーとビューの初期化（依存性注入対応）
    if controller is None:
        controller = CommentGenerationController()
    if view is None:
        view = CommentGenerationView()

    # ページ設定（最初に呼ぶ必要がある）
    view.setup_page_config(controller.config)

    # セッション状態の初期化
    initialize_session_state(controller)

    # 設定の検証とAPIキー警告
    validation_results = controller.validate_configuration()
    view.display_api_key_warning(validation_results)

    # デバッグ情報表示
    view.display_debug_info(controller.config)

    # ヘッダー表示
    view.display_header()

    # サイドバー設定
    view.setup_sidebar(st.session_state.generation_history)

    # メインコンテンツ
    col1, col2 = st.columns(MAIN_COLUMN_RATIO)

    with col1:
        # 入力パネル
        location, llm_provider = view.display_input_panel()
        st.session_state.selected_location = location
        st.session_state.llm_provider = llm_provider

        # 生成ボタン
        if view.display_generation_button(st.session_state.is_generating):
            # 結果表示用のコンテナを先に作成
            col2.empty()
            results_container = col2.container()

            with st.spinner("生成中..."):
                # 複数地点の処理
                if isinstance(location, list) and len(location) > 0:
                    # 地点数の検証
                    is_valid, error_msg = controller.validate_location_count(location)
                    if not is_valid:
                        view.display_location_warning(controller.config.ui_settings.max_locations_per_generation)
                        location = location[:controller.config.ui_settings.max_locations_per_generation]

                    # ヘッダーを一度だけ表示
                    with results_container.container():
                        st.markdown(RESULT_HEADER)

                    # プログレスUI作成
                    progress_bar, status_text = view.create_progress_ui()

                    # 生成中フラグを立てる
                    st.session_state.is_generating = True

                    try:
                        # コールバック関数の定義
                        def progress_callback(current: int, total: int, location: str):
                            view.update_progress(progress_bar, status_text, current, total, location)

                        def result_callback(location_result: dict):
                            # 結果を即座に表示
                            with results_container.container():
                                metadata = controller.extract_weather_metadata(location_result)
                                if 'forecast_time' in metadata and metadata['forecast_time']:
                                    metadata['forecast_time'] = controller.format_forecast_time(metadata['forecast_time'])
                                view.display_single_result(location_result, metadata)

                        # バッチ生成実行
                        result = controller.generate_comments_batch(
                            locations=location,
                            llm_provider=llm_provider,
                            progress_callback=progress_callback,
                            result_callback=result_callback
                        )

                        # 完了処理
                        view.complete_progress(progress_bar, status_text, result['success_count'], result['total_locations'])

                    finally:
                        st.session_state.is_generating = False
                else:
                    view.display_no_location_error()
                    result = None

                st.session_state.current_result = result

                # 完了メッセージ
                view.display_generation_complete(result)

    with col2:
        # 結果セクション
        view.display_results_section(st.session_state.current_result, st.session_state.is_generating)

    # フッター
    view.display_footer()


def run_streamlit_app():
    """Streamlitアプリケーションの実行"""
    main()


if __name__ == "__main__":
    run_streamlit_app()

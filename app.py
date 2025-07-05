"""天気コメント生成システム - Streamlit UIエントリーポイント"""

import streamlit as st

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


def generate_with_progress(controller: CommentGenerationController, view: CommentGenerationView,
                          locations: list, llm_provider: str, results_container):
    """プログレスバー付きでコメントを生成"""
    # ヘッダーを一度だけ表示
    with results_container.container():
        st.markdown("### 🌤️ 生成結果")

    # プログレスUI作成
    progress_bar, status_text = view.create_progress_ui()

    # 生成中フラグを立てる
    st.session_state.is_generating = True

    try:
        # 進捗コールバック関数
        def progress_callback(idx, total, location):
            view.update_progress(progress_bar, status_text, idx, total, location)

            # 中間結果の表示（前のインデックスまでの結果を取得）
            if idx > 0:
                # 既に生成済みの結果を表示
                with results_container.container():
                    for i in range(idx):
                        if i < len(all_results):
                            result = all_results[i]
                            metadata = controller.extract_weather_metadata(result)
                            if 'forecast_time' in metadata and metadata['forecast_time']:
                                metadata['forecast_time'] = controller.format_forecast_time(metadata['forecast_time'])
                            view.display_single_result(result, metadata)

        # バッチ生成実行
        all_results = []

        # 各地点を順番に処理
        for idx, location in enumerate(locations):
            progress_callback(idx, len(locations), location)

            # 単一地点の生成
            location_result = controller.generate_comment_for_location(location, llm_provider)
            all_results.append(location_result)

            # 結果を即座に表示
            with results_container.container():
                metadata = controller.extract_weather_metadata(location_result)
                if 'forecast_time' in metadata and metadata['forecast_time']:
                    metadata['forecast_time'] = controller.format_forecast_time(metadata['forecast_time'])
                view.display_single_result(location_result, metadata)

        # 最終結果を集計
        success_count = sum(1 for r in all_results if r['success'])
        errors = [r for r in all_results if not r['success']]
        error_messages = []

        for err in errors:
            location = err['location']
            error_msg = err.get('error', '不明なエラー')
            error_messages.append(f"{location}: {error_msg}")

        result = {
            'success': success_count > 0,
            'total_locations': len(locations),
            'success_count': success_count,
            'results': all_results,
            'final_comment': '\n'.join([f"{r['location']}: {r['comment']}" for r in all_results if r['success']]),
            'errors': error_messages
        }

        # 完了処理
        view.complete_progress(progress_bar, status_text, success_count, len(locations))

        return result

    finally:
        st.session_state.is_generating = False


def main():
    """メインアプリケーション"""
    # コントローラーとビューの初期化
    controller = CommentGenerationController()
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
    col1, col2 = st.columns([1, 2])

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

                    # プログレスバー付き生成
                    result = generate_with_progress(controller, view, location, llm_provider, results_container)
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

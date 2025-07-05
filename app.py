"""天気コメント生成システム - Streamlit UIエントリーポイント"""

import streamlit as st

from app_controller import CommentGenerationController
from app_session_manager import SessionManager
from app_view import CommentGenerationView


def main():
    """メインアプリケーション"""
    # コントローラーとビューの初期化
    controller = CommentGenerationController()
    view = CommentGenerationView()

    # ページ設定（最初に呼ぶ必要がある）
    view.setup_page_config(controller.config)

    # セッション状態の初期化
    SessionManager.initialize(controller)

    # 設定の検証とAPIキー警告
    validation_results = controller.validate_configuration()
    view.display_api_key_warning(validation_results)

    # デバッグ情報表示
    view.display_debug_info(controller.config)

    # ヘッダー表示
    view.display_header()

    # サイドバー設定
    view.setup_sidebar(SessionManager.get('generation_history', []))

    # メインコンテンツ
    col1, col2 = st.columns([1, 2])

    with col1:
        # 入力パネル
        location, llm_provider = view.display_input_panel()
        SessionManager.set_selected_location(location)
        SessionManager.set_llm_provider(llm_provider)

        # 生成ボタン
        if view.display_generation_button(SessionManager.is_generating()):
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
                    result = controller.generate_with_progress(location, llm_provider, view, results_container)
                else:
                    view.display_no_location_error()
                    result = None

                SessionManager.set_current_result(result)

                # 完了メッセージ
                view.display_generation_complete(result)

    with col2:
        # 結果セクション
        view.display_results_section(SessionManager.get_current_result(), SessionManager.is_generating())

    # フッター
    view.display_footer()


def run_streamlit_app():
    """Streamlitアプリケーションの実行"""
    main()


if __name__ == "__main__":
    run_streamlit_app()

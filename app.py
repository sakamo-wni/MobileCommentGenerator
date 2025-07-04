"""天気コメント生成システム - Streamlit UI"""

import streamlit as st
from src.config.app_config import get_config

# 設定の読み込み
config = get_config()

# ページ設定（最初に呼ぶ必要がある）
st.set_page_config(
    page_title=config.ui_settings.page_title,
    page_icon=config.ui_settings.page_icon,
    layout=config.ui_settings.layout,
    initial_sidebar_state=config.ui_settings.sidebar_state
)

from datetime import datetime
import logging
import time
import pytz
from typing import List, Optional

from src.workflows.comment_generation_workflow import run_comment_generation
from src.ui.streamlit_components import (
    location_selector,
    llm_provider_selector,
    result_display,
    generation_history_display,
    settings_panel
)
from src.ui.streamlit_utils import save_to_history, load_history, load_locations, format_timestamp
from src.utils.error_handler import ErrorHandler, with_error_handling
from src.types import (
    BatchGenerationResult,
    LocationResult,
    GenerationResult,
    LLMProvider
)

logger = logging.getLogger(__name__)

def initialize_session_state():
    """セッション状態の初期化"""
    defaults = {
        'generation_history': load_history(),
        'selected_location': load_locations(),  # 全地点がデフォルト
        'llm_provider': config.ui_settings.default_llm_provider,
        'current_result': None,
        'is_generating': False,
        'config': config
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def display_single_result(result: LocationResult):
    """個別の結果を表示（累積表示を避ける）"""
    location = result['location']
    success = result['success']
    comment = result.get('comment', '')
    error = result.get('error', '')
    source_files = result.get('source_files', [])
    
    if success:
        st.success(f"✅ **{location}**: {comment}")
        
        # メタデータがある場合は天気情報も表示
        if result.get('result') and result['result'].get('generation_metadata'):
            metadata = result['result']['generation_metadata']
            with st.expander(f"📊 {location}の詳細情報"):
                # 天気予報時刻の表示
                forecast_time = metadata.get('weather_forecast_time')
                if forecast_time:
                    try:
                        # UTC時刻をパース
                        dt = datetime.fromisoformat(forecast_time.replace('Z', '+00:00'))
                        # JSTに変換
                        jst = pytz.timezone('Asia/Tokyo')
                        dt_jst = dt.astimezone(jst)
                        st.info(f"⏰ 予報時刻: {dt_jst.strftime('%Y年%m月%d日 %H時')}")
                    except Exception as e:
                        logger.warning(f"予報時刻のパース失敗: {e}, forecast_time={forecast_time}")
                        st.info(f"⏰ 予報時刻: {forecast_time}")
                
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
                selection_meta = metadata.get('selection_metadata', {})
                if selection_meta:
                    st.markdown("**🎯 選択されたコメント:**")
                    weather_comment = selection_meta.get('selected_weather_comment')
                    advice_comment = selection_meta.get('selected_advice_comment')
                    
                    if weather_comment:
                        st.text(f"天気: {weather_comment}")
                    if advice_comment:
                        st.text(f"アドバイス: {advice_comment}")
                    
                    # LLMプロバイダー情報
                    provider = selection_meta.get('llm_provider')
                    if provider:
                        st.text(f"選択方法: LLM ({provider})")
    else:
        st.error(f"❌ **{location}**: {error}")


def display_streaming_results(results: List[LocationResult]):
    """結果をストリーミング表示（従来関数・最終結果用）"""
    # ヘッダーはgenerate_comment_with_progressで表示済み
    
    for result in results:
        display_single_result(result)
    
    # 残りの地点数を表示
    remaining = len([r for r in results if not r['success'] and not r.get('error')])
    if remaining > 0:
        st.info(f"⏳ 生成待ち: {remaining}地点")


def generate_comment_with_progress(locations: List[str], llm_provider: str, results_container) -> BatchGenerationResult:
    """プログレスバー付きコメント生成（複数地点対応）"""
    if not locations:
        return {'success': False, 'error': '地点が選択されていません'}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_results = []
    total_locations = len(locations)
    
    # ヘッダーを一度だけ表示
    with results_container.container():
        st.markdown("### 🌤️ 生成結果")
    
    try:
        # ワークフロー実行の開始
        st.session_state.is_generating = True
        
        for idx, location in enumerate(locations):
            # 進捗更新
            progress = (idx / total_locations)
            progress_bar.progress(progress)
            status_text.text(f"生成中... {location} ({idx + 1}/{total_locations})")
            
            try:
                # 実際のコメント生成
                result = run_comment_generation(
                    location_name=location,
                    target_datetime=datetime.now(),
                    llm_provider=llm_provider
                )
                
                # 結果を収集
                location_result = {
                    'location': location,
                    'result': result,
                    'success': result.get('success', False),
                    'comment': result.get('final_comment', ''),
                    'error': result.get('error', None)
                }
                
                # ソースファイル情報を抽出
                metadata = result.get('generation_metadata', {})
                if metadata.get('selected_past_comments'):
                    sources = []
                    for comment in metadata['selected_past_comments']:
                        if 'source_file' in comment:
                            sources.append(comment['source_file'])
                    if sources:
                        location_result['source_files'] = sources
                        # 詳細ログ出力
                        logger.info(f"地点: {location}")
                        logger.info(f"  天気: {metadata.get('weather_condition', '不明')}")
                        logger.info(f"  気温: {metadata.get('temperature', '不明')}°C")
                        logger.info(f"  コメント生成元ファイル: {sources}")
                        logger.info(f"  生成コメント: {result.get('final_comment', '')}")
                
                all_results.append(location_result)
                
                # 個別地点の結果を追加表示（累積表示を避ける）
                with results_container.container():
                    display_single_result(location_result)
                
                # 履歴に保存
                if result.get('success'):
                    save_to_history(result, location, llm_provider)
                    
            except Exception as location_error:
                # 個別地点のエラーをキャッチして記録
                location_result = ErrorHandler.create_error_result(location, location_error)
                all_results.append(location_result)
                
                # 個別地点の結果を追加表示（累積表示を避ける）
                with results_container.container():
                    display_single_result(location_result)
        
        # 完了
        progress_bar.progress(1.0)
        
        # 成功数をカウント
        success_count = sum(1 for r in all_results if r['success'])
        
        if success_count > 0:
            status_text.text(f"完了！{success_count}/{total_locations}地点の生成が成功しました")
        else:
            status_text.text("エラー：すべての地点でコメント生成に失敗しました")
        
        time.sleep(0.5)
        
        # エラーがあった場合は詳細を収集
        errors = [r for r in all_results if not r['success']]
        error_messages = []
        
        for err in errors:
            location = err['location']
            error_msg = err.get('error', '不明なエラー')
            error_messages.append(f"{location}: {error_msg}")
        
        return {
            'success': success_count > 0,
            'total_locations': total_locations,
            'success_count': success_count,
            'results': all_results,
            'final_comment': '\n'.join([f"{r['location']}: {r['comment']}" for r in all_results if r['success']]),
            'errors': error_messages
        }
        
    except Exception as e:
        # 統一されたエラーハンドリング
        error_response = ErrorHandler.handle_error(e)
        st.error(error_response.user_message)
        if error_response.hint:
            st.info(f"💡 ヒント: {error_response.hint}")
        
        return {
            'success': False,
            'error': error_response.error_message,
            'final_comment': None
        }
    finally:
        st.session_state.is_generating = False
        progress_bar.empty()
        status_text.empty()


def main():
    """メインアプリケーション"""
    # 設定の検証
    validation_results = config.validate()
    
    # 必須APIキーの確認
    if not validation_results["api_keys"]["wxtech"]:
        st.error("⚠️ WXTECH_API_KEYが設定されていません。天気予報データの取得ができません。")
    
    # デバッグモードでの追加情報表示
    if config.debug and config.ui_settings.show_debug_info:
        with st.expander("デバッグ情報", expanded=False):
            st.json(config.to_dict())
    
    # セッション状態の初期化
    initialize_session_state()
    
    # ヘッダー
    st.markdown('<h1 class="main-header">☀️ 天気コメント生成システム ☀️</h1>', unsafe_allow_html=True)
    
    # サイドバー
    with st.sidebar:
        st.header("設定")
        
        # APIキー設定
        with st.expander("APIキー設定", expanded=False):
            settings_panel()
        
        # 生成履歴
        st.header("生成履歴")
        generation_history_display(st.session_state.generation_history)
    
    # メインコンテンツ
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("📍 入力設定")
        
        # 地点選択
        location = location_selector()
        st.session_state.selected_location = location
        
        # LLMプロバイダー選択
        llm_provider = llm_provider_selector()
        st.session_state.llm_provider = llm_provider
        
        # 現在時刻表示
        st.info(f"🕐 生成時刻: {format_timestamp(datetime.now())}")
        
        # 生成ボタン
        if st.button(
            "🎯 コメント生成",
            type="primary",
            disabled=st.session_state.is_generating,
            use_container_width=True
        ):
            # 結果表示用のコンテナを先に作成
            # col2の内容をクリアしてから新しいコンテナを作成
            col2.empty()
            results_container = col2.container()
            
            with st.spinner("生成中..."):
                # 複数地点の処理
                if isinstance(location, list) and len(location) > 0:
                    # 最大地点数のチェック
                    if len(location) > config.ui_settings.max_locations_per_generation:
                        st.warning(f"⚠️ 選択された地点数が上限（{config.ui_settings.max_locations_per_generation}地点）を超えています。")
                        location = location[:config.ui_settings.max_locations_per_generation]
                    result = generate_comment_with_progress(location, llm_provider, results_container)
                else:
                    st.error("地点が選択されていません")
                    result = None
                st.session_state.current_result = result
                
                if result and result['success']:
                    st.success(f"✅ コメント生成が完了しました！ ({result['success_count']}/{result['total_locations']}地点成功)")
                    if result['success_count'] == result['total_locations']:
                        st.balloons()
                    # 一部失敗した場合のエラー表示
                    if result.get('errors'):
                        with st.expander("⚠️ エラー詳細"):
                            for error in result['errors']:
                                st.warning(error)
                elif result:
                    # すべて失敗した場合はerrorメッセージをわかりやすく表示
                    if result.get('errors'):
                        for error in result['errors']:
                            st.error(error)
    
    with col2:
        st.header("💬 生成結果")
        
        # 生成中でない場合のみ固定の結果を表示
        if not st.session_state.is_generating:
            if st.session_state.current_result:
                result_display(st.session_state.current_result)
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
    
    # フッター
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Version**: 1.0.0")
    with col2:
        st.markdown("**Last Updated**: 2025-06-06")
    with col3:
        st.markdown("**By**: WNI Team")


def run_streamlit_app():
    """Streamlitアプリケーションの実行"""
    main()


if __name__ == "__main__":
    run_streamlit_app()

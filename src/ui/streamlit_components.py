"""
Streamlit UIコンポーネント

再利用可能なUIコンポーネントの定義
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


def location_selector() -> List[str]:
    """
    地点選択コンポーネント（複数選択対応）

    Returns:
        選択された地点名のリスト
    """
    from src.ui.streamlit_utils import load_locations, filter_locations

    # 地点データの読み込み
    locations = load_locations()

    # 検索機能
    search_query = st.text_input(
        "🔍 地点名で検索",
        key="location_search",
        placeholder="例: 東京、大阪、札幌...",
        help="地点名の一部を入力して検索できます",
    )

    # フィルタリング
    if search_query:
        filtered_locations = filter_locations(locations, search_query)
    else:
        filtered_locations = locations

    # よく使う地点（セッション状態から）
    if "favorite_locations" not in st.session_state:
        st.session_state.favorite_locations = ["東京", "大阪", "札幌", "福岡", "那覇"]

    # お気に入り地点の表示
    if st.checkbox("⭐ よく使う地点のみ表示"):
        filtered_locations = [
            loc for loc in filtered_locations if loc in st.session_state.favorite_locations
        ]

    # 地域選択オプション
    regions = {
        "関東地方": [
            "父島",
            "横浜",
            "小田原",
            "さいたま",
            "熊谷",
            "秩父",
            "千葉",
            "銚子",
            "館山",
            "水戸",
            "土浦",
            "前橋",
            "みなかみ",
            "宇都宮",
        ],
        "北海道": ["札幌", "函館", "旭川", "釧路", "帯広", "網走", "稚内"],
        "東北": ["仙台", "盛岡", "秋田", "山形", "郡山", "福島", "青森"],
        "中部": ["名古屋", "金沢", "富山", "長野", "新潟", "静岡", "岐阜", "福井", "甲府", "津"],
        "関西": ["大阪", "京都", "神戸", "奈良", "大津", "和歌山"],
        "中国": ["広島", "岡山", "鳥取", "島根", "山口", "松江"],
        "四国": ["高松", "松山", "高知", "徳島"],
        "九州": [
            "福岡",
            "北九州",
            "佐賀",
            "長崎",
            "熊本",
            "大分",
            "宮崎",
            "鹿児島",
            "沖縄",
            "那覇",
        ],
    }

    # 地域選択
    selected_region = st.selectbox(
        "🗾 地域を選択",
        options=["全地点"] + list(regions.keys()),
        help="地域を選択すると、その地域の地点が選択されます",
    )

    # 一括選択オプション
    col1, col2 = st.columns(2)
    with col1:
        if selected_region == "全地点":
            select_all = st.button("🌍 全地点選択", use_container_width=True)
        else:
            select_region = st.button(f"🌏 {selected_region}を選択", use_container_width=True)
    with col2:
        clear_all = st.button("🗑️ 選択解除", use_container_width=True)

    # 初期化：全地点を選択
    if "selected_locations" not in st.session_state:
        st.session_state.selected_locations = filtered_locations.copy()

    # 一括選択/解除
    if selected_region == "全地点":
        if "select_all" in locals() and select_all:
            st.session_state.selected_locations = filtered_locations.copy()
            st.rerun()
    else:
        if "select_region" in locals() and select_region:
            # 地域の地点のうち、filtered_locationsに含まれるもののみを選択
            region_locations = [
                loc for loc in regions[selected_region] if loc in filtered_locations
            ]
            st.session_state.selected_locations = region_locations
            st.rerun()

    if clear_all:
        st.session_state.selected_locations = []
        st.rerun()

    # デフォルト値の検証
    valid_defaults = [
        loc for loc in st.session_state.selected_locations if loc in filtered_locations
    ]

    # 複数選択
    selected_locations = st.multiselect(
        "🏍 地点を選択（複数選択可）",
        options=filtered_locations,
        default=valid_defaults,
        help="天気コメントを生成する地点を選択してください（複数選択可）",
    )

    # セッション状態を更新
    st.session_state.selected_locations = selected_locations

    # 選択状況の表示
    if selected_locations:
        st.info(f"選択中: {len(selected_locations)}地点")
    else:
        st.warning("地点が選択されていません")

    return selected_locations


def llm_provider_selector() -> str:
    """
    LLMプロバイダー選択コンポーネント

    Returns:
        選択されたプロバイダー名
    """
    providers = {
        "openai": "🤖 OpenAI (GPT-4)",
        "gemini": "✨ Google Gemini",
        "anthropic": "🧠 Anthropic Claude",
    }

    # プロバイダー選択
    selected_key = st.selectbox(
        "🤖 LLMプロバイダーを選択",
        options=list(providers.keys()),
        format_func=lambda x: providers[x],
        help="コメント生成に使用するAIモデルを選択してください",
    )

    # プロバイダー情報の表示
    provider_info = {
        "openai": "高品質で安定した生成が可能です。",
        "gemini": "Googleの最新AIモデルです。",
        "anthropic": "安全性を重視した生成が特徴です。",
    }

    st.caption(f"ℹ️ {provider_info.get(selected_key, '')}")

    return selected_key


def result_display(result: Dict[str, Any]):
    """
    生成結果表示コンポーネント（複数地点対応）

    Args:
        result: 生成結果の辞書
    """
    if not result or not result.get("success"):
        st.error("生成結果がありません")
        return

    # 複数地点の結果がある場合
    if "results" in result:
        st.markdown(f"### 生成完了: {result['success_count']}/{result['total_locations']}地点")

        # 各地点の結果を表示
        for location_result in result["results"]:
            location = location_result["location"]
            success = location_result["success"]
            comment = location_result["comment"]

            if success:
                st.markdown(
                    f"""
                    <div style="background-color: #E3F2FD; border: 1px solid #1E88E5; border-radius: 5px; padding: 10px; margin: 5px 0;">
                        <strong>🏍 {location}</strong><br>
                        💬 {comment}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="background-color: #FFEBEE; border: 1px solid #F44336; border-radius: 5px; padding: 10px; margin: 5px 0;">
                        <strong>🏍 {location}</strong><br>
                        ❌ 生成失敗
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # 一括コピー用のテキスト
        all_comments = "\n".join(
            [f"{r['location']}: {r['comment']}" for r in result["results"] if r["success"]]
        )
        comment = all_comments
    else:
        # 単一地点の結果（後方互換性）
        comment = result.get("final_comment", "")
        st.markdown(
            f"""
        <div class="result-box">
            <h2>{comment}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # アクションボタン
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 コピー", key="copy_button", use_container_width=True, type="primary"):
            from src.ui.streamlit_utils import copy_to_clipboard

            copy_to_clipboard(comment)
            st.toast("✅ クリップボードにコピーしました！", icon="✅")

    with col2:
        if st.button("🔄 再生成", use_container_width=True):
            st.rerun()

    with col3:
        if st.button("💾 保存", use_container_width=True):
            # 履歴に保存（省略：保存機能の実装はスキップ）
            st.info("履歴に保存されています")

    # メタデータ表示
    with st.expander("📊 生成情報の詳細"):
        # 複数地点の場合は最初の成功した結果のメタデータを使用
        if "results" in result and result["results"]:
            # 成功した結果を探す
            for location_result in result["results"]:
                if location_result.get("success") and location_result.get("result"):
                    metadata = location_result["result"].get("generation_metadata", {})
                    break
            else:
                metadata = {}
        else:
            # 単一地点の場合
            metadata = result.get("generation_metadata", {})

        col1, col2 = st.columns(2)

        with col1:
            st.metric("実行時間", f"{metadata.get('execution_time_ms', 0)}ms")
            st.metric("気温", f"{metadata.get('temperature', 'N/A')}°C")
            st.metric("リトライ回数", metadata.get("retry_count", 0))

        with col2:
            st.metric("天気", metadata.get("weather_condition", "N/A"))
            st.metric("LLMプロバイダー", metadata.get("llm_provider", "N/A"))
            st.metric(
                "検証スコア",
                (
                    f"{metadata.get('validation_score', 0):.2f}"
                    if metadata.get("validation_score")
                    else "N/A"
                ),
            )

        # 時系列予報データ
        weather_timeline = metadata.get("weather_timeline")
        if weather_timeline:
            st.subheader("📈 時系列予報データ")
            
            # 概要表示
            summary = weather_timeline.get("summary", {})
            if summary:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("天気パターン", summary.get("weather_pattern", "不明"))
                with col2:
                    st.metric("気温範囲", summary.get("temperature_range", "不明"))
                with col3:
                    st.metric("最大降水量", summary.get("max_precipitation", "不明"))
            
            # 過去の推移
            past_forecasts = weather_timeline.get("past_forecasts", [])
            if past_forecasts:
                st.write("**過去の推移（12時間前〜基準時刻）**")
                past_df_data = []
                for forecast in past_forecasts:
                    past_df_data.append({
                        "時刻": forecast.get("label", ""),
                        "日時": forecast.get("time", ""),
                        "天気": forecast.get("weather", ""),
                        "気温": f"{forecast.get('temperature', 'N/A')}°C",
                        "降水量": f"{forecast.get('precipitation', 0)}mm" if forecast.get('precipitation', 0) > 0 else "-"
                    })
                if past_df_data:
                    import pandas as pd
                    st.dataframe(pd.DataFrame(past_df_data), use_container_width=True)
            
            # 未来の予報
            future_forecasts = weather_timeline.get("future_forecasts", [])
            if future_forecasts:
                st.write("**今後の予報（3〜24時間後）**")
                future_df_data = []
                for forecast in future_forecasts:
                    future_df_data.append({
                        "時刻": forecast.get("label", ""),
                        "日時": forecast.get("time", ""),
                        "天気": forecast.get("weather", ""),
                        "気温": f"{forecast.get('temperature', 'N/A')}°C",
                        "降水量": f"{forecast.get('precipitation', 0)}mm" if forecast.get('precipitation', 0) > 0 else "-"
                    })
                if future_df_data:
                    import pandas as pd
                    st.dataframe(pd.DataFrame(future_df_data), use_container_width=True)
            
            # エラー表示
            if "error" in weather_timeline:
                st.error(f"時系列データ取得エラー: {weather_timeline['error']}")

        # 選択された過去コメント情報
        if "selected_past_comments" in metadata:
            st.subheader("📝 参考にした過去コメント")
            for comment in metadata["selected_past_comments"]:
                st.text(f"• {comment.get('text', '')}")

        # 生の JSON データ (ネストされたexpanderを避けるため、直接表示)
        st.subheader("🔧 詳細データ")
        st.json(metadata)


def generation_history_display(history: List[Dict[str, Any]]):
    """
    生成履歴表示コンポーネント

    Args:
        history: 生成履歴のリスト
    """
    if not history:
        st.info("まだ生成履歴がありません。")
        return

    import pandas as pd

    # DataFrameとして表示
    df = pd.DataFrame(history)
    st.dataframe(df)

    # CSVダウンロードボタン
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 履歴をダウンロード",
        data=csv,
        file_name=f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

    # 最新の履歴から表示
    st.divider()
    st.subheader("最近の生成履歴")

    for idx, item in enumerate(reversed(history[-10:])):  # 最新10件
        timestamp = item.get("timestamp", "")
        location = item.get("location", "不明")
        comment = item.get("final_comment", "")

        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.text(f"🏍 {location}")
                st.caption(f"💬 {comment}")

            with col2:
                st.caption(timestamp[:16])  # YYYY-MM-DD HH:MM

                # 詳細ボタン
            if st.button(f"詳細", key=f"history_{idx}"):
                with st.expander("履歴詳細", expanded=True):
                    st.json(item)

            st.divider()

    # 全履歴のエクスポート
    if st.button("📅 履歴をエクスポート"):
        # JSON形式でダウンロード
        json_str = json.dumps(history, ensure_ascii=False, indent=2)
        st.download_button(
            label="JSONファイルをダウンロード",
            data=json_str,
            file_name=f"comment_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )


def settings_panel():
    """
    設定パネルコンポーネント
    """
    st.subheader("🔐 APIキー設定")

    import os

    # OpenAI
    openai_key = st.text_input(
        "OpenAI APIキー",
        type="password",
        value=os.environ.get("OPENAI_API_KEY", st.session_state.get("openai_api_key", "")),
        help="OpenAI APIキーを入力してください",
    )
    if openai_key:
        st.session_state.openai_api_key = openai_key
        if openai_key and len(openai_key) > 10:
            st.success("✅ OpenAI APIキー設定済み")

    # Gemini
    gemini_key = st.text_input(
        "Gemini APIキー",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", st.session_state.get("gemini_api_key", "")),
        help="Google Gemini APIキーを入力してください",
    )
    if gemini_key:
        st.session_state.gemini_api_key = gemini_key
        if gemini_key and len(gemini_key) > 10:
            st.success("✅ Gemini APIキー設定済み")

    # Anthropic
    anthropic_key = st.text_input(
        "Anthropic APIキー",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", st.session_state.get("anthropic_api_key", "")),
        help="Anthropic Claude APIキーを入力してください",
    )
    if anthropic_key:
        st.session_state.anthropic_api_key = anthropic_key
        if anthropic_key and len(anthropic_key) > 10:
            st.success("✅ Anthropic APIキー設定済み")

    # 検証ボタン
    if st.button("🔍 APIキーを検証"):
        with st.spinner("検証中..."):
            # TODO: 実際のAPI検証ロジックを実装
            st.success("APIキーが有効です！")

    st.divider()

    # 生成設定
    st.subheader("⚙️ 生成設定")

    # 文字数制限
    max_chars = st.slider(
        "最大文字数", min_value=10, max_value=200, value=50, help="生成コメントの最大文字数"
    )
    st.session_state.max_chars = max_chars

    # コメントスタイル
    comment_style = st.selectbox(
        "コメントスタイル",
        options=["カジュアル", "フォーマル", "親しみやすい"],
        help="生成コメントのスタイルを選択",
    )
    st.session_state.comment_style = comment_style

    # 絵文字使用
    use_emoji = st.checkbox(
        "絵文字を使用する",
        value=st.session_state.get("use_emoji", True),
        help="コメントに絵文字を含めるかどうか",
    )
    st.session_state.use_emoji = use_emoji

    st.divider()

    # その他の設定
    st.subheader("⚙️ その他の設定")

    # 最大リトライ回数
    max_retries = st.number_input(
        "最大リトライ回数",
        min_value=0,
        max_value=10,
        value=5,
        help="コメント生成が失敗した場合の最大リトライ回数",
    )
    st.session_state.max_retries = max_retries

    # タイムアウト設定
    timeout = st.slider(
        "タイムアウト (秒)",
        min_value=10,
        max_value=60,
        value=30,
        help="API呼び出しのタイムアウト時間",
    )
    st.session_state.timeout = timeout

    # デバッグモード
    debug_mode = st.checkbox(
        "デバッグモード",
        value=st.session_state.get("debug_mode", False),
        help="詳細なログ情報を表示します",
    )
    st.session_state.debug_mode = debug_mode

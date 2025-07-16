"""
キャッシュモニタリングコンポーネント

キャッシュの統計情報とパフォーマンスを可視化する
Streamlitコンポーネント
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from pathlib import Path

from src.utils.cache_manager import get_cache_manager
from src.types.aliases import JsonDict


def display_cache_monitor(show_details: bool = True):
    """キャッシュモニターを表示"""
    st.header("🗄️ キャッシュモニター")
    
    cache_manager = get_cache_manager()
    
    # 更新ボタン
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 更新", key="refresh_cache_stats"):
            st.rerun()
    
    # サマリー統計
    display_cache_summary(cache_manager)
    
    # 詳細統計
    if show_details:
        display_cache_details(cache_manager)
    
    # 履歴グラフ
    display_cache_history()


def display_cache_summary(cache_manager):
    """キャッシュサマリーを表示"""
    stats = cache_manager.get_stats_summary()
    
    # メトリクスを表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "総キャッシュ数",
            stats["total_caches"],
            help="アクティブなキャッシュの総数"
        )
    
    with col2:
        st.metric(
            "総メモリ使用量",
            f"{stats['total_memory_usage_mb']:.1f} MB",
            help="全キャッシュの合計メモリ使用量"
        )
    
    with col3:
        hit_rate_percent = stats['overall_hit_rate'] * 100
        st.metric(
            "全体ヒット率",
            f"{hit_rate_percent:.1f}%",
            help="全キャッシュの平均ヒット率"
        )
    
    with col4:
        memory_pressure = stats['memory_pressure'] * 100
        delta_color = "inverse" if memory_pressure > 80 else "normal"
        st.metric(
            "メモリプレッシャー",
            f"{memory_pressure:.1f}%",
            delta=f"{memory_pressure - 50:.1f}%",
            delta_color=delta_color,
            help="システムのメモリ使用率"
        )


def display_cache_details(cache_manager):
    """キャッシュの詳細情報を表示"""
    st.subheader("📊 キャッシュ詳細")
    
    all_stats = cache_manager.get_all_stats()
    
    # データフレームを作成
    cache_data = []
    for name, stats in all_stats.items():
        cache_data.append({
            "キャッシュ名": name,
            "エントリ数": stats.basic_stats.size,
            "ヒット数": stats.basic_stats.hits,
            "ミス数": stats.basic_stats.misses,
            "ヒット率": f"{stats.basic_stats.hit_rate * 100:.1f}%",
            "メモリ使用量(MB)": f"{stats.basic_stats.memory_usage_bytes / (1024 * 1024):.2f}",
            "効率スコア": f"{stats.cache_efficiency_score:.2f}",
            "LRU削除数": stats.evictions_by_lru,
            "メモリ圧迫削除数": stats.evictions_by_memory_pressure,
        })
    
    df = pd.DataFrame(cache_data)
    
    # テーブル表示
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "効率スコア": st.column_config.ProgressColumn(
                "効率スコア",
                help="キャッシュの総合的な効率性（0-1）",
                format="%.2f",
                min_value=0,
                max_value=1,
            ),
        }
    )
    
    # 個別キャッシュの詳細表示
    selected_cache = st.selectbox(
        "詳細を表示するキャッシュを選択",
        options=list(all_stats.keys()),
        key="selected_cache_detail"
    )
    
    if selected_cache:
        display_single_cache_detail(selected_cache, all_stats[selected_cache])


def display_single_cache_detail(cache_name: str, stats):
    """単一キャッシュの詳細を表示"""
    col1, col2 = st.columns(2)
    
    with col1:
        # ヒット率のゲージチャート
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = stats.basic_stats.hit_rate * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"{cache_name} ヒット率 (%)"},
            delta = {'reference': 80},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # エビクション理由の円グラフ
        eviction_data = {
            "TTL期限切れ": stats.evictions_by_ttl,
            "LRU": stats.evictions_by_lru,
            "メモリ圧迫": stats.evictions_by_memory_pressure,
        }
        
        if sum(eviction_data.values()) > 0:
            fig = px.pie(
                values=list(eviction_data.values()),
                names=list(eviction_data.keys()),
                title=f"{cache_name} エビクション理由"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("エビクションはまだ発生していません")
    
    # エントリの年齢情報
    if stats.basic_stats.oldest_entry_age_seconds:
        st.info(
            f"最古エントリ: {stats.basic_stats.oldest_entry_age_seconds / 60:.1f}分前 | "
            f"最新エントリ: {stats.basic_stats.newest_entry_age_seconds / 60:.1f}分前"
        )


def display_cache_history():
    """キャッシュ履歴グラフを表示"""
    st.subheader("📈 キャッシュパフォーマンス履歴")
    
    # 統計ファイルからデータを読み込み
    stats_file = Path("cache_stats.json")
    
    if not stats_file.exists():
        st.info("履歴データがまだありません。しばらくお待ちください。")
        return
    
    try:
        with open(stats_file, 'r') as f:
            history = json.load(f)
    except Exception as e:
        st.error(f"履歴データの読み込みに失敗しました: {e}")
        return
    
    if not history:
        st.info("履歴データがまだありません。")
        return
    
    # データフレームに変換
    df_history = pd.DataFrame(history)
    df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
    
    # 時間範囲の選択
    time_range = st.select_slider(
        "表示期間",
        options=["1時間", "6時間", "24時間", "7日間"],
        value="24時間",
        key="cache_history_range"
    )
    
    # 時間範囲でフィルタ
    now = datetime.now()
    time_ranges = {
        "1時間": timedelta(hours=1),
        "6時間": timedelta(hours=6),
        "24時間": timedelta(hours=24),
        "7日間": timedelta(days=7),
    }
    
    cutoff_time = now - time_ranges[time_range]
    df_filtered = df_history[df_history['timestamp'] >= cutoff_time]
    
    if df_filtered.empty:
        st.info(f"選択した期間（{time_range}）のデータがありません。")
        return
    
    # グラフの作成
    tab1, tab2, tab3 = st.tabs(["ヒット率", "メモリ使用量", "リクエスト数"])
    
    with tab1:
        fig = px.line(
            df_filtered,
            x='timestamp',
            y='overall_hit_rate',
            title='全体ヒット率の推移',
            labels={'overall_hit_rate': 'ヒット率', 'timestamp': '時刻'}
        )
        fig.update_yaxis(tickformat='.0%')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.line(
            df_filtered,
            x='timestamp',
            y='total_memory_usage_mb',
            title='総メモリ使用量の推移',
            labels={'total_memory_usage_mb': 'メモリ使用量 (MB)', 'timestamp': '時刻'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = px.line(
            df_filtered,
            x='timestamp',
            y='total_requests',
            title='総リクエスト数の推移',
            labels={'total_requests': 'リクエスト数', 'timestamp': '時刻'}
        )
        st.plotly_chart(fig, use_container_width=True)


def cache_control_panel():
    """キャッシュ制御パネル"""
    st.subheader("⚙️ キャッシュ制御")
    
    cache_manager = get_cache_manager()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ 全キャッシュクリア", type="secondary"):
            cache_manager.clear_all_caches()
            st.success("全キャッシュをクリアしました")
            st.rerun()
    
    with col2:
        selected_cache = st.selectbox(
            "個別クリア",
            options=list(cache_manager._caches.keys()),
            key="clear_single_cache"
        )
    
    with col3:
        if st.button("🗑️ 選択したキャッシュをクリア"):
            if selected_cache:
                cache_manager.get_cache(selected_cache).clear()
                st.success(f"{selected_cache} をクリアしました")
                st.rerun()
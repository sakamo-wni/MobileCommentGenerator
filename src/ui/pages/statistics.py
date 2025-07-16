"""
統計・分析ページ

生成履歴の統計分析とデータ可視化
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Any

from src.ui.streamlit_utils import get_statistics, load_history


def show_statistics_page():
    """統計・分析ページの表示"""
    st.title("📊 統計・分析")

    # 履歴データの読み込み
    history = load_history()

    if not history:
        st.info("統計表示するデータがありません。コメントを生成して履歴を作成してください。")
        return

    # 統計データの取得
    stats = get_statistics(history)

    # メトリクス表示
    show_key_metrics(stats)

    # グラフ表示
    show_charts(history)

    # 詳細分析
    show_detailed_analysis(history)


def show_key_metrics(stats: dict[str, Any]):
    """主要指標の表示"""
    st.header("📈 主要指標")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("総生成回数", stats.get("total_generations", 0))

    with col2:
        success_count = stats.get("successful_generations", 0)
        total_count = stats.get("total_generations", 0)
        st.metric("成功回数", success_count, delta=f"成功率 {stats.get('success_rate', 0):.1f}%")

    with col3:
        # 今日の生成回数
        today_count = stats.get("today_count", 0)
        st.metric("今日の生成回数", today_count)

    with col4:
        # 最新生成からの経過時間
        latest = stats.get("latest_generation", "")
        if latest:
            try:
                latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
                hours_ago = int((datetime.now() - latest_dt).total_seconds() / 3600)
                st.metric("最新生成", f"{hours_ago}時間前")
            except:
                st.metric("最新生成", "不明")
        else:
            st.metric("最新生成", "なし")


def show_charts(history: list[dict[str, Any]]):
    """グラフ表示"""
    st.header("📊 データ可視化")

    # DataFrameに変換
    df = pd.DataFrame(history)

    # 時系列チャート
    show_timeline_chart(df)

    # 地点別チャート
    show_location_chart(df)

    # LLMプロバイダー別チャート
    show_provider_chart(df)

    # 成功率チャート
    show_success_rate_chart(df)


def show_timeline_chart(df: pd.DataFrame):
    """時系列チャート"""
    st.subheader("📅 時系列分析")

    if "timestamp" not in df.columns or df.empty:
        st.info("時系列データがありません")
        return

    # タイムスタンプを日時型に変換
    df["datetime"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["datetime"].dt.date

    # 日別集計
    daily_counts = df.groupby("date").size().reset_index(name="count")

    # グラフ作成
    fig = px.line(
        daily_counts,
        x="date",
        y="count",
        title="日別生成回数",
        labels={"date": "日付", "count": "生成回数"},
    )
    fig.update_layout(xaxis_title="日付", yaxis_title="生成回数", showlegend=False)

    st.plotly_chart(fig, use_container_width=True)


def show_location_chart(df: pd.DataFrame):
    """地点別チャート"""
    st.subheader("🏍 地点別分析")

    if "location" not in df.columns or df.empty:
        st.info("地点データがありません")
        return

    # 地点別集計
    location_counts = df["location"].value_counts().head(10)

    col1, col2 = st.columns(2)

    with col1:
        # 棒グラフ
        fig_bar = px.bar(
            x=location_counts.index,
            y=location_counts.values,
            title="地点別生成回数（上位10位）",
            labels={"x": "地点", "y": "生成回数"},
        )
        fig_bar.update_layout(xaxis_title="地点", yaxis_title="生成回数", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        # 円グラフ
        fig_pie = px.pie(
            values=location_counts.values, names=location_counts.index, title="地点別生成割合"
        )
        st.plotly_chart(fig_pie, use_container_width=True)


def show_provider_chart(df: pd.DataFrame):
    """LLMプロバイダー別チャート"""
    st.subheader("🤖 LLMプロバイダー別分析")

    if "llm_provider" not in df.columns or df.empty:
        st.info("プロバイダーデータがありません")
        return

    # プロバイダー別集計
    provider_counts = df["llm_provider"].value_counts()

    # 棒グラフ
    fig = px.bar(
        x=provider_counts.index,
        y=provider_counts.values,
        title="LLMプロバイダー別生成回数",
        labels={"x": "プロバイダー", "y": "生成回数"},
        color=provider_counts.values,
        color_continuous_scale="viridis",
    )
    fig.update_layout(xaxis_title="LLMプロバイダー", yaxis_title="生成回数", showlegend=False)

    st.plotly_chart(fig, use_container_width=True)


def show_success_rate_chart(df: pd.DataFrame):
    """成功率チャート"""
    st.subheader("✅ 成功率分析")

    if "success" not in df.columns or df.empty:
        st.info("成功率データがありません")
        return

    # 成功率の計算
    success_rate = df["success"].mean() * 100
    failure_rate = 100 - success_rate

    # ゲージチャート
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=success_rate,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "全体成功率 (%)"},
            delta={"reference": 90},
            gauge={
                "axis": {"range": [None, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 50], "color": "lightgray"},
                    {"range": [50, 80], "color": "gray"},
                    {"range": [80, 100], "color": "lightgreen"},
                ],
                "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 90},
            },
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # プロバイダー別成功率
    if "llm_provider" in df.columns:
        provider_success = (
            df.groupby("llm_provider")["success"].agg(["count", "sum", "mean"]).reset_index()
        )
        provider_success["success_rate"] = provider_success["mean"] * 100

        fig_provider = px.bar(
            provider_success,
            x="llm_provider",
            y="success_rate",
            title="LLMプロバイダー別成功率",
            labels={"llm_provider": "プロバイダー", "success_rate": "成功率 (%)"},
            color="success_rate",
            color_continuous_scale="RdYlGn",
        )
        fig_provider.update_layout(
            xaxis_title="LLMプロバイダー", yaxis_title="成功率 (%)", showlegend=False
        )

        st.plotly_chart(fig_provider, use_container_width=True)


def show_detailed_analysis(history: list[dict[str, Any]]):
    """詳細分析"""
    st.header("🔍 詳細分析")

    # データフレーム作成
    df = pd.DataFrame(history)

    # 分析タブ
    tab1, tab2, tab3 = st.tabs(["時間分析", "パフォーマンス分析", "エラー分析"])

    with tab1:
        show_time_analysis(df)

    with tab2:
        show_performance_analysis(df)

    with tab3:
        show_error_analysis(df)


def show_time_analysis(df: pd.DataFrame):
    """時間分析"""
    st.subheader("⏰ 時間別使用パターン")

    if "timestamp" not in df.columns or df.empty:
        st.info("時間データがありません")
        return

    df["datetime"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["datetime"].dt.hour
    df["weekday"] = df["datetime"].dt.day_name()

    col1, col2 = st.columns(2)

    with col1:
        # 時間別分析
        hourly_counts = df["hour"].value_counts().sort_index()
        fig_hour = px.bar(
            x=hourly_counts.index,
            y=hourly_counts.values,
            title="時間別生成回数",
            labels={"x": "時間", "y": "生成回数"},
        )
        fig_hour.update_layout(xaxis_title="時間", yaxis_title="生成回数", showlegend=False)
        st.plotly_chart(fig_hour, use_container_width=True)

    with col2:
        # 曜日別分析
        weekday_counts = df["weekday"].value_counts()
        fig_weekday = px.bar(
            x=weekday_counts.index,
            y=weekday_counts.values,
            title="曜日別生成回数",
            labels={"x": "曜日", "y": "生成回数"},
        )
        fig_weekday.update_layout(xaxis_title="曜日", yaxis_title="生成回数", showlegend=False)
        st.plotly_chart(fig_weekday, use_container_width=True)


def show_performance_analysis(df: pd.DataFrame):
    """パフォーマンス分析"""
    st.subheader("⚡ パフォーマンス分析")

    # 実行時間の分析（メタデータから）
    execution_times = []
    for _, row in df.iterrows():
        metadata = row.get("generation_metadata", {})
        if isinstance(metadata, dict) and "execution_time_ms" in metadata:
            execution_times.append(metadata["execution_time_ms"])

    if execution_times:
        # 実行時間の統計
        avg_time = sum(execution_times) / len(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("平均実行時間", f"{avg_time:.0f}ms")
        with col2:
            st.metric("最短実行時間", f"{min_time:.0f}ms")
        with col3:
            st.metric("最長実行時間", f"{max_time:.0f}ms")

        # ヒストグラム
        fig_hist = px.histogram(
            x=execution_times,
            nbins=20,
            title="実行時間分布",
            labels={"x": "実行時間 (ms)", "y": "頻度"},
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("パフォーマンスデータがありません")


def show_error_analysis(df: pd.DataFrame):
    """エラー分析"""
    st.subheader("❌ エラー分析")

    if "success" not in df.columns or df.empty:
        st.info("エラーデータがありません")
        return

    # エラー率
    error_count = (df["success"] == False).sum()
    total_count = len(df)
    error_rate = (error_count / total_count) * 100 if total_count > 0 else 0

    st.metric("エラー率", f"{error_rate:.1f}%", delta=f"{error_count}/{total_count}")

    # エラー詳細
    error_df = df[df["success"] == False]

    if not error_df.empty and "error" in error_df.columns:
        st.subheader("エラー詳細")

        # エラーメッセージの集計
        error_messages = error_df["error"].dropna().value_counts()

        if not error_messages.empty:
            fig_errors = px.bar(
                x=error_messages.values,
                y=error_messages.index,
                orientation="h",
                title="エラータイプ別発生回数",
                labels={"x": "発生回数", "y": "エラータイプ"},
            )
            st.plotly_chart(fig_errors, use_container_width=True)

        # エラー履歴テーブル
        st.subheader("最近のエラー履歴")
        error_display = error_df[["timestamp", "location", "llm_provider", "error"]].tail(10)
        st.dataframe(error_display, use_container_width=True)
    else:
        st.success("エラーは発生していません！")

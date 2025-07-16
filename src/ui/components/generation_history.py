"""生成履歴表示コンポーネント"""

import streamlit as st
from typing import Any
from datetime import datetime
import pytz
import json


def generation_history_display(history: list[dict[str, Any]]) -> None:
    """
    生成履歴表示コンポーネント

    Args:
        history: 生成履歴のリスト
    """
    if not history:
        st.info("まだ生成履歴がありません")
        return
    
    # 履歴の件数表示
    st.write(f"📚 履歴: {len(history)}件")
    
    # フィルタリングオプション
    filter_options = st.expander("フィルターオプション", expanded=False)
    with filter_options:
        # 地点でフィルタ
        all_locations = list(set(h.get('location', '不明') for h in history))
        selected_locations = st.multiselect(
            "地点でフィルタ",
            all_locations,
            default=all_locations
        )
        
        # プロバイダーでフィルタ
        all_providers = list(set(h.get('llm_provider', '不明') for h in history))
        selected_providers = st.multiselect(
            "プロバイダーでフィルタ",
            all_providers,
            default=all_providers
        )
        
        # 日付範囲でフィルタ
        if history:
            dates = [datetime.fromisoformat(h['timestamp'].replace('Z', '+00:00')) for h in history if 'timestamp' in h]
            if dates:
                min_date = min(dates).date()
                max_date = max(dates).date()
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("開始日", value=min_date, min_value=min_date, max_value=max_date)
                with col2:
                    end_date = st.date_input("終了日", value=max_date, min_value=min_date, max_value=max_date)
    
    # フィルタリング実行
    filtered_history = []
    for item in history:
        # 地点フィルタ
        if item.get('location', '不明') not in selected_locations:
            continue
        
        # プロバイダーフィルタ
        if item.get('llm_provider', '不明') not in selected_providers:
            continue
        
        # 日付フィルタ
        if 'timestamp' in item:
            try:
                item_date = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00')).date()
                if not (start_date <= item_date <= end_date):
                    continue
            except (ValueError, TypeError, AttributeError):
                pass
        
        filtered_history.append(item)
    
    # ソート（新しい順）
    filtered_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # 履歴の表示
    for item in filtered_history[:10]:  # 最新10件のみ表示
        display_history_item(item)
    
    # エクスポート機能
    if st.button("📥 履歴をエクスポート"):
        export_history(filtered_history)


def display_history_item(item: dict[str, Any]) -> None:
    """個別の履歴項目を表示"""
    with st.expander(f"📍 {item.get('location', '不明')} - {format_timestamp(item.get('timestamp', ''))}"):
        # 基本情報
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**プロバイダー:** {item.get('llm_provider', '不明')}")
            if item.get('success'):
                st.success("生成成功")
            else:
                st.error("生成失敗")
        
        with col2:
            # メタデータ
            metadata = item.get('generation_metadata', {})
            if metadata:
                temp = metadata.get('temperature')
                if temp:
                    st.write(f"**気温:** {temp}°C")
                weather = metadata.get('weather_condition')
                if weather:
                    st.write(f"**天気:** {weather}")
        
        # コメント
        if item.get('final_comment'):
            st.text_area(
                "生成されたコメント",
                value=item['final_comment'],
                height=100,
                disabled=True,
                key=f"history_{item.get('timestamp', '')}_{item.get('location', '')}"
            )


def format_timestamp(timestamp: str) -> str:
    """タイムスタンプをフォーマット"""
    if not timestamp:
        return "不明"
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        jst = pytz.timezone('Asia/Tokyo')
        dt_jst = dt.astimezone(jst)
        return dt_jst.strftime('%m/%d %H:%M')
    except (ValueError, TypeError, AttributeError):
        return timestamp


def export_history(history: list[dict[str, Any]]) -> None:
    """履歴をJSON形式でダウンロード"""
    if not history:
        st.warning("エクスポートする履歴がありません")
        return
    
    # JSON形式でエクスポート
    json_str = json.dumps(history, ensure_ascii=False, indent=2)
    
    # ダウンロードボタン
    st.download_button(
        label="📥 JSONファイルをダウンロード",
        data=json_str,
        file_name=f"comment_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
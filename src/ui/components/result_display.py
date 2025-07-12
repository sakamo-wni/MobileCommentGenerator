"""結果表示コンポーネント"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def display_single_result(result: Dict[str, Any]) -> None:
    """単一地点の結果を表示"""
    location = result.get('location', '不明')
    success = result.get('success', False)
    comment = result.get('comment', '')
    error = result.get('error')
    
    if success and comment:
        st.success(f"✅ **{location}**")
        st.text_area(
            "生成されたコメント",
            value=comment,
            height=100,
            key=f"comment_{location}_{datetime.now().timestamp()}"
        )
        
        # メタデータの表示
        if 'result' in result and result['result']:
            metadata = result['result'].get('generation_metadata', {})
            if metadata:
                display_metadata(metadata, location)
    else:
        st.error(f"❌ **{location}**: {error}")


def display_metadata(metadata: Dict[str, Any], location: str) -> None:
    """メタデータを表示"""
    with st.expander(f"📊 {location}の詳細情報"):
        # 予報時刻
        forecast_time = metadata.get('forecast_time')
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
        
        # 天気タイムラインの表示
        weather_timeline = metadata.get('weather_timeline')
        if weather_timeline and isinstance(weather_timeline, dict):
            future_forecasts = weather_timeline.get('future_forecasts', [])
            if future_forecasts:
                st.markdown("**📅 翌日の天気予報:**")
                timeline_data = []
                for forecast in future_forecasts:
                    timeline_data.append({
                        "時刻": forecast.get('time', ''),
                        "天気": forecast.get('weather', ''),
                        "気温": f"{forecast.get('temperature', '')}°C",
                        "降水量": f"{forecast.get('precipitation', 0)}mm"
                    })
                if timeline_data:
                    df = pd.DataFrame(timeline_data)
                    st.dataframe(df, hide_index=True)


def display_batch_results(results: List[Dict[str, Any]]) -> None:
    """バッチ結果を表示"""
    if not results:
        st.info("結果がありません")
        return
    
    # サマリー表示
    total = len(results)
    success_count = sum(1 for r in results if r.get('success', False))
    
    if success_count == total:
        st.success(f"✅ すべての地点で生成成功！ ({success_count}/{total})")
    elif success_count > 0:
        st.warning(f"⚠️ 一部の地点で生成成功 ({success_count}/{total})")
    else:
        st.error(f"❌ すべての地点で生成失敗 (0/{total})")
    
    # 個別結果の表示
    for result in results:
        display_single_result(result)
        st.markdown("---")


def result_display(result_data: Optional[Dict[str, Any]]) -> None:
    """
    生成結果表示コンポーネント

    Args:
        result_data: 生成結果データ
    """
    if not result_data:
        st.info("👈 左側のパネルから地点とLLMプロバイダーを選択して、「コメント生成」ボタンをクリックしてください。")
        return
    
    # エラーチェック
    if not result_data.get('success'):
        error = result_data.get('error', '不明なエラー')
        st.error(f"⚠️ エラー: {error}")
        
        # エラー詳細があれば表示
        if result_data.get('errors'):
            with st.expander("エラー詳細"):
                for err in result_data['errors']:
                    st.warning(err)
        return
    
    # 複数地点の結果
    if 'results' in result_data:
        display_batch_results(result_data['results'])
    # 単一地点の結果（後方互換性）
    elif 'final_comment' in result_data:
        single_result = {
            'location': result_data.get('location', '不明'),
            'success': True,
            'comment': result_data['final_comment'],
            'result': result_data
        }
        display_single_result(single_result)
"""
Streamlit UIユーティリティ関数

Streamlit UI用のヘルパー関数とユーティリティ
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import streamlit as st

from src.utils.exceptions import FileOperationError, DataValidationError


def load_locations() -> List[str]:
    """
    地点データを読み込む

    Returns:
        地点名のリスト
    """
    try:
        # frontend/public/地点名.csvファイルを読み込み（正しい地点マスター）
        csv_path = "frontend/public/地点名.csv"
        if os.path.exists(csv_path):
            # CSVファイルとして正しく解析
            df = pd.read_csv(csv_path, encoding="utf-8")
            # 地点名カラムのみを取得
            if "地点名" in df.columns:
                locations = df["地点名"].tolist()
            else:
                # ヘッダーがない場合は最初のカラムを使用
                locations = df.iloc[:, 0].tolist()
        else:
            # フォールバック：src/data/Chiten.csvを試す
            fallback_path = "src/data/Chiten.csv"
            if os.path.exists(fallback_path):
                with open(fallback_path, "r", encoding="utf-8") as f:
                    locations = [line.strip() for line in f.readlines() if line.strip()]
            else:
                # ファイルが存在しない場合のデフォルト地点
                locations = [
                    "東京",
                    "大阪",
                    "名古屋",
                    "福岡",
                    "札幌",
                    "仙台",
                    "広島",
                    "那覇",
                    "新潟",
                    "金沢",
                    "静岡",
                    "岡山",
                    "熊本",
                    "鹿児島",
                    "青森",
                    "盛岡",
                ]
    except FileNotFoundError as e:
        st.warning(f"地点データファイルが見つかりません: {str(e)}")
        # エラー時のデフォルト地点
        locations = ["東京", "大阪", "名古屋", "福岡", "札幌"]
    except (IOError, OSError) as e:
        st.error(f"地点データの読み込みエラー: {str(e)}")
        raise FileOperationError(f"地点データの読み込みに失敗: {str(e)}")
    except pd.errors.EmptyDataError:
        st.error("地点データファイルが空です")
        locations = ["東京", "大阪", "名古屋", "福岡", "札幌"]

    return sorted(locations)


def filter_locations(locations: List[str], query: str) -> List[str]:
    """
    地点リストを検索クエリでフィルタリング

    Args:
        locations: 地点名のリスト
        query: 検索クエリ

    Returns:
        フィルタリングされた地点名のリスト
    """
    if not query:
        return locations

    query_lower = query.lower()
    filtered = [loc for loc in locations if query_lower in loc.lower()]

    return filtered


def copy_to_clipboard(text: str) -> bool:
    """
    テキストをクリップボードにコピー

    Args:
        text: コピーするテキスト

    Returns:
        成功した場合True
    """
    # StreamlitでのJavaScript実行
    js_code = f"""
    <script>
    navigator.clipboard.writeText(`{text}`).then(function() {{
        console.log('Copying to clipboard was successful!');
    }}, function(err) {{
        console.error('Could not copy text: ', err);
    }});
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)
    return True


def save_to_history(result: Dict[str, Any], location: str, llm_provider: str):
    """
    生成結果を履歴に保存

    Args:
        result: 生成結果
        location: 地点名
        llm_provider: LLMプロバイダー名
    """
    history_file = "data/generation_history.json"

    # 履歴データの作成
    history_item = {
        "timestamp": datetime.now().isoformat(),
        "location": location,
        "llm_provider": llm_provider,
        "final_comment": result.get("final_comment", ""),
        "success": result.get("success", False),
        "generation_metadata": result.get("generation_metadata", {}),
        "error": result.get("error", None),
    }

    try:
        # 既存履歴の読み込み
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []

        # 新しい履歴を追加
        history.append(history_item)

        # 履歴サイズの制限（最新1000件まで）
        if len(history) > 1000:
            history = history[-1000:]

        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(history_file), exist_ok=True)

        # ファイルに保存
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    except (IOError, OSError) as e:
        st.error(f"履歴保存エラー: {str(e)}")
        raise FileOperationError(f"履歴の保存に失敗: {str(e)}")
    except json.JSONDecodeError as e:
        st.error(f"JSONデータの解析エラー: {str(e)}")
        raise DataValidationError(f"履歴データの形式が無効: {str(e)}")


def load_history() -> List[Dict[str, Any]]:
    """
    履歴データを読み込む

    Returns:
        履歴データのリスト
    """
    history_file = "data/generation_history.json"

    try:
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                return history
    except (IOError, OSError) as e:
        st.error(f"履歴読み込みエラー: {str(e)}")
    except json.JSONDecodeError as e:
        st.error(f"履歴データの形式が無効です: {str(e)}")

    return []


def format_timestamp(dt: datetime) -> str:
    """
    タイムスタンプをフォーマット

    Args:
        dt: datetime オブジェクト

    Returns:
        フォーマットされた日時文字列
    """
    return dt.strftime("%Y/%m/%d %H:%M:%S")


def validate_api_keys() -> Dict[str, bool]:
    """
    APIキーの有効性を検証

    Returns:
        各プロバイダーの検証結果
    """
    validation_results = {}

    # OpenAI
    openai_key = st.session_state.get("openai_api_key", "")
    validation_results["openai"] = bool(openai_key and len(openai_key) > 10)

    # Gemini
    gemini_key = st.session_state.get("gemini_api_key", "")
    validation_results["gemini"] = bool(gemini_key and len(gemini_key) > 10)

    # Anthropic
    anthropic_key = st.session_state.get("anthropic_api_key", "")
    validation_results["anthropic"] = bool(anthropic_key and len(anthropic_key) > 10)

    return validation_results


def get_theme_colors() -> Dict[str, str]:
    """
    テーマカラーを取得

    Returns:
        カラー設定の辞書
    """
    return {
        "primary": "#1E88E5",
        "secondary": "#E3F2FD",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",
        "background": "#FFFFFF",
        "text": "#333333",
    }


def create_download_link(data: str, filename: str, mime_type: str = "text/plain") -> str:
    """
    ダウンロードリンクを作成

    Args:
        data: ダウンロードするデータ
        filename: ファイル名
        mime_type: MIMEタイプ

    Returns:
        ダウンロードリンクのHTML
    """
    import base64

    b64 = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">📥 {filename}をダウンロード</a>'
    return href


def export_history_csv(history: List[Dict[str, Any]]) -> str:
    """
    履歴をCSV形式でエクスポート

    Args:
        history: 履歴データ

    Returns:
        CSV形式の文字列
    """
    try:
        # DataFrameに変換
        df_data = []
        for item in history:
            row = {
                "日時": item.get("timestamp", ""),
                "地点": item.get("location", ""),
                "LLMプロバイダー": item.get("llm_provider", ""),
                "生成コメント": item.get("final_comment", ""),
                "成功": item.get("success", False),
                "エラー": item.get("error", ""),
            }
            df_data.append(row)

        df = pd.DataFrame(df_data)
        return df.to_csv(index=False, encoding="utf-8-sig")

    except (ValueError, TypeError) as e:
        st.error(f"CSV出力エラー: {str(e)}")
        return ""
    except pd.errors.EmptyDataError:
        st.warning("出力する履歴データがありません")
        return ""


def get_statistics(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    履歴統計を取得

    Args:
        history: 履歴データ

    Returns:
        統計情報の辞書
    """
    if not history:
        return {}

    try:
        total_generations = len(history)
        successful_generations = sum(1 for item in history if item.get("success", False))
        success_rate = (
            (successful_generations / total_generations) * 100 if total_generations > 0 else 0
        )

        # 地点別統計
        location_counts = {}
        for item in history:
            location = item.get("location", "不明")
            location_counts[location] = location_counts.get(location, 0) + 1

        # LLMプロバイダー別統計
        provider_counts = {}
        for item in history:
            provider = item.get("llm_provider", "不明")
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        # 最新の生成日時
        latest_generation = max((item.get("timestamp", "") for item in history), default="")

        return {
            "total_generations": total_generations,
            "successful_generations": successful_generations,
            "success_rate": success_rate,
            "location_counts": location_counts,
            "provider_counts": provider_counts,
            "latest_generation": latest_generation,
        }

    except (ValueError, TypeError, KeyError) as e:
        st.error(f"統計計算エラー: {str(e)}")
        return {}


def reset_session_state():
    """
    セッション状態をリセット
    """
    keys_to_reset = ["current_result", "is_generating", "generation_history"]

    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]


def handle_error(error: Exception, context: str = ""):
    """
    エラーハンドリング

    Args:
        error: 発生した例外
        context: エラーのコンテキスト
    """
    error_message = f"{context}: {str(error)}" if context else str(error)
    st.error(f"❌ エラーが発生しました: {error_message}")

    # デバッグモードが有効な場合は詳細情報を表示
    if st.session_state.get("debug_mode", False):
        with st.expander("エラー詳細"):
            st.exception(error)

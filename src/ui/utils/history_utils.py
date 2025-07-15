"""
履歴管理関連のユーティリティ関数

生成結果の保存、読み込み、エクスポートなど
"""

import json
from pathlib import Path
from typing import Any
from datetime import datetime
import pandas as pd
import streamlit as st


def save_to_history(result: dict[str, Any], location: str, llm_provider: str):
    """
    生成結果を履歴に保存

    Args:
        result: 生成結果
        location: 地点名
        llm_provider: LLMプロバイダー名
    """
    history_file = Path("data/generation_history.json")

    # 履歴データの作成
    history_item = {
        "timestamp": datetime.now().isoformat(),
        "location": location,
        "llm_provider": llm_provider,
        "comment": result.get("final_comment", ""),  # APIと互換性のため comment フィールドも追加
        "final_comment": result.get("final_comment", ""),
        "advice_comment": result.get("generation_metadata", {}).get("selection_metadata", {}).get("selected_advice_comment", ""),
        "success": result.get("success", False),
        "generation_metadata": result.get("generation_metadata", {}),
        "error": result.get("error", None),
    }

    try:
        # 既存履歴の読み込み
        if history_file.exists():
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
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # ファイルに保存
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    except Exception as e:
        st.error(f"履歴保存エラー: {str(e)}")


def load_history() -> list[dict[str, Any]]:
    """
    履歴データを読み込む

    Returns:
        履歴データのリスト
    """
    history_file = Path("data/generation_history.json")

    try:
        if history_file.exists():
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                return history
    except Exception as e:
        st.error(f"履歴読み込みエラー: {str(e)}")

    return []


def export_history_csv(history: list[dict[str, Any]]) -> str:
    """
    履歴データをCSV形式でエクスポート

    Args:
        history: 履歴データリスト

    Returns:
        CSV形式の文字列
    """
    if not history:
        return ""

    # DataFrameに変換
    rows = []
    for item in history:
        row = {
            "timestamp": item.get("timestamp", ""),
            "location": item.get("location", ""),
            "final_comment": item.get("final_comment", ""),
            "advice_comment": item.get("advice_comment", ""),
            "llm_provider": item.get("llm_provider", ""),
            "success": item.get("success", False),
            "execution_time_ms": item.get("generation_metadata", {}).get("execution_time_ms", 0),
            "retry_count": item.get("generation_metadata", {}).get("retry_count", 0),
            "weather_condition": item.get("generation_metadata", {}).get("weather_condition", ""),
            "temperature": item.get("generation_metadata", {}).get("temperature", ""),
            "error": item.get("error", ""),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    
    # タイムスタンプでソート
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp", ascending=False)

    # CSV形式に変換
    return df.to_csv(index=False, encoding="utf-8")
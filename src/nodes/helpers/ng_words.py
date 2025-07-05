"""NGワード管理モジュール"""

from typing import List
import logging
import os
import yaml

logger = logging.getLogger(__name__)


def get_ng_words() -> List[str]:
    """NGワードリストを取得"""
    # 設定ファイルから読み込み
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "ng_words.yaml")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config.get("ng_words", [])
    except FileNotFoundError:
        logger.warning(f"NG words config file not found: {config_path}")
        # フォールバック
        return [
            "災害",
            "危険",
            "注意",
            "警告",
            "絶対",
            "必ず",
            "間違いない",
            "くそ",
            "やばい",
            "最悪",
        ]
    except Exception as e:
        logger.error(f"Error loading NG words config: {e}")
        # フォールバック
        return [
            "災害",
            "危険",
            "注意",
            "警告",
            "絶対",
            "必ず",
            "間違いない",
            "くそ",
            "やばい",
            "最悪",
        ]
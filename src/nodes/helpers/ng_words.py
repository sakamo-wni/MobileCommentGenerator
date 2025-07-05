"""NGワード管理モジュール"""

from typing import List
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

# デフォルトのNGワードリスト
DEFAULT_NG_WORDS = [
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


def get_ng_words() -> List[str]:
    """NGワードリストを取得"""
    # 設定ファイルから読み込み
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "ng_words.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config.get("ng_words", [])
    except FileNotFoundError:
        logger.warning(f"NG words config file not found: {config_path}")
        # フォールバック
        return DEFAULT_NG_WORDS
    except Exception as e:
        logger.error(f"Error loading NG words config: {e}")
        # フォールバック
        return DEFAULT_NG_WORDS
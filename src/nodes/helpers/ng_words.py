"""NGワード管理モジュール"""

from typing import List, Dict, Any
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


def check_ng_words(text: str) -> Dict[str, Any]:
    """テキストにNGワードが含まれているかチェック
    
    Args:
        text: チェック対象のテキスト
        
    Returns:
        Dict with keys:
            - is_valid: NGワードが含まれていない場合True
            - found_words: 見つかったNGワードのリスト
    """
    ng_words = get_ng_words()
    found_words = []
    
    for ng_word in ng_words:
        if ng_word in text:
            found_words.append(ng_word)
    
    return {
        "is_valid": len(found_words) == 0,
        "found_words": found_words
    }
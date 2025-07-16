"""評価設定ローダー"""

from __future__ import annotations
import yaml
from typing import Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EvaluationConfigLoader:
    """評価設定を読み込むクラス"""
    
    def __init__(self, config_path: str = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス（Noneの場合はデフォルトパスを使用）
        """
        if config_path is None:
            config_path = Path(__file__).parent / "evaluation_config.yaml"
        self.config_path = Path(config_path)
        self._config = None
    
    def load_config(self) -> dict[str, Any]:
        """設定を読み込む"""
        if self._config is None:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
                logger.info(f"評価設定を読み込みました: {self.config_path}")
            except Exception as e:
                logger.error(f"評価設定の読み込みに失敗しました: {e}")
                # デフォルト設定を返す
                self._config = self._get_default_config()
        
        return self._config
    
    def get_inappropriate_patterns(self, mode: str = "relaxed") -> list[str]:
        """不適切表現パターンを取得"""
        config = self.load_config()
        patterns = []
        mode_config = config.get("evaluation_modes", {}).get(mode, {})
        enabled_checks = mode_config.get("enabled_checks", [])
        
        pattern_config = config.get("evaluation_patterns", {}).get("inappropriate_patterns", {})
        
        if "extreme_inappropriate" in enabled_checks:
            patterns.extend(pattern_config.get("extreme", []))
        if "offensive_inappropriate" in enabled_checks:
            patterns.extend(pattern_config.get("offensive", []))
        if "negative_inappropriate" in enabled_checks:
            patterns.extend(pattern_config.get("negative", []))
        if "warning_inappropriate" in enabled_checks:
            patterns.extend(pattern_config.get("warning", []))
        
        return patterns
    
    def get_contradiction_patterns(self, mode: str = "relaxed") -> list[dict[str, list[str]]]:
        """矛盾パターンを取得"""
        config = self.load_config()
        mode_config = config.get("evaluation_modes", {}).get(mode, {})
        enabled_checks = mode_config.get("enabled_checks", [])
        
        all_patterns = config.get("evaluation_patterns", {}).get("contradiction_patterns", {})
        
        if "all_contradictions" in enabled_checks:
            # 全ての矛盾パターンを返す
            return self._flatten_contradiction_patterns(all_patterns)
        elif "major_contradictions" in enabled_checks:
            # 主要な矛盾パターンのみ
            return self._flatten_contradiction_patterns({
                "weather": all_patterns.get("weather", [])
            })
        elif "obvious_contradictions" in enabled_checks:
            # 明らかな矛盾のみ
            weather_patterns = all_patterns.get("weather", [])
            return weather_patterns[:2] if len(weather_patterns) >= 2 else weather_patterns
        
        return []
    
    def _flatten_contradiction_patterns(self, patterns: dict) -> list[dict[str, list[str]]]:
        """矛盾パターンをフラット化"""
        result = []
        for category, items in patterns.items():
            result.extend(items)
        return result
    
    def get_mode_config(self, mode: str = "relaxed") -> dict[str, Any]:
        """モード別設定を取得"""
        config = self.load_config()
        return config.get("evaluation_modes", {}).get(mode, {})
    
    def get_positive_expressions(self) -> list[str]:
        """ポジティブ表現を取得"""
        config = self.load_config()
        return config.get("evaluation_patterns", {}).get("positive_expressions", [])
    
    def get_engagement_elements(self) -> list[str]:
        """エンゲージメント要素を取得"""
        config = self.load_config()
        return config.get("evaluation_patterns", {}).get("engagement_elements", [])
    
    def _get_default_config(self) -> dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            "evaluation_patterns": {
                "inappropriate_patterns": {
                    "extreme": ["死|殺|自殺|地獄|絶望|最悪.*死", "危険.*死|警告.*死|やばい.*死"]
                },
                "contradiction_patterns": {},
                "positive_expressions": ["素敵", "素晴らしい", "快適"],
                "engagement_elements": ["[!！♪☆★]", "〜|～"]
            },
            "evaluation_modes": {
                "relaxed": {
                    "thresholds": {
                        "total_score": 0.3,
                        "appropriateness": 0.2,
                        "consistency": 0.2
                    },
                    "enabled_checks": ["extreme_inappropriate"]
                }
            }
        }
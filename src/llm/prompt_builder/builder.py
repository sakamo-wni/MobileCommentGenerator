"""
Main prompt builder class

メインのプロンプトビルダークラス
"""

from __future__ import annotations
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from src.types import CommentPair

from .models import PromptTemplate
from .template_loader import TemplateLoader
from .utils import get_time_of_day_category, get_season_category

logger = logging.getLogger(__name__)


class CommentPromptBuilder:
    """コメント生成用プロンプトビルダー"""
    
    # キャッシュ有効期間のデフォルト値（秒）
    DEFAULT_CACHE_DURATION = 3600

    def __init__(self, template_dir: Optional[Path] = None, 
                 cache_duration: float = DEFAULT_CACHE_DURATION, 
                 strict_validation: bool = False):
        """
        Args:
            template_dir: テンプレートディレクトリのパス
            cache_duration: キャッシュ有効期間（秒）。デフォルトは3600秒（1時間）
            strict_validation: 厳格な検証モード。Trueの場合、テンプレート検証エラーで例外を発生
        """
        self.template_loader = TemplateLoader(template_dir, strict_validation)
        self._templates_cache: Optional[PromptTemplate] = None
        self._cache_time: float = 0
        self._cache_duration: float = cache_duration
        
    @property
    def templates(self) -> PromptTemplate:
        """テンプレートを取得（キャッシュ機能付き）"""
        current_time = time.time()
        
        # キャッシュが無効または期限切れの場合
        if self._templates_cache is None or (current_time - self._cache_time) > self._cache_duration:
            self._templates_cache = self.template_loader.load_all_templates()
            self._cache_time = current_time
            logger.info("テンプレートキャッシュを更新しました")
        
        return self._templates_cache

    def reload_templates(self, force: bool = False):
        """テンプレートを再読み込み
        
        Args:
            force: キャッシュを無視して強制的に再読み込み
        """
        if force:
            self._templates_cache = None
            self._cache_time = 0
            logger.info("テンプレートを強制再読み込みしました")
        
        # templatesプロパティにアクセスしてキャッシュを更新
        _ = self.templates

    def build_prompt(
        self,
        weather_data: WeatherForecast | dict[str, Any],
        past_comments: Optional[list[PastComment]] = None,
        location: str = "",
        selected_pair: Optional[CommentPair] = None
    ) -> str:
        """
        コメント生成用プロンプトを構築

        Args:
            weather_data: 天気予報データ
            past_comments: 過去コメントリスト
            location: 地点名
            selected_pair: 選択されたコメントペア

        Returns:
            str: 構築されたプロンプト
        """
        try:
            # 基本情報の取得
            weather_info = self._extract_weather_info(weather_data)
            past_examples = self._format_past_comments(past_comments, selected_pair)

            # 天気条件に応じた追加指示
            weather_guidance = self._get_weather_specific_guidance(
                weather_info["weather_description"]
            )

            # 季節・時刻に応じた調整
            seasonal_guidance = self._get_seasonal_guidance(weather_info["current_time"])
            time_guidance = self._get_time_specific_guidance(weather_info["current_time"])

            # プロンプト構築
            prompt = self.templates.base_template.format(
                location=location or weather_info.get("location", ""),
                weather_description=weather_info["weather_description"],
                temperature=weather_info["temperature"],
                humidity=weather_info["humidity"],
                wind_speed=weather_info["wind_speed"],
                current_time=weather_info["current_time"],
                past_comments_examples=past_examples,
            )

            # 追加指示を追加
            if weather_guidance:
                prompt += f"\n\n## 天気別の留意点\n{weather_guidance}"

            if seasonal_guidance:
                prompt += f"\n\n## 季節の表現\n{seasonal_guidance}"

            if time_guidance:
                prompt += f"\n\n## 時間帯の表現\n{time_guidance}"

            return prompt

        except Exception as e:
            logger.error(f"プロンプト構築エラー: {e}")
            # フォールバックプロンプトを使用
            return self._build_fallback_prompt(weather_data, location)

    def _extract_weather_info(self, weather_data: WeatherForecast | dict[str, Any]) -> dict[str, Any]:
        """天気情報を抽出
        
        Args:
            weather_data: 天気データ
            
        Returns:
            抽出された天気情報の辞書
        """
        if isinstance(weather_data, dict):
            return {
                "weather_description": weather_data.get("weather", "不明"),
                "temperature": weather_data.get("temperature", 0),
                "humidity": weather_data.get("humidity", 0),
                "wind_speed": weather_data.get("wind_speed", 0),
                "current_time": weather_data.get(
                    "datetime", datetime.now()
                ).strftime("%Y年%m月%d日 %H時%M分"),
            }
        else:
            # WeatherForecast オブジェクトの場合
            return {
                "weather_description": getattr(weather_data, "weather_description", "不明"),
                "temperature": getattr(weather_data, "temperature", 0),
                "humidity": getattr(weather_data, "humidity", 0),
                "wind_speed": getattr(weather_data, "wind_speed", 0),
                "current_time": getattr(
                    weather_data, "datetime", datetime.now()
                ).strftime("%Y年%m月%d日 %H時%M分"),
            }

    def _format_past_comments(
        self,
        past_comments: Optional[list[PastComment]],
        selected_pair: Optional[CommentPair] = None
    ) -> str:
        """過去コメントをフォーマット
        
        Args:
            past_comments: 過去コメントリスト
            selected_pair: 選択されたコメントペア
            
        Returns:
            フォーマットされた過去コメント文字列
        """
        if not past_comments:
            return "（過去のコメント例がありません）"

        examples = []
        
        # 選択されたペアがある場合は最初に表示
        if selected_pair:
            examples.append(
                f"■ 選択されたコメントペア:\n"
                f"  天気: {selected_pair.weather_comment.comment_text}\n"
                f"  アドバイス: {selected_pair.advice_comment.comment_text}"
            )

        # その他の過去コメント（最大5件）
        for i, comment in enumerate(past_comments[:5], 1):
            examples.append(f"{i}. {comment.comment_text}")

        return "\n".join(examples)

    def _get_weather_specific_guidance(self, weather_description: str) -> str:
        """天気別の追加指示を取得
        
        Args:
            weather_description: 天気の説明
            
        Returns:
            天気別の追加指示
        """
        weather_desc_lower = weather_description.lower()
        
        # 天気タイプの判定
        if "雨" in weather_desc_lower:
            weather_type = "雨"
        elif "雪" in weather_desc_lower:
            weather_type = "雪"
        elif "晴" in weather_desc_lower:
            weather_type = "晴れ"
        elif "曇" in weather_desc_lower:
            weather_type = "曇り"
        else:
            weather_type = None

        if weather_type and weather_type in self.templates.weather_specific:
            return self.templates.weather_specific[weather_type]
        
        return ""

    def _get_seasonal_guidance(self, current_time_str: str) -> str:
        """季節別の追加指示を取得
        
        Args:
            current_time_str: 現在時刻文字列
            
        Returns:
            季節別の追加指示
        """
        try:
            # 月を抽出
            month = int(current_time_str.split("月")[0].split("年")[1])
            season = get_season_category(month)
            
            if season in self.templates.seasonal_adjustments:
                return self.templates.seasonal_adjustments[season]
        except Exception as e:
            logger.debug(f"季節判定エラー: {e}")
        
        return ""

    def _get_time_specific_guidance(self, current_time_str: str) -> str:
        """時間帯別の追加指示を取得
        
        Args:
            current_time_str: 現在時刻文字列
            
        Returns:
            時間帯別の追加指示
        """
        try:
            # 時間を抽出
            hour = int(current_time_str.split("時")[0].split(" ")[-1])
            time_category = get_time_of_day_category(hour)
            
            if time_category in self.templates.time_specific:
                return self.templates.time_specific[time_category]
        except Exception as e:
            logger.debug(f"時間帯判定エラー: {e}")
        
        return ""

    def _build_fallback_prompt(
        self,
        weather_data: WeatherForecast | dict[str, Any],
        location: str = ""
    ) -> str:
        """フォールバックプロンプトを構築
        
        Args:
            weather_data: 天気データ
            location: 地点名
            
        Returns:
            フォールバックプロンプト
        """
        weather_info = self._extract_weather_info(weather_data)
        
        return self.templates.fallback_template.format(
            location=location,
            weather=weather_info["weather_description"],
            temperature=weather_info["temperature"]
        )
"""
プロンプトビルダー - コメント生成用プロンプト構築

このモジュールは、天気情報と過去コメントを基に、
効果的な天気コメント生成用プロンプトを構築します。
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Union
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from src.types import CommentPair

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """プロンプトテンプレート"""

    base_template: str
    weather_specific: dict[str, str]
    seasonal_adjustments: dict[str, str]
    time_specific: dict[str, str]
    fallback_template: str
    example_templates: dict[str, str]


class TemplateLoader:
    """テンプレートファイルの読み込みを管理"""

    def __init__(self, template_dir: Path | None = None, strict_validation: bool = False):
        """
        Args:
            template_dir: テンプレートディレクトリのパス
            strict_validation: 厳格な検証モード。Trueの場合、検証エラーで例外を発生
        """
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.strict_validation = strict_validation

    def load_text_file(self, filename: str) -> str:
        """テキストファイルを読み込み"""
        file_path = self.template_dir / filename
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"テンプレートファイルが見つかりません: {filename} ({file_path})")
            raise
        except Exception as e:
            logger.error(f"テンプレート読み込みエラー: {filename} - {e}")
            raise

    def load_json_file(self, filename: str) -> dict[str, str]:
        """JSONファイルを読み込み"""
        file_path = self.template_dir / filename
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"JSONファイルが見つかりません: {filename} ({file_path})")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析エラー: {filename} - {e}")
            return {}
        except Exception as e:
            logger.error(f"JSON読み込みエラー: {filename} - {e}")
            return {}

    def load_all_templates(self) -> PromptTemplate:
        """すべてのテンプレートを読み込み"""
        try:
            template = PromptTemplate(
                base_template=self.load_text_file("base.txt"),
                weather_specific=self.load_json_file("weather_specific.json"),
                seasonal_adjustments=self.load_json_file("seasonal_adjustments.json"),
                time_specific=self.load_json_file("time_specific.json"),
                fallback_template=self.load_text_file("fallback.txt"),
                example_templates=self.load_json_file("examples.json")
            )
            
            # テンプレートバリデーション
            self._validate_templates(template)
            
            return template
        except ValueError:
            # 検証エラーは再発生させる（strict_validationモードのため）
            raise
        except Exception as e:
            logger.error(f"テンプレート読み込み失敗、デフォルトを使用: {e}")
            return self._get_default_templates()

    def _validate_templates(self, template: PromptTemplate) -> None:
        """テンプレートの妥当性を検証
        
        Args:
            template: 検証対象のテンプレート
            
        Raises:
            ValueError: 必須フィールドが不足している場合（strict_validationがTrueの場合）
        """
        validation_errors = []
        
        # 必須プレースホルダーの確認
        required_placeholders = [
            "location", "weather_description", "temperature",
            "humidity", "wind_speed", "current_time", "past_comments_examples"
        ]
        
        for placeholder in required_placeholders:
            if f"{{{placeholder}}}" not in template.base_template:
                error_msg = f"必須プレースホルダー '{{{placeholder}}}' が base.txt に含まれていません"
                validation_errors.append(error_msg)
                logger.warning(error_msg)
        
        # 必須キーの確認
        required_weather_conditions = ["晴", "雨", "雪", "曇"]
        for condition in required_weather_conditions:
            if not any(condition in key for key in template.weather_specific.keys()):
                error_msg = f"天気条件 '{condition}' の指示がweather_specific.jsonに含まれていません"
                validation_errors.append(error_msg)
                logger.warning(error_msg)
        
        # 季節の確認
        required_seasons = ["春", "夏", "秋", "冬"]
        for season in required_seasons:
            if season not in template.seasonal_adjustments:
                error_msg = f"季節 '{season}' の調整がseasonal_adjustments.jsonに含まれていません"
                validation_errors.append(error_msg)
                logger.warning(error_msg)
        
        # 時間帯の確認
        required_times = ["朝", "昼", "夕方", "夜"]
        for time_period in required_times:
            if time_period not in template.time_specific:
                error_msg = f"時間帯 '{time_period}' の指示がtime_specific.jsonに含まれていません"
                validation_errors.append(error_msg)
                logger.warning(error_msg)
        
        # 厳格モードの場合、エラーがあれば例外を発生
        if self.strict_validation and validation_errors:
            raise ValueError(f"テンプレート検証エラー:\n" + "\n".join(validation_errors))

    def _get_default_templates(self) -> PromptTemplate:
        """デフォルトテンプレート（フォールバック用）"""
        return PromptTemplate(
            base_template="15文字以内で天気コメントを生成してください。\n\n天気コメント:",
            weather_specific={},
            seasonal_adjustments={},
            time_specific={},
            fallback_template="15文字以内で天気コメントを生成してください。\n\n天気コメント:",
            example_templates={}
        )


class CommentPromptBuilder:
    """コメント生成用プロンプトビルダー"""
    
    # キャッシュ有効期間のデフォルト値（秒）
    DEFAULT_CACHE_DURATION = 3600

    def __init__(self, template_dir: Path | None = None, cache_duration: float = DEFAULT_CACHE_DURATION, strict_validation: bool = False):
        """
        Args:
            template_dir: テンプレートディレクトリのパス
            cache_duration: キャッシュ有効期間（秒）。デフォルトは3600秒（1時間）
            strict_validation: 厳格な検証モード。Trueの場合、テンプレート検証エラーで例外を発生
        """
        self.template_loader = TemplateLoader(template_dir, strict_validation)
        self._templates_cache: PromptTemplate | None = None
        self._cache_time: float = 0
        self._cache_duration: float = cache_duration
        
    @property
    def templates(self) -> PromptTemplate:
        """テンプレートを取得（キャッシュ機能付き）"""
        import time
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
        weather_data: Union[WeatherForecast, dict[str, Any], None],
        past_comments: list[PastComment] | None = None,
        location: str = "",
        selected_pair: CommentPair | None = None
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

            logger.debug(f"プロンプト構築完了 - 長さ: {len(prompt)}文字")
            return prompt

        except Exception as e:
            logger.error(f"プロンプト構築エラー: {str(e)}")
            return self._get_fallback_prompt(location, weather_data)

    def _extract_weather_info(self, weather_data: Union[WeatherForecast, dict[str, Any], None]) -> dict[str, Any]:
        """天気データから情報を抽出"""
        if not weather_data:
            return {
                "weather_description": "不明",
                "temperature": "不明",
                "humidity": "不明",
                "wind_speed": "不明",
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }

        return {
            "location": getattr(weather_data, "location", ""),
            "weather_description": getattr(weather_data, "weather_description", "不明"),
            "temperature": getattr(weather_data, "temperature", "不明"),
            "humidity": getattr(weather_data, "humidity", "不明"),
            "wind_speed": getattr(weather_data, "wind_speed", "不明"),
            "current_time": getattr(weather_data, "datetime", datetime.now()).strftime(
                "%Y-%m-%d %H:%M"
            ),
        }

    def _format_past_comments(self, past_comments: list[PastComment] | None, selected_pair: CommentPair | None) -> str:
        """過去コメントをフォーマット"""
        if not past_comments and not selected_pair:
            return "（過去のコメントデータなし）"

        examples = []

        # 選択されたペアを優先的に表示
        if selected_pair:
            if hasattr(selected_pair, "weather_comment") and selected_pair.weather_comment:
                comment = selected_pair.weather_comment
                text = getattr(comment, "comment_text", "")
                location = getattr(comment, "location", "不明")
                examples.append(f"- 「{text}」 (地点:{location})")

            if hasattr(selected_pair, "advice_comment") and selected_pair.advice_comment:
                comment = selected_pair.advice_comment
                text = getattr(comment, "comment_text", "")
                location = getattr(comment, "location", "不明")
                examples.append(f"- 「{text}」 (アドバイス, 地点:{location})")

        # その他の過去コメント（JSONLフォーマットに対応）
        if past_comments:
            # 多様性を確保するため、最大15件まで表示
            for comment in past_comments[:15]:
                # PastCommentオブジェクトの場合
                text = getattr(comment, "comment_text", str(comment))
                location = getattr(comment, "location", "不明")
                comment_type = getattr(comment, "comment_type", None)

                if comment_type:
                    examples.append(f"- 「{text}」 ({comment_type}, 地点:{location})")
                else:
                    examples.append(f"- 「{text}」 (地点:{location})")

        return "\n".join(examples) if examples else "（過去のコメントデータなし）"

    def _get_weather_specific_guidance(self, weather_description: str) -> str:
        """天気条件に応じた指示を取得"""
        for condition, guidance in self.templates.weather_specific.items():
            if condition in weather_description:
                return guidance
        return ""

    def _get_seasonal_guidance(self, current_time: str) -> str:
        """季節に応じた指示を取得"""
        try:
            dt = datetime.strptime(current_time, "%Y-%m-%d %H:%M")
            month = dt.month

            if month in [3, 4, 5]:
                season = "春"
            elif month in [6, 7, 8]:
                season = "夏"
            elif month in [9, 10, 11]:
                season = "秋"
            else:
                season = "冬"

            return self.templates.seasonal_adjustments.get(season, "")
        except Exception:
            return ""

    def _get_time_specific_guidance(self, current_time: str) -> str:
        """時間帯に応じた指示を取得"""
        try:
            dt = datetime.strptime(current_time, "%Y-%m-%d %H:%M")
            hour = dt.hour

            if 5 <= hour < 11:
                time_period = "朝"
            elif 11 <= hour < 17:
                time_period = "昼"
            elif 17 <= hour < 21:
                time_period = "夕方"
            else:
                time_period = "夜"

            return self.templates.time_specific.get(time_period, "")
        except Exception:
            return ""

    def _get_fallback_prompt(self, location: str, weather_data: Union[WeatherForecast, dict[str, Any], None]) -> str:
        """フォールバック用のシンプルなプロンプト"""
        try:
            return self.templates.fallback_template.format(location=location or '')
        except Exception:
            return f"15文字以内で{location or ''}の天気に適したコメントを生成してください。\n天気コメント:"

    def create_custom_prompt(
        self,
        template: str,
        weather_data: Union[WeatherForecast, dict[str, Any], None],
        past_comments: list[PastComment] | None = None,
        **kwargs: Any
    ) -> str:
        """
        カスタムテンプレートでプロンプト生成

        Args:
            template: カスタムテンプレート文字列
            weather_data: 天気データ
            past_comments: 過去コメント
            **kwargs: その他のパラメータ

        Returns:
            str: 構築されたプロンプト
        """
        weather_info = self._extract_weather_info(weather_data)
        past_examples = self._format_past_comments(past_comments, None)

        format_vars = {**weather_info, "past_comments_examples": past_examples, **kwargs}

        try:
            return template.format(**format_vars)
        except KeyError as e:
            logger.error(f"テンプレート変数不足: {str(e)}")
            return self._get_fallback_prompt(kwargs.get("location", ""), weather_data)

    def get_example_template(self, template_name: str) -> str | None:
        """例示テンプレートを取得"""
        return self.templates.example_templates.get(template_name)


def create_simple_prompt(weather_description: str, temperature: str, location: str = "") -> str:
    """シンプルなプロンプト生成（テスト用）"""
    return f"""天気が{weather_description}、気温{temperature}度の{location}について、15文字以内の天気コメントを生成してください。

天気コメント:"""


# 後方互換性のため、EXAMPLE_TEMPLATESを維持
EXAMPLE_TEMPLATES = {
    "basic": "15文字以内で{location}の天気コメントを生成してください。\n天気: {weather_description}\n気温: {temperature}°C\n\n天気コメント:",
    "detailed": "あなたは天気キャスターです。以下の天気情報を基に、視聴者に向けた15文字以内のコメントを生成してください。\n\n地点: {location}\n天気: {weather_description}\n気温: {temperature}°C\n時刻: {current_time}\n\n過去の例:\n{past_comments_examples}\n\n天気コメント:",
    "friendly": "親しみやすい天気コメントを15文字以内で生成してください。\n\n今の天気: {weather_description}\n気温: {temperature}°C\n場所: {location}\n\n天気コメント:",
}


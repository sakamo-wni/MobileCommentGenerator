"""LLMプロバイダーの基底クラス"""

from abc import ABC, abstractmethod
from typing import Any

from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair


class LLMProvider(ABC):
    """LLMプロバイダーの抽象基底クラス"""

    @abstractmethod
    def generate_comment(
        self, weather_data: WeatherForecast, past_comments: CommentPair, constraints: dict[str, Any]
    ) -> str:
        """
        天気コメントを生成する。

        Args:
            weather_data: 天気予報データ
            past_comments: 過去のコメントペア
            constraints: 制約条件（max_length, ng_words等）

        Returns:
            生成されたコメント文字列
        """
        pass

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        汎用的なテキスト生成を行う。

        Args:
            prompt: プロンプト文字列

        Returns:
            生成されたテキスト
        """
        pass

    def _build_prompt(
        self, weather_data: WeatherForecast, past_comments: CommentPair, constraints: dict[str, Any]
    ) -> str:
        """
        プロンプトを構築する共通メソッド。

        Args:
            weather_data: 天気予報データ
            past_comments: 過去のコメントペア
            constraints: 制約条件

        Returns:
            構築されたプロンプト文字列
        """
        from src.llm.prompt_templates import COMMENT_GENERATION_PROMPT

        # NGワードのフォーマット
        ng_words_str = "、".join(constraints.get("ng_words", []))

        # プロンプトの構築
        prompt = COMMENT_GENERATION_PROMPT.format(
            location=weather_data.location,
            weather_condition=weather_data.weather_description,
            temperature=weather_data.temperature,
            time_period=constraints.get("time_period", "昼"),
            weather_comment=past_comments.weather_comment.comment_text,
            advice_comment=past_comments.advice_comment.comment_text,
            ng_words=ng_words_str,
            max_length=constraints.get("max_length", 15),
        )

        return prompt


# エクスポート
__all__ = ["LLMProvider"]

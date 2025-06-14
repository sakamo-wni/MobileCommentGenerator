"""OpenAI APIプロバイダー"""

import logging
import time
from typing import Dict, Any

from openai import OpenAI

from src.llm.providers.base_provider import LLMProvider
from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI APIを使用するプロバイダー"""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        OpenAIプロバイダーの初期化。

        Args:
            api_key: OpenAI APIキー
            model: 使用するモデル名
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"Initialized OpenAI provider with model: {model}")

    def generate_comment(
        self, weather_data: WeatherForecast, past_comments: CommentPair, constraints: Dict[str, Any]
    ) -> str:
        """
        OpenAI APIを使用してコメントを生成。

        Args:
            weather_data: 天気予報データ
            past_comments: 過去のコメントペア
            constraints: 制約条件

        Returns:
            生成されたコメント
        """
        max_retries = 3
        retry_delay = 3  # 初期待機時間（秒）

        for attempt in range(max_retries):
            try:
                # プロンプトの構築
                prompt = self._build_prompt(weather_data, past_comments, constraints)

                # APIリクエスト
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "あなたは天気予報のコメント作成の専門家です。短く、親しみやすいコメントを生成してください。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=50,
                    n=1,
                )

                # レスポンスからコメントを抽出
                generated_comment = response.choices[0].message.content.strip()

                # 改行や余分な記号を除去
                generated_comment = generated_comment.replace("\n", "").strip('"')

                logger.info(f"Generated comment: {generated_comment}")
                return generated_comment

            except Exception as e:
                error_message = str(e)

                # Rate limit errorの場合はリトライ
                if "rate_limit_exceeded" in error_message or "429" in error_message:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2**attempt)  # 指数バックオフ
                        logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue

                logger.error(f"Error in OpenAI API call: {error_message}")
                raise

    def generate(self, prompt: str) -> str:
        """
        汎用的なテキスト生成を行う。

        Args:
            prompt: プロンプト文字列

        Returns:
            生成されたテキスト
        """
        max_retries = 3
        retry_delay = 3  # 初期待機時間（秒）

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Generating text with OpenAI {self.model} (attempt {attempt + 1}/{max_retries})"
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "あなたは役立つアシスタントです。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=500,
                )

                generated_text = response.choices[0].message.content
                logger.info(f"Generated text: {generated_text[:100]}...")

                return generated_text

            except Exception as e:
                error_message = str(e)

                # Rate limit errorの場合はリトライ
                if "rate_limit_exceeded" in error_message or "429" in error_message:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2**attempt)  # 指数バックオフ
                        logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue

                logger.error(f"OpenAI API error: {error_message}")
                raise


# エクスポート
__all__ = ["OpenAIProvider"]

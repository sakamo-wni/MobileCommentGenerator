"""Google Gemini APIプロバイダー"""

import logging
from typing import Dict, Any

import google.generativeai as genai

from src.llm.providers.base_provider import LLMProvider
from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini APIを使用するプロバイダー"""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        """
        Geminiプロバイダーの初期化。

        Args:
            api_key: Gemini APIキー
            model: 使用するモデル名
        """
        # タイムアウトを含む設定でAPIを初期化
        genai.configure(
            api_key=api_key,
            transport='rest',  # RESTトランスポートを使用
            client_options={'api_endpoint': 'https://generativelanguage.googleapis.com'}
        )
        self.model = genai.GenerativeModel(model)
        self.model_name = model
        logger.info(f"Initialized Gemini provider with model: {model}")

    def generate_comment(
        self, weather_data: WeatherForecast, past_comments: CommentPair, constraints: Dict[str, Any]
    ) -> str:
        """
        Gemini APIを使用してコメントを生成。

        Args:
            weather_data: 天気予報データ
            past_comments: 過去のコメントペア
            constraints: 制約条件

        Returns:
            生成されたコメント
        """
        try:
            # プロンプトの構築
            prompt = self._build_prompt(weather_data, past_comments, constraints)

            # システムプロンプトを含めた完全なプロンプト
            full_prompt = (
                "あなたは天気予報のコメント作成の専門家です。"
                "短く、親しみやすいコメントを生成してください。\n\n"
                f"{prompt}"
            )

            # APIリクエスト
            # タイムアウトエラーを回避するため、短いレスポンスを要求
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=50,
                    candidate_count=1,  # 候補数を1に制限
                )
            )

            # レスポンスからコメントを抽出
            generated_comment = response.text.strip()

            # 改行や余分な記号を除去
            generated_comment = generated_comment.replace("\n", "").strip('"')

            logger.info(f"Generated comment: {generated_comment}")
            return generated_comment

        except Exception as e:
            logger.error(f"Error in Gemini API call: {str(e)}")
            raise

    def generate(self, prompt: str) -> str:
        """
        汎用的なテキスト生成を行う。

        Args:
            prompt: プロンプト文字列

        Returns:
            生成されたテキスト
        """
        try:
            logger.info(f"Generating text with Gemini")

            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                    candidate_count=1,  # 候補数を1に制限
                )
            )

            generated_text = response.text
            logger.info(f"Generated text: {generated_text[:100]}...")

            return generated_text

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise


# エクスポート
__all__ = ["GeminiProvider"]

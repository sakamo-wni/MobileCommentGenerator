"""LLMマネージャー

複数のLLMプロバイダーを統一的に管理するマネージャークラス。
"""

import os
from typing import Dict, Any, Optional, List
import logging

from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair
from src.llm.providers.base_provider import LLMProvider
from src.llm.providers.openai_provider import OpenAIProvider
from src.llm.providers.gemini_provider import GeminiProvider
from src.llm.providers.anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)


class LLMManager:
    """LLMプロバイダーを管理するマネージャークラス"""

    def __init__(self, provider: str = "openai", config: Optional[Any] = None):
        """
        LLMマネージャーの初期化。

        Args:
            provider: 使用するプロバイダー名 ("openai", "gemini", "anthropic")
            config: LLM設定オブジェクト (省略時はデフォルト設定を使用)
        """
        self.provider_name = provider
        self.config = config
        self.provider = self._initialize_provider(provider)

    def _initialize_provider(self, provider_name: str) -> LLMProvider:
        """プロバイダーを初期化"""
        providers = {
            "openai": self._init_openai,
            "gemini": self._init_gemini,
            "anthropic": self._init_anthropic,
        }

        if provider_name not in providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        return providers[provider_name]()

    def _init_openai(self) -> OpenAIProvider:
        """OpenAIプロバイダーを初期化"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY環境変数が設定されていません。\n"
                "設定方法: export OPENAI_API_KEY='your-api-key' または .envファイルに記載"
            )
        
        # APIキーのログ出力は削除（セキュリティ対策）
        logger.info("Using OpenAI API")

        # パフォーマンスモードをチェック
        from src.config import get_llm_config
        llm_config = get_llm_config()
        
        if llm_config.performance_mode:
            model = llm_config.performance_openai_model
            logger.info(f"Performance mode enabled - using {model}")
        else:
            model = llm_config.openai_model
            
        return OpenAIProvider(api_key=api_key, model=model)

    def _init_gemini(self) -> GeminiProvider:
        """Geminiプロバイダーを初期化"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY環境変数が設定されていません。\n"
                "設定方法: export GEMINI_API_KEY='your-api-key' または .envファイルに記載"
            )

        # パフォーマンスモードをチェック
        from src.config import get_llm_config
        llm_config = get_llm_config()
        
        if llm_config.performance_mode:
            model = llm_config.performance_gemini_model
            logger.info(f"Performance mode enabled - using {model}")
        else:
            model = llm_config.gemini_model
            
        return GeminiProvider(api_key=api_key, model=model)

    def _init_anthropic(self) -> AnthropicProvider:
        """Anthropicプロバイダーを初期化"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY環境変数が設定されていません。\n"
                "設定方法: export ANTHROPIC_API_KEY='your-api-key' または .envファイルに記載"
            )

        # パフォーマンスモードをチェック
        from src.config import get_llm_config
        llm_config = get_llm_config()
        
        if llm_config.performance_mode:
            model = llm_config.performance_anthropic_model
            logger.info(f"Performance mode enabled - using {model}")
        else:
            model = llm_config.anthropic_model
            
        return AnthropicProvider(api_key=api_key, model=model)

    def generate(self, prompt: str) -> str:
        """
        汎用的なテキスト生成を行う。

        Args:
            prompt: プロンプト文字列

        Returns:
            生成されたテキスト
        """
        try:
            logger.info(f"Generating text using {self.provider_name}")

            # プロバイダーの汎用生成メソッドを呼び出す
            if hasattr(self.provider, "generate"):
                return self.provider.generate(prompt)
            else:
                # generateメソッドがない場合は、generate_commentを使う
                # ダミーのweather_dataとpast_commentsを作成
                from src.data.weather_data import WeatherForecast, WeatherCondition
                from datetime import datetime

                dummy_weather = WeatherForecast(
                    datetime=datetime.now(),
                    weather_condition=WeatherCondition.CLEAR,
                    weather_code=100,
                    weather_description="晴れ",
                    temperature=20.0,
                    feels_like=20.0,
                    humidity=50.0,
                    pressure=1013.0,
                    wind_speed=0.0,
                    wind_direction=0,
                    precipitation=0.0,
                    cloud_cover=0,
                    visibility=10.0,
                    confidence=1.0,
                )

                # プロンプトをそのまま使用
                constraints = {"custom_prompt": prompt}

                return self.provider.generate_comment(
                    weather_data=dummy_weather, past_comments=None, constraints=constraints
                )

        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    def generate_comment(
        self, weather_data: WeatherForecast, past_comments: CommentPair, constraints: Dict[str, Any]
    ) -> str:
        """
        天気コメントを生成する。

        Args:
            weather_data: 天気予報データ
            past_comments: 過去のコメントペア
            constraints: 制約条件

        Returns:
            生成されたコメント
        """
        try:
            logger.info(f"Generating comment using {self.provider_name}")

            # プロバイダーを使用してコメント生成
            comment = self.provider.generate_comment(
                weather_data=weather_data, past_comments=past_comments, constraints=constraints
            )

            # コメント長の検証と調整
            max_length = constraints.get("max_length", 15)
            if len(comment) > max_length:
                logger.warning(
                    f"Generated comment exceeds max length ({len(comment)} > {max_length}): {comment}"
                )
                # 自然な位置で切り詰める
                comment = self._truncate_naturally(comment, max_length)
                logger.info(f"Truncated comment to: {comment}")

            return comment

        except Exception as e:
            logger.error(f"Error generating comment: {str(e)}")
            raise

    def switch_provider(self, provider_name: str):
        """プロバイダーを切り替える"""
        logger.info(f"Switching provider from {self.provider_name} to {provider_name}")
        self.provider_name = provider_name
        self.provider = self._initialize_provider(provider_name)

    def _truncate_naturally(self, text: str, max_length: int) -> str:
        """コメントを自然な位置で切り詰める"""
        if len(text) <= max_length:
            return text

        # 句読点や助詞の位置を探す
        natural_breaks = ["。", "、", "です", "ます", "ね", "よ", "を", "に", "で", "は", "が"]

        # max_length以内で最も後ろにある自然な区切り位置を探す
        best_pos = max_length
        for i in range(max_length, 0, -1):
            for break_str in natural_breaks:
                # 区切り文字列の開始位置を確認
                if i + len(break_str) <= len(text):
                    if text[i : i + len(break_str)] == break_str:
                        # 区切り文字列の後で切る
                        best_pos = i + len(break_str)
                        return text[:best_pos]

        # 自然な区切りが見つからない場合は単純に切り詰め
        return text[:max_length]


# エクスポート
__all__ = ["LLMManager"]

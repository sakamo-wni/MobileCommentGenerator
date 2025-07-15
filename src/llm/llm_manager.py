"""LLMマネージャー

複数のLLMプロバイダーを統一的に管理するマネージャークラス。
"""

import os
from typing import Any
import logging

from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair
from src.llm.providers.base_provider import LLMProvider
from src.llm.providers.openai_provider import OpenAIProvider
from src.llm.providers.gemini_provider import GeminiProvider
from src.llm.providers.anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)

# Python 3.13 type alias
type ProviderClass = type[LLMProvider]
type ModelAttrs = tuple[str, str]  # (normal_model_attr, performance_model_attr)


class LLMManager:
    """LLMプロバイダーを管理するマネージャークラス"""
    
    # プロバイダー設定の定義
    PROVIDER_CONFIGS: dict[str, dict[str, Any]] = {
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "model_attrs": ("openai_model", "performance_openai_model"),
            "provider_class": OpenAIProvider,
            "display_name": "OpenAI API"
        },
        "gemini": {
            "api_key_env": "GEMINI_API_KEY",
            "model_attrs": ("gemini_model", "performance_gemini_model"),
            "provider_class": GeminiProvider,
            "display_name": "Gemini API"
        },
        "anthropic": {
            "api_key_env": "ANTHROPIC_API_KEY",
            "model_attrs": ("anthropic_model", "performance_anthropic_model"),
            "provider_class": AnthropicProvider,
            "display_name": "Anthropic API"
        },
    }

    def __init__(self, provider: str = "openai", config: Any | None = None):
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
        """プロバイダーを初期化（統一された実装）"""
        if provider_name not in self.PROVIDER_CONFIGS:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        config = self.PROVIDER_CONFIGS[provider_name]
        
        # APIキーの取得
        api_key = self._get_api_key(config["api_key_env"])
        
        # モデルの選択
        model = self._get_model_name(config["model_attrs"])
        
        logger.info(f"Using {config['display_name']}")
        
        # プロバイダーインスタンスの作成
        provider_class: ProviderClass = config["provider_class"]
        return provider_class(api_key=api_key, model=model)
    
    def _get_api_key(self, env_name: str) -> str:
        """環境変数からAPIキーを取得"""
        api_key = os.getenv(env_name)
        if not api_key:
            raise ValueError(
                f"{env_name}環境変数が設定されていません。\n"
                f"設定方法: export {env_name}='your-api-key' または .envファイルに記載"
            )
        return api_key
    
    def _get_model_name(self, model_attrs: ModelAttrs) -> str:
        """設定からモデル名を取得"""
        from src.config.config import get_llm_config
        llm_config = get_llm_config()
        
        normal_attr, perf_attr = model_attrs
        
        if llm_config.performance_mode:
            model = getattr(llm_config, perf_attr)
            logger.info(f"Performance mode enabled - using {model}")
        else:
            model = getattr(llm_config, normal_attr)
        
        return model

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
        self, weather_data: WeatherForecast, past_comments: CommentPair, constraints: dict[str, Any]
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

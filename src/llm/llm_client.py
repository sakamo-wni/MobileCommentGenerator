"""
LLMクライアント - マルチプロバイダー対応のLLMクライアント

このモジュールは、OpenAI、Gemini、Anthropic Claude APIに対応した
統一インターフェースでのLLMクライアントを提供します。
"""

import os
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json

from src.utils.exceptions import (
    ConfigurationError,
    LLMAPIError,
    ValidationError,
)

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM設定データクラス"""

    model: str
    temperature: float = 0.7
    max_tokens: int = 50
    timeout: int = 30
    api_key: Optional[str] = None
    additional_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


class LLMClient(ABC):
    """LLMクライアントの抽象基底クラス"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key or self._get_api_key()

    @abstractmethod
    def _get_api_key(self) -> str:
        """APIキーを環境変数から取得"""
        pass

    @abstractmethod
    def generate_comment(self, prompt: str) -> str:
        """コメントを生成"""
        pass

    @abstractmethod
    def _make_api_request(self, prompt: str) -> Dict[str, Any]:
        """API リクエストの実行"""
        pass

    def _validate_response(self, response_text: str) -> str:
        """レスポンスの検証・整形"""
        if not response_text:
            raise ValidationError("空のレスポンスが返されました")

        # 15文字制限チェック
        if len(response_text) > 15:
            logger.warning(f"生成コメントが15文字を超過: {len(response_text)}文字")
            # 最初の15文字を取得
            response_text = response_text[:15]

        # 改行文字除去
        response_text = response_text.replace("\n", "").replace("\r", "")

        return response_text.strip()


class OpenAIClient(LLMClient):
    """OpenAI GPT クライアント"""

    def _get_api_key(self) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ConfigurationError("OPENAI_API_KEY環境変数が設定されていません")
        return api_key

    def generate_comment(self, prompt: str) -> str:
        """OpenAI APIでコメント生成"""
        try:
            response = self._make_api_request(prompt)
            generated_text = response["choices"][0]["message"]["content"]
            return self._validate_response(generated_text)
        except LLMAPIError:
            raise
        except Exception as e:
            logger.error(f"OpenAI API エラー: {str(e)}")
            raise LLMAPIError(f"OpenAI API エラー: {str(e)}")

    def _make_api_request(self, prompt: str) -> Dict[str, Any]:
        """OpenAI API リクエスト"""
        import openai

        openai.api_key = self.api_key

        try:
            response = openai.ChatCompletion.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )
            return response
        except Exception as e:
            logger.error(f"OpenAI API リクエストエラー: {str(e)}")
            raise LLMAPIError(f"OpenAI API リクエストエラー: {str(e)}")


class GeminiClient(LLMClient):
    """Google Gemini クライアント"""

    def _get_api_key(self) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ConfigurationError("GEMINI_API_KEY環境変数が設定されていません")
        return api_key

    def generate_comment(self, prompt: str) -> str:
        """Gemini APIでコメント生成"""
        try:
            response = self._make_api_request(prompt)
            generated_text = response["candidates"][0]["content"]["parts"][0]["text"]
            return self._validate_response(generated_text)
        except LLMAPIError:
            raise
        except Exception as e:
            logger.error(f"Gemini API エラー: {str(e)}")
            raise LLMAPIError(f"Gemini API エラー: {str(e)}")

    def _make_api_request(self, prompt: str) -> Dict[str, Any]:
        """Gemini API リクエスト"""
        import requests

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
        }

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
            },
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=data,
                params={"key": self.api_key},
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Gemini API リクエストエラー: {str(e)}")
            raise LLMAPIError(f"Gemini API リクエストエラー: {str(e)}")


class AnthropicClient(LLMClient):
    """Anthropic Claude クライアント"""

    def _get_api_key(self) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ConfigurationError("ANTHROPIC_API_KEY環境変数が設定されていません")
        return api_key

    def generate_comment(self, prompt: str) -> str:
        """Anthropic APIでコメント生成"""
        try:
            response = self._make_api_request(prompt)
            generated_text = response["content"][0]["text"]
            return self._validate_response(generated_text)
        except LLMAPIError:
            raise
        except Exception as e:
            logger.error(f"Anthropic API エラー: {str(e)}")
            raise LLMAPIError(f"Anthropic API エラー: {str(e)}")

    def _make_api_request(self, prompt: str) -> Dict[str, Any]:
        """Anthropic API リクエスト"""
        import requests

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        data = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Anthropic API リクエストエラー: {str(e)}")
            raise LLMAPIError(f"Anthropic API リクエストエラー: {str(e)}")


class LLMClientFactory:
    """LLMクライアントファクトリー"""

    # デフォルト設定
    DEFAULT_CONFIGS = {
        "openai": LLMConfig(model="gpt-4", temperature=0.7, max_tokens=50),
        "gemini": LLMConfig(model="gemini-pro", temperature=0.7, max_tokens=50),
        "anthropic": LLMConfig(model="claude-3-sonnet-20240229", temperature=0.7, max_tokens=50),
    }

    @classmethod
    def create_client(cls, provider: str, config: Optional[LLMConfig] = None) -> LLMClient:
        """
        指定プロバイダーのLLMクライアントを作成

        Args:
            provider: プロバイダー名 ('openai', 'gemini', 'anthropic')
            config: LLM設定（指定しない場合はデフォルト使用）

        Returns:
            LLMClient: 指定プロバイダーのクライアント

        Raises:
            ValueError: 不正なプロバイダー名の場合
        """
        if config is None:
            config = cls.DEFAULT_CONFIGS.get(provider)
            if config is None:
                raise ConfigurationError(f"未対応のプロバイダー: {provider}")

        if provider == "openai":
            return OpenAIClient(config)
        elif provider == "gemini":
            return GeminiClient(config)
        elif provider == "anthropic":
            return AnthropicClient(config)
        else:
            raise ConfigurationError(f"未対応のプロバイダー: {provider}")

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """利用可能なプロバイダー一覧を取得"""
        return list(cls.DEFAULT_CONFIGS.keys())

    @classmethod
    def validate_api_keys(cls) -> Dict[str, bool]:
        """各プロバイダーのAPIキー設定状況を確認"""
        results = {}
        for provider in cls.get_available_providers():
            try:
                client = cls.create_client(provider)
                results[provider] = bool(client.api_key)
            except (ValueError, ConfigurationError):
                results[provider] = False
        return results


def create_test_client(provider: str = "openai") -> LLMClient:
    """テスト用クライアント作成"""
    return LLMClientFactory.create_client(provider)


# レート制限対応の装飾子
def rate_limit(calls_per_minute: int = 60):
    """レート制限装飾子"""

    def decorator(func):
        last_called = [0.0]

        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            min_interval = 60.0 / calls_per_minute

            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                time.sleep(sleep_time)

            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result

        return wrapper

    return decorator

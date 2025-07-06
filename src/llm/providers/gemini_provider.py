"""Google Gemini APIプロバイダー"""

import logging
from typing import Dict, Any
import time

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
        import time
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # プロンプトの構築
                prompt = self._build_prompt(weather_data, past_comments, constraints)

                # システムプロンプトを含めた完全なプロンプト（簡潔に）
                full_prompt = f"天気予報の短いコメントを生成。最大15文字。\n{prompt}"

                logger.info(f"Gemini API呼び出し開始 (試行 {attempt + 1}/{max_retries})")
                
                # タイマー開始
                start_time = time.time()
                
                # APIリクエスト（さらに簡潔な設定）
                # タイムアウトを30秒に設定
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self.model.generate_content,
                        full_prompt,
                        generation_config=genai.GenerationConfig(
                            temperature=0.5,  # より確定的な出力
                            max_output_tokens=50,  # 少し増やす
                            candidate_count=1,
                            top_p=0.8,  # 確率分布を制限
                            top_k=10,  # 候補トークンを制限
                        ),
                        safety_settings={
                            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                        }
                    )
                    try:
                        response = future.result(timeout=30)  # 30秒のタイムアウト
                    except concurrent.futures.TimeoutError:
                        logger.error(f"Gemini API timeout after 30 seconds (attempt {attempt + 1})")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (attempt + 1))
                            continue
                        else:
                            raise Exception("Gemini API timeout after all retries")
                
                # レスポンス時間を記録
                response_time = time.time() - start_time
                logger.info(f"Gemini APIレスポンス時間: {response_time:.2f}秒")

                # レスポンスの検証
                if not response.parts:
                    logger.warning(f"Response has no parts. Candidates: {response.candidates}")
                    if response.candidates and len(response.candidates) > 0:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'finish_reason'):
                            logger.error(f"Finish reason: {candidate.finish_reason}")
                            if candidate.finish_reason == 2:  # MAX_TOKENS
                                logger.error("Output truncated due to max tokens limit")
                                # より短い出力を求めて再試行
                                if attempt < max_retries - 1:
                                    logger.info("Retrying with shorter output request...")
                                    time.sleep(retry_delay)
                                    continue
                            elif candidate.finish_reason == 3:  # SAFETY
                                logger.error("Content blocked by safety filters")
                                if attempt < max_retries - 1:
                                    logger.info("Retrying with safer prompt...")
                                    time.sleep(retry_delay)
                                    continue
                    return "本日の天気情報です"
                
                # レスポンスからコメントを抽出
                generated_comment = response.text.strip()
                # 改行や余分な記号を除去
                generated_comment = generated_comment.replace("\n", "").strip('"')

                logger.info(f"Generated comment: {generated_comment}")
                return generated_comment

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Gemini API error (attempt {attempt + 1}): {error_msg}")
                
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"タイムアウトエラー。{wait_time}秒後にリトライします...")
                        time.sleep(wait_time)
                        continue
                
                if attempt == max_retries - 1:
                    # 最後の試行でも失敗した場合は、フォールバックコメントを返す
                    logger.error("Gemini API呼び出しが全て失敗しました。フォールバックコメントを使用します。")
                    return "本日の天気情報です"
                    
        return "本日の天気情報です"

    def generate(self, prompt: str) -> str:
        """
        汎用的なテキスト生成を行う。

        Args:
            prompt: プロンプト文字列

        Returns:
            生成されたテキスト
        """
        import time
        max_retries = 3
        retry_delay = 2
        
        # プロンプトを短くして、簡潔な指示に変更
        simplified_prompt = f"簡潔に回答してください（100文字以内）:\n{prompt[:500]}"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Generating text with Gemini (attempt {attempt + 1}/{max_retries})")
                
                # タイマー開始
                start_time = time.time()

                # タイムアウトを30秒に設定
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self.model.generate_content,
                        simplified_prompt,
                        generation_config=genai.GenerationConfig(
                            temperature=0.5,
                            max_output_tokens=300,  # 少し増やす
                            candidate_count=1,
                            top_p=0.8,
                            top_k=20,
                        ),
                        safety_settings={
                            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                        }
                    )
                    try:
                        response = future.result(timeout=30)  # 30秒のタイムアウト
                    except concurrent.futures.TimeoutError:
                        logger.error(f"Gemini API timeout after 30 seconds (attempt {attempt + 1})")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (attempt + 1))
                            continue
                        else:
                            raise Exception("Gemini API timeout after all retries")
                
                # レスポンス時間を記録
                response_time = time.time() - start_time
                logger.info(f"Gemini APIレスポンス時間: {response_time:.2f}秒")

                # レスポンスの検証
                if not response.parts:
                    logger.warning(f"Response has no parts. Candidates: {response.candidates}")
                    if response.candidates and len(response.candidates) > 0:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'finish_reason'):
                            logger.error(f"Finish reason: {candidate.finish_reason}")
                            if candidate.finish_reason == 2:  # MAX_TOKENS
                                logger.error("Output truncated due to max tokens limit")
                                if attempt < max_retries - 1:
                                    logger.info("Retrying with shorter output request...")
                                    time.sleep(retry_delay)
                                    continue
                            elif candidate.finish_reason == 3:  # SAFETY
                                logger.error("Content blocked by safety filters")
                                if attempt < max_retries - 1:
                                    logger.info("Retrying with safer prompt...")
                                    time.sleep(retry_delay)
                                    continue
                    raise Exception("Response generation failed")
                
                generated_text = response.text
                logger.info(f"Generated text: {generated_text[:100]}...")

                return generated_text

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Gemini API error (attempt {attempt + 1}): {error_msg}")
                
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"タイムアウトエラー。{wait_time}秒後にリトライします...")
                        time.sleep(wait_time)
                        continue
                
                if attempt == max_retries - 1:
                    logger.error("Gemini API呼び出しが全て失敗しました")
                    raise
                    
        raise Exception("Gemini API呼び出しが全て失敗しました")


# エクスポート
__all__ = ["GeminiProvider"]

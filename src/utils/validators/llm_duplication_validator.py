"""LLMを使用した動的な重複検証バリデータ"""

import logging
from typing import Tuple
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from .base_validator import BaseValidator

logger = logging.getLogger(__name__)


class LLMDuplicationValidator(BaseValidator):
    """LLMを使用して動的に重複や矛盾を検証"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.0,  # 一貫性のある判定のため温度を0に
            max_retries=2,
        )
        
        self.system_prompt = """あなたは天気予報コメントの重複・矛盾を検証する専門家です。
2つのコメントを分析し、以下の観点で問題がないか判定してください：

1. 意味的な重複：同じ内容を異なる表現で繰り返していないか
2. 論理的な矛盾：相反する内容が含まれていないか
3. 情報の冗長性：片方のコメントがもう片方を完全に包含していないか

判定基準：
- 「夏バテに注意」と「夏バテ対策を」のような同じ概念の繰り返しは重複
- 「雨が降りやすく」と「急な雨に注意」のような同じ警告の繰り返しは重複
- 「朝昼の気温差大」と「朝晩と昼間の気温差に注意」のような同じ情報の繰り返しは重複
- 「過ごしやすい」と「蒸し暑い」のような相反する表現は矛盾
- 「晴れ間が広がる」と「紫外線対策を」のような補完的な関係はOK

応答形式：
必ず以下のJSON形式で応答してください：
{
  "is_valid": true/false,
  "reason": "判定理由（30文字以内）",
  "type": "duplicate" or "contradiction" or "ok"
}"""
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """単一コメントの検証（LLMDuplicationValidatorでは実装しない）"""
        return True, "単一コメントのチェックは他のバリデータで実施"
    
    async def validate_comment_pair_with_llm(
        self,
        weather_comment: str,
        advice_comment: str,
        weather_data: WeatherForecast
    ) -> Tuple[bool, str]:
        """LLMを使用してコメントペアの一貫性を検証"""
        try:
            user_message = f"""以下の2つのコメントを検証してください：

天気コメント: {weather_comment}
アドバイスコメント: {advice_comment}

参考情報：
- 気温: {weather_data.temperature}°C
- 天気: {weather_data.weather_description}
- 降水量: {weather_data.precipitation}mm"""

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # レスポンスをパース
            try:
                import json
                # JSONブロックを抽出
                content = response.content.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(content)
                
                is_valid = result.get("is_valid", True)
                reason = result.get("reason", "LLM判定エラー")
                
                if not is_valid:
                    logger.info(f"LLM重複検出: {reason} - 天気:'{weather_comment}', アドバイス:'{advice_comment}'")
                
                return is_valid, reason
                
            except Exception as e:
                logger.error(f"LLMレスポンスのパースエラー: {e}, レスポンス: {response.content}")
                # パースエラーの場合は通過させる（安全側に倒す）
                return True, "LLM判定エラー"
            
        except Exception as e:
            logger.error(f"LLM検証エラー: {e}")
            # エラーの場合は通過させる（安全側に倒す）
            return True, "LLM検証エラー"
    
    def validate_comment_pair_with_llm_sync(
        self,
        weather_comment: str,
        advice_comment: str,
        weather_data: WeatherForecast
    ) -> Tuple[bool, str]:
        """同期版のLLM検証（既存コードとの互換性のため）"""
        try:
            return asyncio.run(self.validate_comment_pair_with_llm(
                weather_comment, advice_comment, weather_data
            ))
        except Exception as e:
            logger.error(f"LLM検証の同期実行エラー: {e}")
            return True, "LLM検証エラー"
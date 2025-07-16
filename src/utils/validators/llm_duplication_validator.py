"""LLMを使用した動的な重複検証バリデータ"""

import logging
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from src.data.comment_generation_state import CommentGenerationState
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
4. 天気パターンとの整合性：実際の天気予報と矛盾していないか

判定基準：
- 「夏バテに注意」と「夏バテ対策を」のような同じ概念の繰り返しは重複
- 「雨が降りやすく」と「急な雨に注意」のような同じ警告の繰り返しは重複
- 「朝昼の気温差大」と「朝晩と昼間の気温差に注意」のような同じ情報の繰り返しは重複
- 「過ごしやすい」と「蒸し暑い」のような相反する表現は矛盾
- 「晴れ間が広がる」と「紫外線対策を」のような補完的な関係はOK

天気パターンとの矛盾チェック：
- 4時間すべて雨の場合、「にわか雨」「一時的な雨」は不適切（継続的な雨なのに一時的と表現）
- 4時間すべて雨の場合、「傘があると安心」「傘がお守り」は不適切（確実に雨なので「傘が必須」が適切）
- 晴れ続きの場合、「雨が心配」「傘の準備」は不適切（降水予報なし）
- 気温が一定の場合、「気温差が大きい」は不適切
- 天気が安定している場合、「変わりやすい天気」は不適切

応答形式：
必ず以下のJSON形式で応答してください：
{
  "is_valid": true/false,
  "reason": "判定理由（30文字以内）",
  "type": "duplicate" or "contradiction" or "weather_mismatch" or "ok"
}"""
    
    def validate(self, comment: PastComment, weather_data: WeatherForecast) -> tuple[bool, str]:
        """単一コメントの検証（LLMDuplicationValidatorでは実装しない）"""
        return True, "単一コメントのチェックは他のバリデータで実施"
    
    def validate_comment_pair_with_llm_sync(
        self,
        weather_comment: str,
        advice_comment: str,
        weather_data: WeatherForecast,
        state: CommentGenerationState | None = None
    ) -> tuple[bool, str]:
        """LLMを使用してコメントペアの一貫性を検証
        
        注意: エラー時はTrueを返してコメントを通過させる。
        これはシステムの可用性を優先し、LLMエラーによる
        サービス停止を避けるため。
        """
        try:
            # 4時点の予報データを準備
            period_info = self._format_period_forecasts(state)
            
            user_message = f"""以下の2つのコメントを検証してください：

天気コメント: {weather_comment}
アドバイスコメント: {advice_comment}

参考情報：
- 気温: {weather_data.temperature}°C
- 天気: {weather_data.weather_description}
- 降水量: {weather_data.precipitation}mm

{period_info}"""

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            
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
                # パースエラーの場合は通過させる
                # （システム可用性優先：重複コンテンツよりサービス継続を重視）
                return True, "LLM判定エラー"
            
        except Exception as e:
            logger.error(f"LLM検証エラー: {e}")
            # エラーの場合は通過させる
            # （システム可用性優先：重複コンテンツよりサービス継続を重視）
            return True, "LLM検証エラー"
    
    def _format_period_forecasts(self, state: CommentGenerationState | None) -> str:
        """4時点の予報データをフォーマット"""
        if not state or not hasattr(state, 'generation_metadata'):
            return ""
        
        period_forecasts = state.generation_metadata.get('period_forecasts', [])
        if not period_forecasts:
            return ""
        
        formatted_periods = ["翌日の時間帯別予報:"]
        
        # 天気パターンの分析
        weather_patterns = []
        rain_count = 0
        total_hours = len(period_forecasts)
        
        for forecast in period_forecasts:
            if hasattr(forecast, 'datetime') and hasattr(forecast, 'weather_description'):
                time_str = forecast.datetime.strftime('%H:%M')
                temp = getattr(forecast, 'temperature', 0)
                precip = getattr(forecast, 'precipitation', 0)
                desc = getattr(forecast, 'weather_description', '')
                
                formatted_periods.append(f"- {time_str}: {desc}, {temp}°C, 降水量{precip}mm")
                
                # 雨判定
                if precip > 0 or '雨' in desc:
                    rain_count += 1
                    weather_patterns.append('雨')
                elif '晴' in desc:
                    weather_patterns.append('晴れ')
                elif '曇' in desc:
                    weather_patterns.append('曇り')
                else:
                    weather_patterns.append('その他')
        
        # パターン分析結果を追加
        formatted_periods.append("\n天気パターン分析:")
        
        if rain_count == total_hours:
            formatted_periods.append("- 全時間帯で雨（継続的な雨）")
        elif rain_count >= total_hours * 0.5:
            formatted_periods.append(f"- {rain_count}/{total_hours}時間で雨（断続的な雨）")
        elif rain_count > 0:
            formatted_periods.append(f"- {rain_count}/{total_hours}時間で雨（一時的な雨）")
        else:
            formatted_periods.append("- 降水なし")
        
        # 天気の変化パターン
        if len(set(weather_patterns)) == 1:
            formatted_periods.append(f"- 天気は終日{weather_patterns[0]}で安定")
        else:
            formatted_periods.append(f"- 天気が変化: {' → '.join(weather_patterns)}")
        
        return "\n".join(formatted_periods)
    

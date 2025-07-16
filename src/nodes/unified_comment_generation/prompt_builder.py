"""
Prompt builder for unified comment generation

統合コメント生成用のプロンプト構築
"""

from __future__ import annotations

from datetime import datetime
from src.data.past_comment import PastComment


def build_unified_prompt(weather_comments: list[PastComment],
                        advice_comments: list[PastComment],
                        weather_info: str,
                        location_name: str,
                        target_datetime: datetime) -> str:
    """統合プロンプトの構築
    
    Args:
        weather_comments: 天気コメントリスト
        advice_comments: アドバイスコメントリスト
        weather_info: フォーマット済み天気情報
        location_name: 地点名
        target_datetime: 対象日時
        
    Returns:
        統合プロンプト文字列
    """
    # 表示する候補数を制限（上位30件）
    MAX_CANDIDATES = 30
    weather_comments_display = weather_comments[:MAX_CANDIDATES]
    advice_comments_display = advice_comments[:MAX_CANDIDATES]
    
    prompt = f"""以下の過去のコメントと現在の天気情報を基に、最適な天気コメントとアドバイスのペアを選択し、それらを元により魅力的で完成度の高い最終的なコメントを生成してください。

### 現在の状況:
地点: {location_name}
日時: {target_datetime.strftime('%Y年%m月%d日 %H時')}

### 現在の天気情報:
{weather_info}

### 天気コメント候補:
"""
    
    for i, comment in enumerate(weather_comments_display, 1):
        prompt += f"{i}. {comment.comment_text}\n"
    
    prompt += "\n### アドバイスコメント候補:\n"
    
    for i, comment in enumerate(advice_comments_display, 1):
        prompt += f"{i}. {comment.comment_text}\n"
    
    prompt += """
### 生成ルール:
1. 天気コメントとアドバイスコメントで内容が重複しないよう注意してください
2. 気温差情報が大きい場合は、体調管理に関するアドバイスを優先してください
3. 降水がある場合は、傘に関する言及を含めてください
4. 時刻に応じた適切な表現を使用してください（朝・昼・夕方・夜）
5. 地点名に応じた地域性を考慮してください

### 回答形式（必ずJSON形式で出力）:
{
    "selected_weather_index": 選択した天気コメントの番号,
    "selected_advice_index": 選択したアドバイスコメントの番号,
    "weather_comment": "生成した天気コメント（元のコメントを改良）",
    "advice_comment": "生成したアドバイスコメント（元のコメントを改良）",
    "selection_reason": "このペアを選んだ理由"
}
"""
    
    return prompt
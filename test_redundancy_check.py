#!/usr/bin/env python3
"""重複コメント選択のテスト"""

import logging
from src.workflows.unified_comment_generation_workflow import create_unified_comment_generation_workflow
from src.config.config import get_config

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_rain_comment_selection():
    """雨の時のコメント選択をテスト"""
    workflow = create_unified_comment_generation_workflow()
    
    locations = ["東京", "大阪", "名古屋", "札幌", "福岡"]
    
    print("=== 雨関連コメントの重複チェック ===\n")
    
    for location in locations:
        print(f"\n{location}のテスト:")
        print("-" * 40)
        
        try:
            from src.data.comment_generation_state import CommentGenerationState
            initial_state = CommentGenerationState(
                location_name=location,
                llm_provider="gemini"
            )
            result = workflow.invoke(initial_state)
            result = result.__dict__ if hasattr(result, '__dict__') else result
            
            if result.get("generated_comment"):
                comment = result["generated_comment"]
                print(f"生成されたコメント: {comment}")
                
                # 傘関連の表現をチェック
                umbrella_phrases = ["傘が必須", "傘があると安心", "傘は必須", "傘の用意", "傘を忘れずに"]
                found_phrases = [phrase for phrase in umbrella_phrases if phrase in comment]
                
                if len(found_phrases) > 1:
                    print(f"⚠️  重複検出: {found_phrases}")
                elif found_phrases:
                    print(f"✅ 傘表現: {found_phrases[0]}")
                else:
                    print("ℹ️  傘関連の表現なし")
                    
                # メタデータから選択されたコメントを確認
                metadata = result.get("generation_metadata", {})
                if metadata:
                    weather_comment = metadata.get("selected_weather_comment", "")
                    advice_comment = metadata.get("selected_advice_comment", "")
                    print(f"  天気: {weather_comment}")
                    print(f"  アドバイス: {advice_comment}")
                    
        except Exception as e:
            print(f"エラー: {e}")

if __name__ == "__main__":
    test_rain_comment_selection()
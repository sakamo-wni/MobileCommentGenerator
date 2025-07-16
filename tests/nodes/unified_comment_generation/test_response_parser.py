#!/usr/bin/env python3
"""response_parser.pyのテスト"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nodes.unified_comment_generation.response_parser import parse_unified_response

# テストケース
test_cases = [
    # ケース1: 標準的な```json形式
    {
        "name": "標準的な```json形式",
        "response": '''```json
{
    "selected_weather_index": 1,
    "selected_advice_index": 2,
    "weather_comment": "今日は晴れです",
    "advice_comment": "傘は不要です"
}
```''',
        "expected": True
    },
    # ケース2: 改行が多い```json形式
    {
        "name": "改行が多い```json形式",
        "response": '''```json

{
    "selected_weather_index": 1,
    "selected_advice_index": 2,
    "weather_comment": "今日は晴れです",
    "advice_comment": "傘は不要です"
}

```''',
        "expected": True
    },
    # ケース3: 大文字のJSON
    {
        "name": "大文字のJSON",
        "response": '''```JSON
{
    "selected_weather_index": 1,
    "selected_advice_index": 2,
    "weather_comment": "今日は晴れです",
    "advice_comment": "傘は不要です"
}
```''',
        "expected": True
    },
    # ケース4: プレーンなJSON
    {
        "name": "プレーンなJSON",
        "response": '''{
    "selected_weather_index": 1,
    "selected_advice_index": 2,
    "weather_comment": "今日は晴れです",
    "advice_comment": "傘は不要です"
}''',
        "expected": True
    },
    # ケース5: テキストに埋め込まれたJSON
    {
        "name": "テキストに埋め込まれたJSON",
        "response": '''以下が結果です:

{
    "selected_weather_index": 1,
    "selected_advice_index": 2,
    "weather_comment": "今日は晴れです",
    "advice_comment": "傘は不要です"
}

以上です。''',
        "expected": True
    },
    # ケース6: json:形式
    {
        "name": "json:形式",
        "response": '''json:
{
    "selected_weather_index": 1,
    "selected_advice_index": 2,
    "weather_comment": "今日は晴れです",
    "advice_comment": "傘は不要です"
}''',
        "expected": True
    },
    # ケース7: 切り詰められたJSON（文字列の途中で切れている）
    {
        "name": "切り詰められたJSON",
        "response": '''```json
{
    "selected_weather_index": 1,
    "selected_advice_index": 2,
    "weather_comment": "今日は晴れです",
    "advice_comment": "傘は不要で''',
        "expected": True  # 修正により成功するはず
    },
    # ケース8: ブレースが不完全なJSON
    {
        "name": "ブレースが不完全なJSON",
        "response": '''```json
{
    "selected_weather_index": 1,
    "selected_advice_index": 2,
    "weather_comment": "今日は晴れです"''',
        "expected": True  # 修正により成功するはず
    },
]

# テスト実行
for test in test_cases:
    print(f"\n=== {test['name']} ===")
    try:
        result = parse_unified_response(test['response'])
        print(f"✓ 成功: {result}")
    except Exception as e:
        if test['expected']:
            print(f"✗ 失敗: {e}")
        else:
            print(f"✓ 期待通りエラー: {e}")
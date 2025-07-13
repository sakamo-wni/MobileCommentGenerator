# UI/UX改善ガイド

このドキュメントでは、Phase 2で実装されたUI/UX改善機能の使用方法を説明します。

## 1. エラーメッセージング

### 改善前
```python
st.error(f"❌ エラー: {str(error)}")
```

### 改善後
```python
from src.ui.utils import show_error, ErrorType, handle_exception

# 特定のエラータイプで表示
show_error(
    error_type=ErrorType.API_KEY_MISSING,
    details="OpenAI APIキーが設定されていません",
    callback=lambda: st.rerun()  # 再試行ボタン
)

# 例外から自動的にエラータイプを判定
try:
    # 処理
except Exception as e:
    handle_exception(e, context="コメント生成", callback=retry_generation)
```

## 2. レスポンシブデザイン

### 基本的な使用方法
```python
from src.ui.utils import apply_responsive_styles, create_responsive_columns

# ページの先頭でスタイルを適用
apply_responsive_styles()

# レスポンシブカラムの作成
col1, col2, col3 = create_responsive_columns([2, 3, 1], gap="medium")
```

### カードUIの作成
```python
from src.ui.utils import create_card

create_card(
    title="本日の生成数",
    content="15件のコメントを生成しました",
    icon="📊",
    color="#e3f2fd"
)
```

## 3. ユーザーフィードバック

### 操作状態の表示
```python
from src.ui.utils import show_operation_status

# 処理中
show_operation_status(
    "コメント生成中",
    status="processing",
    message="3/5地点を処理中...",
    progress=0.6
)

# 成功
show_operation_status(
    "生成完了",
    status="success",
    message="すべての地点でコメントを生成しました",
    details={"生成数": 5, "所要時間": "12秒"}
)
```

### ステップ進行状況
```python
from src.ui.utils import show_step_progress

steps = [
    {"name": "天気データ取得", "status": "complete"},
    {"name": "過去コメント検索", "status": "complete"},
    {"name": "LLM生成", "status": "current"},
    {"name": "結果保存", "status": "pending"}
]

show_step_progress(steps, current_step=2)
```

### 通知の表示
```python
from src.ui.utils import show_notification

# 成功通知
show_notification(
    "コメントをクリップボードにコピーしました",
    type="success",
    duration=3
)

# エラー通知
show_notification(
    "ネットワークエラーが発生しました",
    type="error",
    duration=5
)
```

## 4. 実装例：改善されたエラーハンドリング

### result_display.pyの改善例
```python
# 改善前
if error:
    st.error(f"❌ **{location}**: {error}")

# 改善後
from src.ui.utils import show_error, ErrorType, get_error_type_from_exception

if error:
    error_obj = Exception(error) if isinstance(error, str) else error
    show_error(
        error_type=get_error_type_from_exception(error_obj),
        details=f"地点: {location}\nエラー: {str(error)}",
        callback=lambda: regenerate_for_location(location)
    )
```

## 5. オンボーディング

新規ユーザー向けのツアーを実装：

```python
from src.ui.utils import create_onboarding_tour

tour_steps = [
    {
        "title": "ようこそ！",
        "content": "天気コメント生成システムへようこそ。このツアーで基本的な使い方を説明します。"
    },
    {
        "title": "地点選択",
        "content": "まず、左のサイドバーから生成したい地点を選択してください。"
    },
    {
        "title": "LLMプロバイダー選択",
        "content": "次に、使用するLLMプロバイダーを選択します。APIキーの設定もお忘れなく。"
    }
]

create_onboarding_tour(tour_steps)
```

## 6. アクセシビリティの改善

- すべてのインタラクティブ要素に44px以上のタッチターゲットを確保
- フォーカス状態を明確に表示
- エラーメッセージに視覚的な強調（左ボーダー）を追加
- 読みやすさのため行間を1.6に設定

## 7. パフォーマンスの体感向上

- アニメーションによる視覚的フィードバック
- ローディング状態の明確な表示
- プログレスインジケーターによる進捗の可視化

これらの改善により、ユーザーエクスペリエンスが大幅に向上し、エラー時の対処法が明確になり、モバイルデバイスでも使いやすくなりました。
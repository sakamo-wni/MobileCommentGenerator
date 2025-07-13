# セキュリティ改善ガイド

このドキュメントでは、Phase 2で実装されたセキュリティ改善について説明します。

## 1. HTMLインジェクション対策

### 問題点
- `unsafe_allow_html=True`を使用している箇所で、ユーザー入力がそのまま表示される可能性
- JavaScriptコード内でエスケープされていない文字列の使用

### 解決策

#### security_utils.pyの追加
```python
from src.ui.utils.security_utils import sanitize_html, sanitize_id, generate_safe_id

# HTMLエスケープ
safe_text = sanitize_html(user_input)

# 安全なID生成
safe_id = generate_safe_id("notification")

# CSS値のサニタイズ
safe_color = sanitize_css_value(color_input)
```

#### 実装例
```python
# 改善前
st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)

# 改善後
st.markdown(f"<h3>{sanitize_html(title)}</h3>", unsafe_allow_html=True)
```

## 2. CSS競合の解決

### 問題点
- グローバルCSSセレクタが他のStreamlitコンポーネントに影響
- 毎回CSS定義を出力することによるパフォーマンス低下

### 解決策

#### より具体的なセレクタの使用
```css
/* 改善前 */
button:focus { outline: 2px solid #0066cc; }

/* 改善後 */
.stApp button:focus { outline: 2px solid #0066cc !important; }
```

#### CSS適用の最適化
```python
_CSS_APPLIED_KEY = "_responsive_css_applied"

def apply_responsive_styles():
    # 既に適用済みの場合はスキップ
    if st.session_state.get(_CSS_APPLIED_KEY, False):
        return
    
    st.session_state[_CSS_APPLIED_KEY] = True
    # CSSを適用...
```

## 3. Clipboard APIのフォールバック

### 問題点
- `navigator.clipboard`APIはHTTPS環境でのみ動作
- エラー時のフォールバック処理が不足

### 解決策
```javascript
// Clipboard APIが利用可能か確認
if (navigator.clipboard && window.isSecureContext) {
    // Clipboard APIを使用
} else {
    // フォールバック：選択可能なテキストエリアを表示
    showFallback();
}
```

## 4. 型ヒントの強化

### 改善例
```python
# 改善前
def show_notification(message: str, type: str = "info"):

# 改善後
from typing import Literal

def show_notification(
    message: str, 
    type: Literal["info", "success", "warning", "error"] = "info"
):
```

## 5. エラーメッセージのi18n対応準備

### 設定ファイルからの読み込み
```python
# 環境変数で設定ファイルパスを指定
ERROR_MESSAGES_CONFIG_PATH = os.environ.get("ERROR_MESSAGES_CONFIG_PATH")

# カスタムメッセージの読み込み
custom_messages = load_error_messages_from_config()
if custom_messages:
    ERROR_MESSAGES.update(custom_messages)
```

### 設定ファイル例（error_messages.json）
```json
{
    "api_key_missing": {
        "title": "API Key Not Set",
        "description": "The API key for the selected LLM provider is not configured.",
        "solution": "Please open Settings from the sidebar and enter your API key."
    }
}
```

## 6. 入力検証

### validate_input関数の使用
```python
from src.ui.utils.security_utils import validate_input

# 数値入力の検証
is_valid, error_msg = validate_input(
    value=user_input,
    input_type="number",
    min_value=0,
    max_value=100
)

if not is_valid:
    st.error(error_msg)
```

## セキュリティチェックリスト

- ✅ すべてのユーザー入力をサニタイズ
- ✅ JavaScriptコード内の文字列をエスケープ
- ✅ CSS値を適切にサニタイズ
- ✅ IDの自動生成に安全な関数を使用
- ✅ Clipboard APIのフォールバック処理
- ✅ 入力値の検証
- ✅ 型ヒントによる型安全性の向上

これらの改善により、XSS攻撃やインジェクション攻撃のリスクが大幅に軽減されました。
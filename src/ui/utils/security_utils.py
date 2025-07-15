"""
セキュリティ関連のユーティリティ

HTMLサニタイズ、入力検証など
"""

import re
import html
from typing import Any, import hashlib
import time


def sanitize_html(text: str) -> str:
    """
    HTMLエスケープを行い、安全な文字列を返す
    
    Args:
        text: サニタイズする文字列
        
    Returns:
        サニタイズされた文字列
    """
    if not isinstance(text, str):
        text = str(text)
    
    # HTMLエスケープ
    text = html.escape(text)
    
    # 追加のサニタイズ（JavaScriptイベントハンドラの除去）
    # on*= パターンを除去
    text = re.sub(r'\bon\w+\s*=', '', text, flags=re.IGNORECASE)
    
    # javascript: URLスキームを除去
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    # vbscript: URLスキームを除去
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)
    
    return text


def sanitize_id(id_string: str) -> str:
    """
    HTML IDとして安全な文字列を生成
    
    Args:
        id_string: ID文字列
        
    Returns:
        サニタイズされたID文字列
    """
    # 英数字、ハイフン、アンダースコアのみを許可
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', id_string)
    
    # 空の場合はタイムスタンプベースのIDを生成
    if not sanitized:
        sanitized = f"id_{int(time.time() * 1000)}"
    
    # 数字で始まる場合はプレフィックスを追加
    if sanitized[0].isdigit():
        sanitized = f"id_{sanitized}"
    
    return sanitized


def sanitize_css_value(value: str) -> str:
    """
    CSS値として安全な文字列を返す
    
    Args:
        value: CSS値
        
    Returns:
        サニタイズされたCSS値
    """
    # 基本的なサニタイズ
    value = str(value)
    
    # セミコロンやブレースを除去（CSSインジェクション対策）
    value = re.sub(r'[;{}]', '', value)
    
    # URLの場合の処理
    if 'url(' in value.lower():
        # javascript: などの危険なURLスキームを除去
        value = re.sub(r'(javascript|vbscript|data):', '', value, flags=re.IGNORECASE)
    
    # 式の評価を防ぐ
    value = re.sub(r'expression\s*\(', '', value, flags=re.IGNORECASE)
    
    return value


def generate_safe_id(prefix: str = "component") -> str:
    """
    ユニークで安全なIDを生成
    
    Args:
        prefix: IDのプレフィックス
        
    Returns:
        安全なID文字列
    """
    # プレフィックスをサニタイズ
    safe_prefix = sanitize_id(prefix)
    
    # タイムスタンプとランダムハッシュを組み合わせ
    timestamp = int(time.time() * 1000000)
    random_part = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
    
    return f"{safe_prefix}_{timestamp}_{random_part}"


def validate_input(
    value: Any,
    input_type: str,
    min_value: float | None = None,
    max_value: float | None = None,
    allowed_values: list[Any | None] = None,
    pattern: str | None = None
) -> tuple[bool, str | None]:
    """
    入力値の検証
    
    Args:
        value: 検証する値
        input_type: 入力タイプ（text, number, email, url など）
        min_value: 最小値（数値の場合）
        max_value: 最大値（数値の場合）
        allowed_values: 許可される値のリスト
        pattern: 正規表現パターン
        
    Returns:
        (is_valid, error_message) のタプル
    """
    if value is None:
        return False, "値が入力されていません"
    
    # 許可リストチェック
    if allowed_values is not None and value not in allowed_values:
        return False, f"許可されていない値です: {value}"
    
    # タイプ別検証
    if input_type == "number":
        try:
            num_value = float(value)
            if min_value is not None and num_value < min_value:
                return False, f"値が小さすぎます（最小値: {min_value}）"
            if max_value is not None and num_value > max_value:
                return False, f"値が大きすぎます（最大値: {max_value}）"
        except (ValueError, TypeError):
            return False, "数値を入力してください"
    
    elif input_type == "email":
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, str(value)):
            return False, "有効なメールアドレスを入力してください"
    
    elif input_type == "url":
        url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
        if not re.match(url_pattern, str(value)):
            return False, "有効なURLを入力してください"
    
    elif input_type == "text":
        # テキストの基本的なサニタイズチェック
        text_value = str(value)
        if len(text_value) > 10000:  # 最大文字数制限
            return False, "テキストが長すぎます（最大10000文字）"
    
    # カスタムパターンチェック
    if pattern is not None:
        if not re.match(pattern, str(value)):
            return False, "入力形式が正しくありません"
    
    return True, None


def escape_json_string(text: str) -> str:
    """
    JSON文字列として安全にエスケープ
    
    Args:
        text: エスケープする文字列
        
    Returns:
        エスケープされた文字列
    """
    # 基本的なエスケープ
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\r')
    text = text.replace('\t', '\\t')
    text = text.replace('\b', '\\b')
    text = text.replace('\f', '\\f')
    
    # 制御文字の除去
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text


def create_csp_meta_tag() -> str:
    """
    Content Security Policy (CSP) メタタグを生成
    
    Returns:
        CSPメタタグのHTML
    """
    csp_rules = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self' data:",
        "connect-src 'self' https://api.openai.com https://api.anthropic.com",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'"
    ]
    
    csp_content = "; ".join(csp_rules)
    
    return f'<meta http-equiv="Content-Security-Policy" content="{csp_content}">'
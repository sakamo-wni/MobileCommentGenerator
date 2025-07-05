"""
WxTech API エラー定義

WxTech API で発生するエラーの定義と処理を管理
"""

from typing import Optional


class WxTechAPIError(Exception):
    """WxTech API エラー
    
    Attributes:
        status_code: HTTPステータスコード（あれば）
        error_type: エラータイプ（api_key_invalid, rate_limit, network_error等）
    """
    
    def __init__(self, message: str, status_code: Optional[int] = None, error_type: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type


def handle_http_error(status_code: int) -> WxTechAPIError:
    """HTTPステータスコードに応じたエラーを生成
    
    Args:
        status_code: HTTPステータスコード
        
    Returns:
        適切なWxTechAPIError
    """
    error_mappings = {
        401: ("APIキーが無効です", 'api_key_invalid'),
        403: ("APIアクセスが拒否されました", 'http_error'),
        404: ("指定された地点データが見つかりません", 'http_error'),
        429: ("レート制限に達しました", 'rate_limit'),
        500: ("APIサーバーエラーが発生しました", 'server_error'),
    }
    
    if status_code in error_mappings:
        message, error_type = error_mappings[status_code]
        return WxTechAPIError(message, status_code=status_code, error_type=error_type)
    else:
        return WxTechAPIError(
            f"APIエラー: ステータスコード {status_code}", 
            status_code=status_code, 
            error_type='http_error'
        )
"""
WxTech API リクエスト処理

低レベルのHTTPリクエスト処理とレート制限を管理
"""

from __future__ import annotations
from typing import Any
import requests
import json
import time
import logging

from src.apis.wxtech.errors import WxTechAPIError, handle_http_error

logger = logging.getLogger(__name__)


class WxTechAPI:
    """WxTech API の低レベルリクエスト処理
    
    HTTPリクエスト、レート制限、エラーハンドリングを管理
    """
    
    # API設定
    BASE_URL = "https://wxtech.weathernews.com/api/v1"
    DEFAULT_TIMEOUT = 30
    
    def __init__(self, api_key: str, timeout: int = DEFAULT_TIMEOUT):
        """APIクライアントを初期化
        
        Args:
            api_key: WxTech API キー
            timeout: タイムアウト秒数（デフォルト: 30秒）
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
        # ヘッダー設定
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "WxTechAPIClient/1.0",
                "X-API-Key": self.api_key,
            }
        )
        
        # レート制限対策（秒間10リクエストまで）
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms
    
    def _rate_limit(self):
        """レート制限を適用"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def make_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """API リクエストを実行
        
        Args:
            endpoint: エンドポイント名
            params: リクエストパラメータ
            
        Returns:
            レスポンスデータ
            
        Raises:
            WxTechAPIError: API エラー
        """
        # レート制限
        self._rate_limit()
        
        # URL 構築
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            # リクエスト実行
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            # ステータスコードチェック
            if response.status_code != 200:
                raise handle_http_error(response.status_code)
            
            # JSON パース
            try:
                data = response.json()
            except json.JSONDecodeError:
                raise WxTechAPIError(
                    "レスポンスのJSONパースに失敗しました", 
                    status_code=response.status_code, 
                    error_type='http_error'
                )
            
            # エラーレスポンスチェック
            if "error" in data:
                error_msg = data.get("message", "不明なエラー")
                raise WxTechAPIError(
                    f"APIエラー: {error_msg}", 
                    status_code=response.status_code, 
                    error_type='http_error'
                )
            
            # 成功レスポンス検証
            if "wxdata" not in data or not data["wxdata"]:
                raise WxTechAPIError(
                    "天気データが含まれていません", 
                    status_code=response.status_code, 
                    error_type='http_error'
                )
            
            return data
            
        except requests.exceptions.Timeout:
            raise WxTechAPIError(
                f"リクエストがタイムアウトしました（{self.timeout}秒）", 
                error_type='timeout'
            )
        except requests.exceptions.ConnectionError:
            raise WxTechAPIError(
                "API サーバーに接続できません", 
                error_type='network_error'
            )
        except requests.exceptions.RequestException as e:
            raise WxTechAPIError(
                f"リクエスト実行エラー: {str(e)}", 
                error_type='network_error'
            )
    
    def close(self):
        """セッションを閉じる"""
        if hasattr(self, "session"):
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
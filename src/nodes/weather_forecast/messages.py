"""
Weather forecast error messages

天気予報ノードのエラーメッセージ定義
将来的な国際化（i18n）に対応できる構造
"""

from __future__ import annotations
from typing import Any


class Messages:
    """メッセージ管理クラス
    
    将来的にはロケール対応を追加可能
    """
    
    # API関連のエラーメッセージ
    API_ERRORS = {
        'api_key_not_found': (
            "気象APIキー（WXTECH_API_KEY）が設定されていません。\n"
            "設定方法: export WXTECH_API_KEY='your-api-key' または .envファイルに記載"
        ),
        'api_key_invalid': (
            "気象APIキーが無効です。\n"
            "WXTECH_API_KEYが正しく設定されているか確認してください。"
        ),
        'rate_limit': "気象APIのレート制限に達しました。しばらく待ってから再試行してください。",
        'network_error': "気象APIサーバーに接続できません。ネットワーク接続を確認してください。",
        'timeout': "気象APIへのリクエストがタイムアウトしました: {error}",
        'server_error': "気象APIサーバーでエラーが発生しました。しばらく待ってから再試行してください。",
        'unknown': "気象API接続エラー: {error}",
    }
    
    # 地点関連のエラーメッセージ
    LOCATION_ERRORS = {
        'not_found': "地点 '{location_name}' が見つかりません",
        'no_coordinates': "地点 '{location_name}' の緯度経度情報がありません",
        'invalid_coordinates': "無効な緯度経度: lat={lat}, lon={lon}",
    }
    
    # データ処理関連のエラーメッセージ
    DATA_ERRORS = {
        'empty_forecast': "地点 '{location_name}' の天気予報データが取得できませんでした",
        'insufficient_data': "気象変化分析に十分な予報データがありません: {count}件",
        'cache_error': "予報データのキャッシュ保存に失敗しました: {error}",
    }
    
    # ログメッセージ
    LOG_MESSAGES = {
        'api_retry': "Attempt {attempt}/{max_retries}: APIエラー ({error_type}). {delay}秒後にリトライします。",
        'empty_data_retry': "Attempt {attempt}/{max_retries}: 天気予報データが空です。{delay}秒後にリトライします。",
        'fetch_success': "Attempt {attempt}/{max_retries}: 天気予報データを正常に取得しました。",
        'location_parsed': "地点情報をパース: 名前='{name}', 緯度={lat}, 経度={lon}",
        'target_date': "対象日: {date}",
        'trend_analysis': "気象変化傾向: {summary}",
        'cache_saved': "予報データをキャッシュに保存しました",
        'temperature_diff': "前日との気温差: {location} - {diff}",
    }
    
    @classmethod
    def get(cls, category: str, key: str, **kwargs: Any) -> str:
        """メッセージを取得
        
        Args:
            category: メッセージカテゴリ（'API_ERRORS', 'LOCATION_ERRORS'など）
            key: メッセージキー
            **kwargs: メッセージのフォーマットパラメータ
            
        Returns:
            フォーマット済みメッセージ
        """
        messages = getattr(cls, category, {})
        template = messages.get(key, f"Unknown message: {category}.{key}")
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"{template} (Missing parameter: {e})"
    
    @classmethod
    def get_api_error(cls, key: str, **kwargs: Any) -> str:
        """APIエラーメッセージを取得"""
        return cls.get('API_ERRORS', key, **kwargs)
    
    @classmethod
    def get_location_error(cls, key: str, **kwargs: Any) -> str:
        """地点エラーメッセージを取得"""
        return cls.get('LOCATION_ERRORS', key, **kwargs)
    
    @classmethod
    def get_data_error(cls, key: str, **kwargs: Any) -> str:
        """データエラーメッセージを取得"""
        return cls.get('DATA_ERRORS', key, **kwargs)
    
    @classmethod
    def get_log_message(cls, key: str, **kwargs: Any) -> str:
        """ログメッセージを取得"""
        return cls.get('LOG_MESSAGES', key, **kwargs)
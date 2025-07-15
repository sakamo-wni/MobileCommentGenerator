"""セキュアな設定管理"""

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SecureConfigManager:
    """APIキーなどの機密情報を安全に管理するクラス"""
    
    def __init__(self, config_file: str = ".secure_config"):
        self.config_file = Path.home() / config_file
        self._cipher_suite: Fernet | None = None
        self._init_encryption()
    
    def _init_encryption(self) -> None:
        """暗号化の初期化"""
        # マシン固有の情報からキーを生成
        machine_id = self._get_machine_id()
        salt = b'mobile_comment_generator_salt'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        self._cipher_suite = Fernet(key)
    
    def _get_machine_id(self) -> str:
        """マシン固有のIDを取得"""
        # 環境変数から取得（CI/CD環境用）
        if os.getenv("MACHINE_ID"):
            return os.getenv("MACHINE_ID")
        
        # ホスト名とユーザー名の組み合わせ
        import socket
        hostname = socket.gethostname()
        username = os.getenv("USER", "default")
        return f"{hostname}_{username}"
    
    def save_api_key(self, provider: str, api_key: str) -> None:
        """APIキーを暗号化して保存"""
        if not api_key or api_key == "*" * 20:
            return
        
        # 既存の設定を読み込む
        config = self._load_config()
        
        # APIキーを暗号化
        encrypted_key = self._cipher_suite.encrypt(api_key.encode())
        config[provider] = base64.b64encode(encrypted_key).decode()
        
        # 保存
        self._save_config(config)
        logger.info(f"API key for {provider} saved securely")
    
    def get_api_key(self, provider: str) -> str | None:
        """暗号化されたAPIキーを復号して取得"""
        # まず環境変数をチェック
        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "wxtech": "WXTECH_API_KEY"
        }
        
        env_key = os.getenv(env_key_map.get(provider, ""))
        if env_key:
            return env_key
        
        # 暗号化された設定から取得
        config = self._load_config()
        encrypted_key = config.get(provider)
        
        if not encrypted_key:
            return None
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_key.encode())
            decrypted_key = self._cipher_suite.decrypt(encrypted_bytes)
            return decrypted_key.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key for {provider}: {e}")
            return None
    
    def remove_api_key(self, provider: str) -> None:
        """APIキーを削除"""
        config = self._load_config()
        if provider in config:
            del config[provider]
            self._save_config(config)
            logger.info(f"API key for {provider} removed")
    
    def _load_config(self) -> dict[str, Any]:
        """設定ファイルを読み込む"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _save_config(self, config: dict[str, Any]) -> None:
        """設定ファイルに保存"""
        try:
            # ディレクトリが存在しない場合は作成
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # ファイルのパーミッションを制限
            os.chmod(self.config_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")


# シングルトンインスタンス
_secure_config_instance: SecureConfigManager | None = None


def get_secure_config() -> SecureConfigManager:
    """セキュア設定マネージャーのシングルトンインスタンスを取得"""
    global _secure_config_instance
    if _secure_config_instance is None:
        _secure_config_instance = SecureConfigManager()
    return _secure_config_instance


def mask_api_key(api_key: str) -> str:
    """APIキーをマスク表示用に変換"""
    if not api_key or len(api_key) < 8:
        return "*" * 20
    
    # 最初の4文字と最後の4文字以外をマスク
    visible_start = api_key[:4]
    visible_end = api_key[-4:]
    masked_middle = "*" * (len(api_key) - 8)
    
    return f"{visible_start}{masked_middle}{visible_end}"
"""
ストレージ抽象化レイヤー

DynamoDBとローカルストレージの両方に対応できる基底クラス
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class StorageInterface(ABC):
    """ストレージインターフェース
    
    DynamoDBへの移行を考慮した抽象化レイヤー
    """
    
    @abstractmethod
    def put_item(self, table_name: str, item: Dict[str, Any]) -> None:
        """アイテムを保存
        
        Args:
            table_name: テーブル名（DynamoDBテーブル名に相当）
            item: 保存するアイテム
        """
        pass
    
    @abstractmethod
    def get_item(self, table_name: str, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """アイテムを取得
        
        Args:
            table_name: テーブル名
            key: プライマリキー（パーティションキー + ソートキー）
            
        Returns:
            アイテム、存在しない場合はNone
        """
        pass
    
    @abstractmethod
    def query(self, table_name: str, key_condition: Dict[str, Any], 
              limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """クエリ実行
        
        Args:
            table_name: テーブル名
            key_condition: キー条件
            limit: 取得件数の上限
            
        Returns:
            マッチしたアイテムのリスト
        """
        pass
    
    @abstractmethod
    def batch_write(self, table_name: str, items: List[Dict[str, Any]]) -> None:
        """バッチ書き込み
        
        Args:
            table_name: テーブル名
            items: 書き込むアイテムのリスト
        """
        pass
    
    @abstractmethod
    def delete_item(self, table_name: str, key: Dict[str, Any]) -> None:
        """アイテムを削除
        
        Args:
            table_name: テーブル名
            key: プライマリキー
        """
        pass
    
    @abstractmethod
    def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """テーブルを作成
        
        Args:
            table_name: テーブル名
            schema: テーブルスキーマ
        """
        pass
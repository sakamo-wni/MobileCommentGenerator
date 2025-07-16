"""Trie（トライ木）データ構造の実装 - 効率的な前方一致検索用"""

from dataclasses import dataclass, field


@dataclass
class TrieNode:
    """Trieのノード"""
    children: dict[str, 'TrieNode'] = field(default_factory=dict)
    locations: list['Location'] = field(default_factory=list)
    location_ids: set[int] = field(default_factory=set)  # 重複チェック用
    is_end_of_word: bool = False


class LocationTrie:
    """地点データ用のTrie構造
    
    効率的な前方一致検索を実現するためのデータ構造
    """
    
    def __init__(self):
        """初期化"""
        self.root = TrieNode()
        self._location_ids: dict[str, set[int]] = {}  # 重複チェック用（IDで管理）
    
    def insert(self, word: str, location: 'Location'):
        """単語と地点データをTrieに挿入
        
        Args:
            word: 挿入する単語（地点名）
            location: 関連付ける地点データ
        """
        if not word:
            return
        
        # 重複チェック用のキーを生成
        key = word.lower()
        location_id = id(location)
        
        if key not in self._location_ids:
            self._location_ids[key] = set()
        
        # 既に同じ地点が登録されている場合はスキップ
        if location_id in self._location_ids[key]:
            return
        
        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            # 各ノードに地点データを追加（前方一致検索用）
            # IDベースでの重複チェック（O(1)）
            if location_id not in node.location_ids:
                node.locations.append(location)
                node.location_ids.add(location_id)
        
        node.is_end_of_word = True
        self._location_ids[key].add(location_id)
    
    def search_prefix(self, prefix: str) -> list['Location']:
        """前方一致検索
        
        Args:
            prefix: 検索するプレフィックス
            
        Returns:
            プレフィックスにマッチする地点のリスト
        """
        if not prefix:
            return []
        
        node = self.root
        prefix_lower = prefix.lower()
        
        # プレフィックスまで辿る
        for char in prefix_lower:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # そのノードに保存されている地点データを返す
        return node.locations.copy()
    
    def search_exact(self, word: str) -> list['Location']:
        """完全一致検索
        
        Args:
            word: 検索する単語
            
        Returns:
            完全一致する地点のリスト
        """
        if not word:
            return []
        
        node = self.root
        word_lower = word.lower()
        
        for char in word_lower:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # 単語の終端でない場合は空リストを返す
        if not node.is_end_of_word:
            return []
        
        return node.locations.copy()
    
    def get_all_prefixes(self, word: str) -> dict[str, list['Location']]:
        """単語のすべてのプレフィックスとマッチする地点を取得
        
        Args:
            word: 対象の単語
            
        Returns:
            プレフィックスと地点リストの辞書
        """
        if not word:
            return {}
        
        results = {}
        node = self.root
        word_lower = word.lower()
        current_prefix = ""
        
        for char in word_lower:
            if char not in node.children:
                break
            node = node.children[char]
            current_prefix += char
            if node.locations:
                results[current_prefix] = node.locations.copy()
        
        return results
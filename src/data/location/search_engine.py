"""地点データ検索エンジン - 地点データの高速検索機能を提供"""

import logging
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict

from .models import Location
from .trie import LocationTrie

logger = logging.getLogger(__name__)


class LocationSearchEngine:
    """地点データ検索エンジン"""
    
    def __init__(self, locations: List[Location]):
        """初期化
        
        Args:
            locations: 検索対象の地点データリスト
        """
        self.locations = locations
        self._build_index()
    
    def _build_index(self):
        """検索用インデックスの構築"""
        logger.info("検索インデックスを構築中...")
        
        # 各種インデックスの初期化
        self.name_index: Dict[str, Location] = {}
        self.normalized_index: Dict[str, Location] = {}
        self.prefecture_index: Dict[str, List[Location]] = defaultdict(list)
        self.region_index: Dict[str, List[Location]] = defaultdict(list)
        self.prefix_trie = LocationTrie()  # Trie構造を使用
        
        # インデックスの構築
        for location in self.locations:
            # 名前インデックス
            self.name_index[location.name.lower()] = location
            self.normalized_index[location.normalized_name.lower()] = location
            
            # 都道府県インデックス
            if location.prefecture:
                self.prefecture_index[location.prefecture].append(location)
            
            # 地方インデックス
            if location.region:
                self.region_index[location.region].append(location)
            
            # プレフィックスインデックス（前方一致検索用）
            # Trieに挿入（効率的）
            self.prefix_trie.insert(location.name, location)
            if location.normalized_name.lower() != location.name.lower():
                self.prefix_trie.insert(location.normalized_name, location)
        
        logger.info(
            f"インデックス構築完了: "
            f"{len(self.name_index)}件の名前, "
            f"{len(self.prefecture_index)}都道府県, "
            f"{len(self.region_index)}地方"
        )
    
    def get_location(self, name: str) -> Optional[Location]:
        """地点名から地点データを取得
        
        Args:
            name: 地点名
            
        Returns:
            地点データ、見つからない場合はNone
        """
        if not name:
            return None
        
        name_lower = name.lower().strip()
        
        # 完全一致検索（名前）
        if name_lower in self.name_index:
            return self.name_index[name_lower]
        
        # 完全一致検索（正規化名）
        if name_lower in self.normalized_index:
            return self.normalized_index[name_lower]
        
        # 前方一致検索（Trieを使用）
        candidates = self.prefix_trie.search_prefix(name_lower)
        if candidates:
            if len(candidates) == 1:
                return candidates[0]
            # 複数候補がある場合は最短のものを選択
            candidates.sort(key=lambda loc: len(loc.name))
            return candidates[0]
        
        # 部分一致検索（fallback）
        for location in self.locations:
            if location.matches_query(name, fuzzy=True):
                return location
        
        logger.warning(f"地点が見つかりません: {name}")
        return None
    
    def search_locations(
        self, 
        query: str, 
        region: Optional[str] = None,
        prefecture: Optional[str] = None,
        fuzzy: bool = True,
        limit: int = 10
    ) -> List[Location]:
        """地点を検索
        
        Args:
            query: 検索クエリ
            region: 地方でフィルタ
            prefecture: 都道府県でフィルタ
            fuzzy: 曖昧検索を有効にするか
            limit: 最大結果数
            
        Returns:
            検索結果のリスト
        """
        results = []
        
        # フィルタリング対象の決定
        candidates = self.locations
        
        if region:
            candidates = self.get_locations_by_region(region)
        elif prefecture:
            candidates = self.get_locations_by_prefecture(prefecture)
        
        # クエリによる検索
        if query:
            for location in candidates:
                if location.matches_query(query, fuzzy=fuzzy):
                    results.append(location)
                    if len(results) >= limit:
                        break
        else:
            # クエリがない場合は全件返す
            results = candidates[:limit]
        
        return results
    
    def get_locations_by_region(self, region: str) -> List[Location]:
        """地方から地点リストを取得
        
        Args:
            region: 地方名
            
        Returns:
            該当する地点のリスト
        """
        return self.region_index.get(region, [])
    
    def get_locations_by_prefecture(self, prefecture: str) -> List[Location]:
        """都道府県から地点リストを取得
        
        Args:
            prefecture: 都道府県名
            
        Returns:
            該当する地点のリスト
        """
        return self.prefecture_index.get(prefecture, [])
    
    def get_nearby_locations(
        self, 
        location: Location, 
        radius_km: float = 50.0,
        limit: int = 10
    ) -> List[Location]:
        """指定地点の近隣地点を取得
        
        Args:
            location: 基準地点
            radius_km: 検索半径（km）
            limit: 最大結果数
            
        Returns:
            近隣地点のリスト（距離順）
        """
        if not location.latitude or not location.longitude:
            logger.warning(f"座標情報がありません: {location.name}")
            return []
        
        nearby = []
        
        for other in self.locations:
            if other == location:
                continue
            
            distance = location.distance_to(other)
            if distance is not None and distance <= radius_km:
                nearby.append((distance, other))
        
        # 距離順にソート
        nearby.sort(key=lambda x: x[0])
        
        # 上位N件を返す
        return [loc for _, loc in nearby[:limit]]
    
    def get_statistics(self) -> Dict[str, any]:
        """検索エンジンの統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        stats = {
            "total_locations": len(self.locations),
            "indexed_names": len(self.name_index),
            "indexed_normalized": len(self.normalized_index),
            "prefectures": len(self.prefecture_index),
            "regions": len(self.region_index),
            "prefix_patterns": len(self.prefix_trie._location_ids),
            "locations_with_coordinates": sum(
                1 for loc in self.locations 
                if loc.latitude and loc.longitude
            ),
            "locations_by_region": {
                region: len(locations) 
                for region, locations in self.region_index.items()
            },
            "locations_by_prefecture": {
                pref: len(locations) 
                for pref, locations in self.prefecture_index.items()
            }
        }
        
        return stats
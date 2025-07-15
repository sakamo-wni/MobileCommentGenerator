"""リファクタリングされた地点データ管理システム - ファサードパターンで各コンポーネントを統合"""

import logging
from typing import Any
from pathlib import Path

from .models import Location
from .csv_loader import LocationCSVLoader
from .search_engine import LocationSearchEngine

logger = logging.getLogger(__name__)


class LocationManagerRefactored:
    """地点データ管理システム（リファクタリング版）
    
    CSVローダーと検索エンジンを統合し、シンプルなインターフェースを提供
    """
    
    # シングルトンインスタンス
    _instance = None
    _initialized = False
    
    def __new__(cls, csv_path: str | None = None):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, csv_path: str | None = None):
        """初期化
        
        Args:
            csv_path: CSVファイルのパス
        """
        # 既に初期化済みの場合はスキップ
        if LocationManagerRefactored._initialized:
            return
        
        logger.info("LocationManagerを初期化中...")
        
        # コンポーネントの初期化
        self.csv_loader = LocationCSVLoader(csv_path)
        self.locations: list[Location] = []
        self.search_engine: LocationSearchEngine | None = None
        self._location_order: dict[str, int] = {}
        
        # データの読み込み
        self.load_locations()
        
        LocationManagerRefactored._initialized = True
    
    def load_locations(self) -> int:
        """CSVファイルから地点データを読み込む
        
        Returns:
            読み込まれた地点数
        """
        # CSVローダーでデータを読み込み
        self.locations = self.csv_loader.load_locations()
        
        # 検索エンジンの初期化
        self.search_engine = LocationSearchEngine(self.locations)
        
        # 地点の表示順序を設定
        self._setup_location_order()
        
        logger.info(f"地点データの読み込み完了: {len(self.locations)}件")
        return len(self.locations)
    
    def _setup_location_order(self):
        """地点の表示順序を設定"""
        # デフォルトの順序（北から南へ）
        default_order = [
            # 北海道・東北
            "稚内", "留萌", "網走", "旭川", "岩見沢", "札幌", "小樽", "函館",
            "青森", "むつ", "八戸", "盛岡", "宮古", "大船渡",
            "秋田", "横手", "山形", "米沢", "仙台", "白石",
            "福島", "郡山", "いわき", "会津若松",
            # 関東
            "水戸", "土浦", "つくば", "宇都宮", "大田原", "日光",
            "前橋", "高崎", "みなかみ", "熊谷", "秩父", "さいたま", "川越",
            "千葉", "銚子", "館山", "東京", "大島", "八丈島", "父島",
            "横浜", "小田原", "箱根",
            # 中部
            "新潟", "長岡", "上越", "富山", "高岡", "金沢", "輪島",
            "福井", "敦賀", "甲府", "河口湖", "長野", "松本", "飯田",
            "岐阜", "高山", "静岡", "浜松", "清水", "網代",
            "名古屋", "豊橋", "豊田",
            # 近畿
            "津", "尾鷲", "大津", "彦根", "京都", "舞鶴",
            "大阪", "堺", "神戸", "豊岡", "姫路",
            "奈良", "橿原", "風屋", "和歌山", "潮岬", "日和佐",
            # 中国・四国
            "鳥取", "米子", "松江", "出雲", "岡山", "倉敷",
            "広島", "福山", "山口", "下関",
            "徳島", "鳴門", "高松", "丸亀", "松山", "新居浜", "宇和島",
            "高知", "室戸岬", "四万十",
            # 九州・沖縄
            "福岡", "北九州", "佐賀", "唐津", "長崎", "佐世保",
            "熊本", "阿蘇", "大分", "別府", "宮崎", "延岡",
            "鹿児島", "屋久島", "奄美", "那覇", "名護", 
            "宮古島", "石垣島", "与那国島", "久米島", "大東島"
        ]
        
        # 順序辞書の作成
        self._location_order = {name: i for i, name in enumerate(default_order)}
    
    def get_location(self, name: str) -> Location | None:
        """地点名から地点データを取得
        
        Args:
            name: 地点名
            
        Returns:
            地点データ、見つからない場合はNone
        """
        if not self.search_engine:
            logger.error("検索エンジンが初期化されていません")
            return None
        
        return self.search_engine.get_location(name)
    
    def search_locations(
        self, 
        query: str = "",
        region: str | None = None,
        prefecture: str | None = None,
        fuzzy: bool = True,
        limit: int = 10
    ) -> list[Location]:
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
        if not self.search_engine:
            logger.error("検索エンジンが初期化されていません")
            return []
        
        results = self.search_engine.search_locations(
            query=query,
            region=region,
            prefecture=prefecture,
            fuzzy=fuzzy,
            limit=limit
        )
        
        # 結果を表示順序でソート
        return self._sort_locations_by_order(results)
    
    def get_locations_by_region(self, region: str) -> list[Location]:
        """地方から地点リストを取得
        
        Args:
            region: 地方名
            
        Returns:
            該当する地点のリスト（表示順序でソート済み）
        """
        if not self.search_engine:
            logger.error("検索エンジンが初期化されていません")
            return []
        
        locations = self.search_engine.get_locations_by_region(region)
        return self._sort_locations_by_order(locations)
    
    def get_locations_by_prefecture(self, prefecture: str) -> list[Location]:
        """都道府県から地点リストを取得
        
        Args:
            prefecture: 都道府県名
            
        Returns:
            該当する地点のリスト（表示順序でソート済み）
        """
        if not self.search_engine:
            logger.error("検索エンジンが初期化されていません")
            return []
        
        locations = self.search_engine.get_locations_by_prefecture(prefecture)
        return self._sort_locations_by_order(locations)
    
    def get_nearby_locations(
        self, 
        location: Location, 
        radius_km: float = 50.0,
        limit: int = 10
    ) -> list[Location]:
        """指定地点の近隣地点を取得
        
        Args:
            location: 基準地点
            radius_km: 検索半径（km）
            limit: 最大結果数
            
        Returns:
            近隣地点のリスト（距離順）
        """
        if not self.search_engine:
            logger.error("検索エンジンが初期化されていません")
            return []
        
        return self.search_engine.get_nearby_locations(location, radius_km, limit)
    
    def get_all_locations(self) -> list[Location]:
        """全地点データを取得（表示順序でソート済み）
        
        Returns:
            全地点のリスト
        """
        return self._sort_locations_by_order(self.locations)
    
    def _sort_locations_by_order(self, locations: list[Location]) -> list[Location]:
        """地点リストを表示順序でソート
        
        Args:
            locations: ソート対象の地点リスト
            
        Returns:
            ソート済みの地点リスト
        """
        def sort_key(location: Location) -> tuple:
            # 順序が定義されている場合はその値、なければ999999（最後尾）
            order = self._location_order.get(location.name, 999999)
            # 同じ順序の場合は名前でソート
            return (order, location.name)
        
        return sorted(locations, key=sort_key)
    
    def get_statistics(self) -> dict[str, Any]:
        """統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        if not self.search_engine:
            return {"error": "検索エンジンが初期化されていません"}
        
        # 基本統計
        stats = self.search_engine.get_statistics()
        
        # 追加情報
        stats.update({
            "csv_path": self.csv_loader.csv_path,
            "location_order_defined": len(self._location_order),
            "singleton_instance": id(self)
        })
        
        return stats
    
    @classmethod
    def reset_instance(cls):
        """シングルトンインスタンスをリセット（テスト用）"""
        cls._instance = None
        cls._initialized = False
"""
地点データ管理システム

Chiten.csvを活用した地点データの管理・検索機能を提供する
Issue #2の実装: 地点データ管理システム
"""

import csv
import os
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any
import logging
from pathlib import Path

from src.utils.exceptions import DataValidationError, LocationValidationError

# ログ設定
logger = logging.getLogger(__name__)


@dataclass
class Location:
    """地点データクラス

    Attributes:
        name: 地点名（元の名前）
        normalized_name: 正規化された地点名
        prefecture: 都道府県名（推定）
        latitude: 緯度（度）
        longitude: 経度（度）
        region: 地方区分
        location_type: 地点タイプ（市、区、町、村など）
        population: 人口（推定）
        metadata: その他のメタデータ
    """

    name: str
    normalized_name: str
    prefecture: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None
    location_type: Optional[str] = None
    population: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """データクラス初期化後の処理"""
        # 正規化名が設定されていない場合は自動生成
        if not self.normalized_name:
            self.normalized_name = self._normalize_name(self.name)

        # 都道府県名が設定されていない場合は推定
        if not self.prefecture:
            self.prefecture = self._infer_prefecture()

        # 地方区分が設定されていない場合は推定
        if not self.region:
            self.region = self._infer_region()

    def _normalize_name(self, name: str) -> str:
        """地点名を正規化

        Args:
            name: 元の地点名

        Returns:
            正規化された地点名
        """
        if not name:
            return ""

        # Unicode正規化（NFKCで全角・半角統一）
        normalized = unicodedata.normalize("NFKC", name)

        # 前後の空白除去
        normalized = normalized.strip()

        # ひらがなをカタカナに変換（オプション）
        # normalized = self._hiragana_to_katakana(normalized)

        return normalized

    def _hiragana_to_katakana(self, text: str) -> str:
        """ひらがなをカタカナに変換"""
        katakana = ""
        for char in text:
            code = ord(char)
            # ひらがな範囲（あ-ん: 0x3042-0x3093）
            if 0x3042 <= code <= 0x3093:
                katakana += chr(code + 0x60)  # カタカナに変換
            else:
                katakana += char
        return katakana

    def _infer_prefecture(self) -> Optional[str]:
        """地点名から都道府県名を推定

        Returns:
            推定された都道府県名
        """
        # 都道府県庁所在地・主要都市マッピング
        prefecture_mapping = {
            # 北海道
            "稚内": "北海道",
            "旭川": "北海道",
            "札幌": "北海道",
            "函館": "北海道",
            "帯広": "北海道",
            "釧路": "北海道",
            "北見": "北海道",
            "室蘭": "北海道",
            "苫小牧": "北海道",
            "根室": "北海道",
            "網走": "北海道",
            "留萌": "北海道",
            "名寄": "北海道",
            "紋別": "北海道",
            "小樽": "北海道",
            "岩見沢": "北海道",
            # 東北
            "青森": "青森県",
            "八戸": "青森県",
            "秋田": "秋田県",
            "盛岡": "岩手県",
            "仙台": "宮城県",
            "山形": "山形県",
            "福島": "福島県",
            # 関東
            "水戸": "茨城県",
            "土浦": "茨城県",
            "宇都宮": "栃木県",
            "前橋": "群馬県",
            "みなかみ": "群馬県",
            "さいたま": "埼玉県",
            "熊谷": "埼玉県",
            "秩父": "埼玉県",
            "千葉": "千葉県",
            "銚子": "千葉県",
            "館山": "千葉県",
            "東京": "東京都",
            "父島": "東京都",
            "横浜": "神奈川県",
            "小田原": "神奈川県",
            # 中部
            "新潟": "新潟県",
            "富山": "富山県",
            "金沢": "石川県",
            "福井": "福井県",
            "甲府": "山梨県",
            "長野": "長野県",
            "岐阜": "岐阜県",
            "静岡": "静岡県",
            "名古屋": "愛知県",
            # 近畿
            "津": "三重県",
            "大津": "滋賀県",
            "京都": "京都府",
            "大阪": "大阪府",
            "神戸": "兵庫県",
            "奈良": "奈良県",
            "和歌山": "和歌山県",
            # 中国
            "鳥取": "鳥取県",
            "松江": "島根県",
            "岡山": "岡山県",
            "広島": "広島県",
            "山口": "山口県",
            # 四国
            "徳島": "徳島県",
            "高松": "香川県",
            "松山": "愛媛県",
            "高知": "高知県",
            # 九州・沖縄
            "福岡": "福岡県",
            "佐賀": "佐賀県",
            "長崎": "長崎県",
            "熊本": "熊本県",
            "大分": "大分県",
            "宮崎": "宮崎県",
            "鹿児島": "鹿児島県",
            "那覇": "沖縄県",
        }

        return prefecture_mapping.get(self.normalized_name)

    def _infer_region(self) -> Optional[str]:
        """都道府県から地方区分を推定

        Returns:
            推定された地方区分
        """
        if not self.prefecture:
            return None

        region_mapping = {
            "北海道": "北海道",
            "青森県": "東北",
            "岩手県": "東北",
            "宮城県": "東北",
            "秋田県": "東北",
            "山形県": "東北",
            "福島県": "東北",
            "茨城県": "関東",
            "栃木県": "関東",
            "群馬県": "関東",
            "埼玉県": "関東",
            "千葉県": "関東",
            "東京都": "関東",
            "神奈川県": "関東",
            "新潟県": "中部",
            "富山県": "中部",
            "石川県": "中部",
            "福井県": "中部",
            "山梨県": "中部",
            "長野県": "中部",
            "岐阜県": "中部",
            "静岡県": "中部",
            "愛知県": "中部",
            "三重県": "近畿",
            "滋賀県": "近畿",
            "京都府": "近畿",
            "大阪府": "近畿",
            "兵庫県": "近畿",
            "奈良県": "近畿",
            "和歌山県": "近畿",
            "鳥取県": "中国",
            "島根県": "中国",
            "岡山県": "中国",
            "広島県": "中国",
            "山口県": "中国",
            "徳島県": "四国",
            "香川県": "四国",
            "愛媛県": "四国",
            "高知県": "四国",
            "福岡県": "九州",
            "佐賀県": "九州",
            "長崎県": "九州",
            "熊本県": "九州",
            "大分県": "九州",
            "宮崎県": "九州",
            "鹿児島県": "九州",
            "沖縄県": "九州",
        }

        return region_mapping.get(self.prefecture)

    def distance_to(self, other: "Location") -> Optional[float]:
        """他の地点との距離を計算（km）

        Args:
            other: 比較対象の地点

        Returns:
            距離（km）、座標情報がない場合はNone
        """
        if not all([self.latitude, self.longitude, other.latitude, other.longitude]):
            return None

        import math

        # ハヴァーサイン式
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # 地球の半径（km）
        earth_radius = 6371.0

        return earth_radius * c

    def matches_query(self, query: str, fuzzy: bool = True) -> bool:
        """検索クエリにマッチするかチェック

        Args:
            query: 検索クエリ
            fuzzy: あいまい検索を行うか

        Returns:
            マッチする場合True
        """
        if not query:
            return False

        query_normalized = self._normalize_name(query)

        # 完全一致
        if self.normalized_name == query_normalized:
            return True

        # 部分一致
        if query_normalized in self.normalized_name or self.normalized_name in query_normalized:
            return True

        # 都道府県名での一致
        if self.prefecture and query_normalized in self.prefecture:
            return True

        if not fuzzy:
            return False

        # あいまい検索（レーベンシュタイン距離）
        distance = self._levenshtein_distance(self.normalized_name, query_normalized)
        max_length = max(len(self.normalized_name), len(query_normalized))

        # 類似度が70%以上の場合マッチとみなす
        similarity = 1.0 - (distance / max_length) if max_length > 0 else 0.0
        return similarity >= 0.7

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """レーベンシュタイン距離を計算

        Args:
            s1: 文字列1
            s2: 文字列2

        Returns:
            レーベンシュタイン距離
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            地点データの辞書
        """
        return {
            "name": self.name,
            "normalized_name": self.normalized_name,
            "prefecture": self.prefecture,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "region": self.region,
            "location_type": self.location_type,
            "population": self.population,
            "metadata": self.metadata,
        }


class LocationManager:
    """地点データ管理クラス

    Chiten.csvからの地点データ読み込み・管理・検索機能を提供
    """

    def __init__(self, csv_path: Optional[str] = None):
        """地点管理システムを初期化

        Args:
            csv_path: CSVファイルのパス（Noneの場合はデフォルトパス使用）
        """
        self.csv_path = csv_path or self._get_default_csv_path()
        self.locations: List[Location] = []
        self.location_index: Dict[str, List[Location]] = {}
        self.loaded_at: Optional[datetime] = None

        # 自動読み込み
        if os.path.exists(self.csv_path):
            self.load_locations()
        else:
            logger.warning(f"CSVファイルが見つかりません: {self.csv_path}")
            self._load_default_locations()

    def _get_default_csv_path(self) -> str:
        """デフォルトCSVパスを取得

        Returns:
            デフォルトCSVファイルパス
        """
        # プロジェクトルートを探す
        current_dir = Path(__file__).parent
        while current_dir.parent != current_dir:
            # まず frontend/public/地点名.csv を探す（優先）
            csv_path = current_dir / "frontend" / "public" / "地点名.csv"
            if csv_path.exists():
                return str(csv_path)
            current_dir = current_dir.parent

        # 現在のディレクトリから探す
        current_dir = Path(__file__).parent
        # 次に src/data/Chiten.csv を探す
        csv_path = current_dir / "Chiten.csv"
        if csv_path.exists():
            # Chiten.csvが見つかった場合、地点名.csvも探す
            project_root = current_dir.parent.parent
            location_csv = project_root / "frontend" / "public" / "地点名.csv"
            if location_csv.exists():
                return str(location_csv)
            return str(csv_path)

        # 見つからない場合は地点名.csv を優先的に使用
        return "frontend/public/地点名.csv"

    def load_locations(self) -> int:
        """CSVファイルから地点データを読み込み

        Returns:
            読み込んだ地点数
        """
        try:
            self.locations.clear()

            with open(self.csv_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row_num, row in enumerate(reader, 2):  # ヘッダー行を考慮して2から開始
                    try:
                        # 地点名の取得
                        name = row.get("地点名", "").strip()
                        if not name:
                            continue

                        # 緯度経度の取得と検証
                        lat_str = row.get("緯度", "").strip()
                        lon_str = row.get("経度", "").strip()

                        latitude = float(lat_str) if lat_str else None
                        longitude = float(lon_str) if lon_str else None

                        # 緯度経度の妥当性チェック
                        if latitude is not None and not (-90 <= latitude <= 90):
                            logger.warning(f"無効な緯度: {row_num}行目 - {name} ({latitude})")
                            latitude = None

                        if longitude is not None and not (-180 <= longitude <= 180):
                            logger.warning(f"無効な経度: {row_num}行目 - {name} ({longitude})")
                            longitude = None

                        # 地点データを作成
                        location = Location(
                            name=name, normalized_name="", latitude=latitude, longitude=longitude
                        )
                        self.locations.append(location)

                    except (ValueError, KeyError) as e:
                        logger.warning(f"データ解析エラー: {row_num}行目 - {str(e)}")
                        continue

            self._build_index()
            self.loaded_at = datetime.now()

            logger.info(f"地点データ読み込み完了: {len(self.locations)}件")
            return len(self.locations)

        except FileNotFoundError:
            logger.warning(f"CSVファイルが見つかりません: {self.csv_path}")
            self._load_default_locations()
            return len(self.locations)
        except (IOError, OSError) as e:
            logger.error(f"地点データ読み込みエラー: {str(e)}")
            self._load_default_locations()
            return len(self.locations)

    def _load_default_locations(self):
        """デフォルト地点データを読み込み"""
        logger.info("デフォルト地点データを使用します")

        default_locations = [
            "稚内",
            "旭川",
            "札幌",
            "函館",
            "帯広",
            "釧路",
            "北見",
            "室蘭",
            "苫小牧",
            "根室",
            "青森",
            "八戸",
            "秋田",
            "盛岡",
            "仙台",
            "山形",
            "福島",
            "水戸",
            "宇都宮",
            "前橋",
            "さいたま",
            "千葉",
            "東京",
            "横浜",
            "新潟",
            "富山",
            "金沢",
            "福井",
            "甲府",
            "長野",
            "岐阜",
            "静岡",
            "名古屋",
            "津",
            "大津",
            "京都",
            "大阪",
            "神戸",
            "奈良",
            "和歌山",
            "鳥取",
            "松江",
            "岡山",
            "広島",
            "山口",
            "徳島",
            "高松",
            "松山",
            "高知",
            "福岡",
            "佐賀",
            "長崎",
            "熊本",
            "大分",
            "宮崎",
            "鹿児島",
            "那覇",
        ]

        self.locations = [Location(name=name, normalized_name="") for name in default_locations]
        self._build_index()
        self.loaded_at = datetime.now()

    def _build_index(self):
        """検索用インデックスを構築"""
        self.location_index.clear()

        for location in self.locations:
            # 正規化名でインデックス
            key = location.normalized_name.lower()
            if key not in self.location_index:
                self.location_index[key] = []
            self.location_index[key].append(location)

            # 都道府県名でもインデックス
            if location.prefecture:
                pref_key = location.prefecture.lower()
                if pref_key not in self.location_index:
                    self.location_index[pref_key] = []
                self.location_index[pref_key].append(location)

    def search_location(
        self, query: str, max_results: int = 10, fuzzy: bool = True
    ) -> List[Location]:
        """地点を検索

        Args:
            query: 検索クエリ
            max_results: 最大結果数
            fuzzy: あいまい検索を行うか

        Returns:
            検索結果の地点リスト
        """
        if not query or not self.locations:
            return []

        results = []
        query_normalized = query.strip().lower()

        # 1. 完全一致検索
        if query_normalized in self.location_index:
            results.extend(self.location_index[query_normalized])

        # 2. 部分一致検索
        for location in self.locations:
            if location not in results and location.matches_query(query, fuzzy=False):
                results.append(location)

        # 3. あいまい検索（必要に応じて）
        if fuzzy and len(results) < max_results:
            for location in self.locations:
                if location not in results and location.matches_query(query, fuzzy=True):
                    results.append(location)

        return results[:max_results]

    def get_location(self, name: str) -> Optional[Location]:
        """地点名から地点を取得（完全一致）

        Args:
            name: 地点名

        Returns:
            地点データ、見つからない場合はNone
        """
        name_normalized = name.strip().lower()

        # インデックス検索
        if name_normalized in self.location_index:
            candidates = self.location_index[name_normalized]
            if candidates:
                return candidates[0]

        # 線形検索
        for location in self.locations:
            if location.normalized_name.lower() == name_normalized:
                return location

        return None

    def get_locations_by_region(self, region: str) -> List[Location]:
        """地方区分で地点を取得

        Args:
            region: 地方区分（北海道、東北、関東など）

        Returns:
            該当地点のリスト
        """
        return [loc for loc in self.locations if loc.region == region]

    def get_locations_by_prefecture(self, prefecture: str) -> List[Location]:
        """都道府県で地点を取得

        Args:
            prefecture: 都道府県名

        Returns:
            該当地点のリスト
        """
        return [loc for loc in self.locations if loc.prefecture == prefecture]

    def get_nearby_locations(
        self,
        target: Union[Location, Tuple[float, float]],
        radius_km: float = 100,
        max_results: int = 10,
    ) -> List[Tuple[Location, float]]:
        """近隣地点を取得

        Args:
            target: 基準地点（LocationオブジェクトまたはLatLon座標）
            radius_km: 検索半径（km）
            max_results: 最大結果数

        Returns:
            (地点, 距離)のタプルリスト（距離順）
        """
        if isinstance(target, tuple):
            # 座標から仮想地点を作成
            target_location = Location(
                name="検索基準点",
                normalized_name="検索基準点",
                latitude=target[0],
                longitude=target[1],
            )
        else:
            target_location = target

        if not target_location.latitude or not target_location.longitude:
            return []

        nearby = []
        for location in self.locations:
            if location == target_location:
                continue

            distance = target_location.distance_to(location)
            if distance is not None and distance <= radius_km:
                nearby.append((location, distance))

        # 距離順でソート
        nearby.sort(key=lambda x: x[1])
        return nearby[:max_results]

    def get_all_locations(self) -> List[Location]:
        """全地点データを取得

        Returns:
            全地点のリスト
        """
        return self.locations.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得

        Returns:
            統計情報の辞書
        """
        if not self.locations:
            return {}

        # 地方別集計
        region_counts = {}
        for location in self.locations:
            region = location.region or "不明"
            region_counts[region] = region_counts.get(region, 0) + 1

        # 都道府県別集計
        prefecture_counts = {}
        for location in self.locations:
            prefecture = location.prefecture or "不明"
            prefecture_counts[prefecture] = prefecture_counts.get(prefecture, 0) + 1

        return {
            "total_locations": len(self.locations),
            "regions": dict(sorted(region_counts.items(), key=lambda x: x[1], reverse=True)),
            "prefectures": dict(
                sorted(prefecture_counts.items(), key=lambda x: x[1], reverse=True)
            ),
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "csv_path": self.csv_path,
        }


# グローバルインスタンス
_location_manager: Optional[LocationManager] = None


def get_location_manager(csv_path: Optional[str] = None) -> LocationManager:
    """LocationManagerのシングルトンインスタンスを取得

    Args:
        csv_path: CSVファイルのパス（初回のみ有効）

    Returns:
        LocationManagerインスタンス
    """
    global _location_manager

    if _location_manager is None:
        _location_manager = LocationManager(csv_path)

    return _location_manager


# 便利関数
def load_locations_from_csv(csv_path: str = "Chiten.csv") -> List[Location]:
    """CSVファイルから地点データを読み込み

    Args:
        csv_path: CSVファイルのパス

    Returns:
        地点データのリスト
    """
    manager = LocationManager(csv_path)
    return manager.get_all_locations()


def search_location(query: str, max_results: int = 10, fuzzy: bool = True) -> List[Location]:
    """地点検索の便利関数

    Args:
        query: 検索クエリ
        max_results: 最大結果数
        fuzzy: あいまい検索を行うか

    Returns:
        検索結果の地点リスト
    """
    manager = get_location_manager()
    return manager.search_location(query, max_results, fuzzy)


def get_location_by_name(name: str) -> Optional[Location]:
    """地点名から地点を取得する便利関数

    Args:
        name: 地点名

    Returns:
        地点データ、見つからない場合はNone
    """
    manager = get_location_manager()
    return manager.get_location(name)


if __name__ == "__main__":
    # テスト用コード
    print("=== 地点データ管理システムテスト ===")

    # LocationManagerの初期化
    manager = get_location_manager()

    # 統計情報の表示
    stats = manager.get_statistics()
    print(f"読み込み地点数: {stats['total_locations']}")
    print(f"地方別分布: {stats['regions']}")

    # 検索テスト
    print("\n=== 検索テスト ===")

    # 東京の検索
    tokyo_results = manager.search_location("東京")
    print(f"「東京」検索結果: {[loc.name for loc in tokyo_results]}")

    # あいまい検索テスト
    fuzzy_results = manager.search_location("おおさか", fuzzy=True)
    print(f"「おおさか」あいまい検索結果: {[loc.name for loc in fuzzy_results]}")

    # 地方別取得テスト
    kanto_locations = manager.get_locations_by_region("関東")
    print(f"関東地方の地点: {[loc.name for loc in kanto_locations]}")

    # 便利関数テスト
    sapporo = get_location_by_name("札幌")
    if sapporo:
        print(f"札幌の情報: {sapporo.to_dict()}")

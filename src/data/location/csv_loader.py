"""地点データCSVローダー - CSVファイルから地点データを読み込む"""

from __future__ import annotations
import csv
import logging
from pathlib import Path
from typing import Any

from .models import Location

logger = logging.getLogger(__name__)


class LocationCSVLoader:
    """地点データCSVローダー"""
    
    def __init__(self, csv_path: str | None = None, coordinates_csv_path: str | None = None):
        """初期化
        
        Args:
            csv_path: CSVファイルのパス。Noneの場合はデフォルトパスを使用
            coordinates_csv_path: 緯度経度CSVファイルのパス。Noneの場合はデフォルトパスを使用
        """
        self.csv_path = csv_path or self._get_default_csv_path()
        self.coordinates_csv_path = coordinates_csv_path or self._get_default_coordinates_csv_path()
        self._coordinates_cache = None
    
    def _get_default_csv_path(self) -> str:
        """デフォルトのCSVファイルパスを取得"""
        current_file_path = Path(__file__).resolve()
        
        # 現在のファイルから相対的にChiten.csvを探す
        possible_paths = [
            # src/data/location/csv_loader.py から src/data/Chiten.csv
            current_file_path.parent.parent / "Chiten.csv",
            # プロジェクトルートから
            current_file_path.parent.parent.parent.parent / "data" / "Chiten.csv",
            # 現在のディレクトリ
            Path("Chiten.csv"),
            Path("data/Chiten.csv"),
            Path("src/data/Chiten.csv"),
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Chiten.csvを検出: {path}")
                return str(path)
        
        # 見つからない場合はデフォルトパスを返す（エラーは後で発生）
        default_path = "src/data/Chiten.csv"
        logger.warning(f"Chiten.csvが見つかりません。デフォルトパスを使用: {default_path}")
        return default_path
    
    def _get_default_coordinates_csv_path(self) -> str:
        """デフォルトの緯度経度CSVファイルパスを取得"""
        current_file_path = Path(__file__).resolve()
        
        # 現在のファイルから相対的にlocation_coordinates.csvを探す
        possible_paths = [
            # src/data/location/csv_loader.py から src/data/location_coordinates.csv
            current_file_path.parent.parent / "location_coordinates.csv",
            # プロジェクトルートから
            current_file_path.parent.parent.parent.parent / "data" / "location_coordinates.csv",
            # 現在のディレクトリ
            Path("location_coordinates.csv"),
            Path("data/location_coordinates.csv"),
            Path("src/data/location_coordinates.csv"),
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"location_coordinates.csvを検出: {path}")
                return str(path)
        
        # 見つからない場合はデフォルトパスを返す（エラーは後で発生）
        default_path = "src/data/location_coordinates.csv"
        logger.warning(f"location_coordinates.csvが見つかりません。デフォルトパスを使用: {default_path}")
        return default_path
    
    def load_locations(self) -> list[Location]:
        """CSVファイルから地点データを読み込む
        
        Returns:
            読み込まれた地点データのリスト
        """
        locations = []
        missing_coordinates = []
        
        try:
            with open(self.csv_path, "r", encoding="utf-8-sig") as f:
                # Chiten.csvは地点名のみの単純なリストなので、単純に行ごとに読み込む
                for line_num, line in enumerate(f, start=1):
                    location_name = line.strip()
                    if location_name:  # 空行をスキップ
                        # 地点名から緯度経度情報を取得
                        location_data = self._get_location_coordinates(location_name)
                        if location_data:
                            location = Location(
                                name=location_name,
                                normalized_name=location_name,
                                latitude=location_data.get("latitude"),
                                longitude=location_data.get("longitude"),
                                prefecture=location_data.get("prefecture")
                            )
                            locations.append(location)
                        else:
                            missing_coordinates.append(location_name)
                
                # エラーサマリーを表示
                if missing_coordinates:
                    logger.warning(f"座標情報が見つからない地点: {len(missing_coordinates)}件")
                    logger.warning(f"対象地点: {', '.join(missing_coordinates[:10])}" + 
                                 ("..." if len(missing_coordinates) > 10 else ""))
                
                logger.info(f"{len(locations)}件の地点データを読み込みました（全{len(locations) + len(missing_coordinates)}件中）")
                
                # データが読み込めなかった場合はデフォルトデータを使用
                if not locations:
                    logger.warning("CSVからデータを読み込めませんでした。デフォルトデータを使用します")
                    return self._load_default_locations()
                
                return locations
                
        except FileNotFoundError:
            logger.error(f"CSVファイルが見つかりません: {self.csv_path}")
            return self._load_default_locations()
        except Exception as e:
            logger.error(f"CSV読み込みエラー: {e}")
            return self._load_default_locations()
    
    def _parse_location_row(self, row: dict[str, str]) -> Location | None:
        """CSV行から地点データを解析
        
        Args:
            row: CSV行データ
            
        Returns:
            解析された地点データ、失敗時はNone
        """
        # 必須フィールドの確認
        name = row.get("name", "").strip()
        if not name:
            return None
        
        # 緯度・経度の解析
        try:
            latitude = float(row.get("latitude", 0)) if row.get("latitude") else None
            longitude = float(row.get("longitude", 0)) if row.get("longitude") else None
        except (ValueError, TypeError):
            latitude = longitude = None
        
        # 人口の解析
        try:
            population = int(row.get("population", 0)) if row.get("population") else None
        except (ValueError, TypeError):
            population = None
        
        # Locationオブジェクトの作成
        location = Location(
            name=name,
            normalized_name=row.get("normalized_name", "").strip() or name,
            prefecture=row.get("prefecture", "").strip() or None,
            latitude=latitude,
            longitude=longitude,
            region=row.get("region", "").strip() or None,
            location_type=row.get("location_type", "").strip() or None,
            population=population,
            metadata={
                "raw_data": dict(row)  # 元のデータを保存
            }
        )
        
        return location
    
    def _load_coordinates_from_csv(self) -> dict[str, dict[str, Any]]:
        """CSVファイルから緯度経度情報を読み込む"""
        coordinates_data = {}
        
        try:
            with open(self.coordinates_csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    location_name = row.get("location_name", "").strip()
                    if location_name:
                        try:
                            coordinates_data[location_name] = {
                                "prefecture": row.get("prefecture", "").strip(),
                                "latitude": float(row.get("latitude", 0)),
                                "longitude": float(row.get("longitude", 0))
                            }
                        except (ValueError, TypeError) as e:
                            logger.warning(f"緯度経度の解析エラー ({location_name}): {e}")
                            continue
                
                logger.info(f"{len(coordinates_data)}件の緯度経度情報を読み込みました")
                
        except FileNotFoundError:
            logger.error(f"緯度経度CSVファイルが見つかりません: {self.coordinates_csv_path}")
        except Exception as e:
            logger.error(f"緯度経度CSV読み込みエラー: {e}")
        
        return coordinates_data
    
    def _get_location_coordinates(self, location_name: str) -> dict[str, Any | None]:
        """地点名から緯度経度情報を取得
        
        Args:
            location_name: 地点名
            
        Returns:
            緯度経度情報を含む辞書、見つからない場合はNone
        """
        # キャッシュされていない場合は読み込む
        if self._coordinates_cache is None:
            self._coordinates_cache = self._load_coordinates_from_csv()
            
            # CSVファイルが見つからない場合のフォールバック
            if not self._coordinates_cache:
                logger.warning("緯度経度CSVファイルが読み込めません。ハードコードされたデータを使用します")
                # 最小限のデータのみハードコード（フォールバック用）
                self._coordinates_cache = {
                    "東京": {"prefecture": "東京", "latitude": 35.6762, "longitude": 139.6503},
                    "大阪": {"prefecture": "大阪", "latitude": 34.6937, "longitude": 135.5023},
                    "名古屋": {"prefecture": "愛知", "latitude": 35.1815, "longitude": 136.9066},
                    "札幌": {"prefecture": "北海道", "latitude": 43.0642, "longitude": 141.3469},
                    "福岡": {"prefecture": "福岡", "latitude": 33.5904, "longitude": 130.4017},
                }
        
        return self._coordinates_cache.get(location_name)
    
    def _load_default_locations(self) -> list[Location]:
        """デフォルトの地点データを返す"""
        logger.info("デフォルトの地点データをロードしています...")
        
        # 基本的な地点データ
        default_data = [
            {"name": "東京", "prefecture": "東京", "latitude": 35.6762, "longitude": 139.6503},
            {"name": "大阪", "prefecture": "大阪", "latitude": 34.6937, "longitude": 135.5023},
            {"name": "名古屋", "prefecture": "愛知", "latitude": 35.1815, "longitude": 136.9066},
            {"name": "札幌", "prefecture": "北海道", "latitude": 43.0642, "longitude": 141.3469},
            {"name": "福岡", "prefecture": "福岡", "latitude": 33.5904, "longitude": 130.4017},
            {"name": "仙台", "prefecture": "宮城", "latitude": 38.2682, "longitude": 140.8694},
            {"name": "広島", "prefecture": "広島", "latitude": 34.3853, "longitude": 132.4553},
            {"name": "京都", "prefecture": "京都", "latitude": 35.0116, "longitude": 135.7681},
            {"name": "横浜", "prefecture": "神奈川", "latitude": 35.4437, "longitude": 139.6380},
            {"name": "神戸", "prefecture": "兵庫", "latitude": 34.6901, "longitude": 135.1955},
            {"name": "那覇", "prefecture": "沖縄", "latitude": 26.2124, "longitude": 127.6792},
            {"name": "金沢", "prefecture": "石川", "latitude": 36.5944, "longitude": 136.6256},
            {"name": "新潟", "prefecture": "新潟", "latitude": 37.9026, "longitude": 139.0238},
            {"name": "熊本", "prefecture": "熊本", "latitude": 32.7898, "longitude": 130.7417},
            {"name": "鹿児島", "prefecture": "鹿児島", "latitude": 31.5966, "longitude": 130.5571},
            {"name": "松山", "prefecture": "愛媛", "latitude": 33.8416, "longitude": 132.7657},
            {"name": "高松", "prefecture": "香川", "latitude": 34.3428, "longitude": 134.0434},
            {"name": "静岡", "prefecture": "静岡", "latitude": 34.9769, "longitude": 138.3831},
            {"name": "岡山", "prefecture": "岡山", "latitude": 34.6555, "longitude": 133.9195},
            {"name": "千葉", "prefecture": "千葉", "latitude": 35.6073, "longitude": 140.1063},
            {"name": "大津", "prefecture": "滋賀", "latitude": 35.0045, "longitude": 135.8686},
            {"name": "宇都宮", "prefecture": "栃木", "latitude": 36.5551, "longitude": 139.8828},
            {"name": "前橋", "prefecture": "群馬", "latitude": 36.3895, "longitude": 139.0634},
            {"name": "甲府", "prefecture": "山梨", "latitude": 35.6640, "longitude": 138.5685},
            {"name": "河口湖", "prefecture": "山梨", "latitude": 35.5103, "longitude": 138.7728},
            {"name": "長野", "prefecture": "長野", "latitude": 36.6485, "longitude": 138.1811},
            {"name": "岐阜", "prefecture": "岐阜", "latitude": 35.3912, "longitude": 136.7223},
            {"name": "津", "prefecture": "三重", "latitude": 34.7185, "longitude": 136.5056},
            {"name": "奈良", "prefecture": "奈良", "latitude": 34.6851, "longitude": 135.8048},
            {"name": "和歌山", "prefecture": "和歌山", "latitude": 34.2305, "longitude": 135.1708},
            {"name": "鳥取", "prefecture": "鳥取", "latitude": 35.5011, "longitude": 134.2351},
            {"name": "松江", "prefecture": "島根", "latitude": 35.4723, "longitude": 133.0505},
            {"name": "山口", "prefecture": "山口", "latitude": 34.1866, "longitude": 131.4705},
            {"name": "徳島", "prefecture": "徳島", "latitude": 34.0658, "longitude": 134.5594},
            {"name": "高知", "prefecture": "高知", "latitude": 33.5597, "longitude": 133.5311},
            {"name": "佐賀", "prefecture": "佐賀", "latitude": 33.2492, "longitude": 130.2988},
            {"name": "長崎", "prefecture": "長崎", "latitude": 32.7448, "longitude": 129.8737},
            {"name": "大分", "prefecture": "大分", "latitude": 33.2382, "longitude": 131.6126},
            {"name": "宮崎", "prefecture": "宮崎", "latitude": 31.9077, "longitude": 131.4202},
            {"name": "富山", "prefecture": "富山", "latitude": 36.6953, "longitude": 137.2113},
            {"name": "福井", "prefecture": "福井", "latitude": 36.0652, "longitude": 136.2216},
            {"name": "盛岡", "prefecture": "岩手", "latitude": 39.7036, "longitude": 141.1527},
            {"name": "青森", "prefecture": "青森", "latitude": 40.8246, "longitude": 140.7406},
            {"name": "秋田", "prefecture": "秋田", "latitude": 39.7186, "longitude": 140.1023},
            {"name": "山形", "prefecture": "山形", "latitude": 38.2405, "longitude": 140.3634},
            {"name": "福島", "prefecture": "福島", "latitude": 37.7608, "longitude": 140.4748},
            {"name": "水戸", "prefecture": "茨城", "latitude": 36.3418, "longitude": 140.4468},
            {"name": "さいたま", "prefecture": "埼玉", "latitude": 35.8570, "longitude": 139.6489},
        ]
        
        # Locationオブジェクトのリストを作成
        locations = []
        for data in default_data:
            location = Location(
                name=data["name"],
                normalized_name=data["name"],
                prefecture=data.get("prefecture"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude")
            )
            locations.append(location)
        
        return locations
"""地点データCSVローダー - CSVファイルから地点データを読み込む"""

import csv
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import Location

logger = logging.getLogger(__name__)


class LocationCSVLoader:
    """地点データCSVローダー"""
    
    def __init__(self, csv_path: Optional[str] = None):
        """初期化
        
        Args:
            csv_path: CSVファイルのパス。Noneの場合はデフォルトパスを使用
        """
        self.csv_path = csv_path or self._get_default_csv_path()
    
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
    
    def load_locations(self) -> List[Location]:
        """CSVファイルから地点データを読み込む
        
        Returns:
            読み込まれた地点データのリスト
        """
        locations = []
        
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
                            logger.warning(f"地点 '{location_name}' の座標情報が見つかりません")
                
                logger.info(f"{len(locations)}件の地点データを読み込みました")
                
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
    
    def _parse_location_row(self, row: Dict[str, str]) -> Optional[Location]:
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
    
    def _get_location_coordinates(self, location_name: str) -> Optional[Dict[str, Any]]:
        """地点名から緯度経度情報を取得
        
        Args:
            location_name: 地点名
            
        Returns:
            緯度経度情報を含む辞書、見つからない場合はNone
        """
        # 全142地点の緯度経度情報
        location_data = {
            # 北海道
            "稚内": {"prefecture": "北海道", "latitude": 45.4166, "longitude": 141.6728},
            "旭川": {"prefecture": "北海道", "latitude": 43.7706, "longitude": 142.3650},
            "留萌": {"prefecture": "北海道", "latitude": 43.9409, "longitude": 141.6370},
            "札幌": {"prefecture": "北海道", "latitude": 43.0642, "longitude": 141.3469},
            "岩見沢": {"prefecture": "北海道", "latitude": 43.2000, "longitude": 141.7600},
            "倶知安": {"prefecture": "北海道", "latitude": 42.9011, "longitude": 140.7594},
            "網走": {"prefecture": "北海道", "latitude": 44.0206, "longitude": 144.2734},
            "北見": {"prefecture": "北海道", "latitude": 43.8048, "longitude": 143.8909},
            "紋別": {"prefecture": "北海道", "latitude": 44.3558, "longitude": 143.3547},
            "根室": {"prefecture": "北海道", "latitude": 43.3306, "longitude": 145.5829},
            "釧路": {"prefecture": "北海道", "latitude": 42.9849, "longitude": 144.3816},
            "帯広": {"prefecture": "北海道", "latitude": 42.9237, "longitude": 143.1968},
            "室蘭": {"prefecture": "北海道", "latitude": 42.3153, "longitude": 140.9739},
            "浦河": {"prefecture": "北海道", "latitude": 42.1686, "longitude": 142.7680},
            "函館": {"prefecture": "北海道", "latitude": 41.7687, "longitude": 140.7289},
            "江差": {"prefecture": "北海道", "latitude": 41.8692, "longitude": 140.1275},
            # 東北
            "青森": {"prefecture": "青森", "latitude": 40.8246, "longitude": 140.7406},
            "むつ": {"prefecture": "青森", "latitude": 41.2924, "longitude": 141.1836},
            "八戸": {"prefecture": "青森", "latitude": 40.5122, "longitude": 141.4883},
            "盛岡": {"prefecture": "岩手", "latitude": 39.7036, "longitude": 141.1527},
            "宮古": {"prefecture": "岩手", "latitude": 39.6395, "longitude": 141.9480},
            "大船渡": {"prefecture": "岩手", "latitude": 39.0820, "longitude": 141.7090},
            "秋田": {"prefecture": "秋田", "latitude": 39.7186, "longitude": 140.1023},
            "横手": {"prefecture": "秋田", "latitude": 39.3138, "longitude": 140.5666},
            "仙台": {"prefecture": "宮城", "latitude": 38.2682, "longitude": 140.8694},
            "白石": {"prefecture": "宮城", "latitude": 38.0025, "longitude": 140.6199},
            "山形": {"prefecture": "山形", "latitude": 38.2405, "longitude": 140.3634},
            "米沢": {"prefecture": "山形", "latitude": 37.9189, "longitude": 140.1195},
            "酒田": {"prefecture": "山形", "latitude": 38.9116, "longitude": 139.8399},
            "新庄": {"prefecture": "山形", "latitude": 38.7620, "longitude": 140.3050},
            "福島": {"prefecture": "福島", "latitude": 37.7608, "longitude": 140.4748},
            "小名浜": {"prefecture": "福島", "latitude": 36.9500, "longitude": 140.9000},
            "若松": {"prefecture": "福島", "latitude": 37.4947, "longitude": 139.9098},
            # 北陸
            "新潟": {"prefecture": "新潟", "latitude": 37.9026, "longitude": 139.0238},
            "長岡": {"prefecture": "新潟", "latitude": 37.4464, "longitude": 138.8518},
            "高田": {"prefecture": "新潟", "latitude": 37.1046, "longitude": 138.2457},
            "相川": {"prefecture": "新潟", "latitude": 38.0283, "longitude": 138.2432},
            "金沢": {"prefecture": "石川", "latitude": 36.5944, "longitude": 136.6256},
            "輪島": {"prefecture": "石川", "latitude": 37.3907, "longitude": 136.8991},
            "富山": {"prefecture": "富山", "latitude": 36.6953, "longitude": 137.2113},
            "伏木": {"prefecture": "富山", "latitude": 36.7905, "longitude": 137.0553},
            "福井": {"prefecture": "福井", "latitude": 36.0652, "longitude": 136.2216},
            "敦賀": {"prefecture": "福井", "latitude": 35.6454, "longitude": 136.0553},
            # 関東
            "東京": {"prefecture": "東京", "latitude": 35.6762, "longitude": 139.6503},
            "大島": {"prefecture": "東京", "latitude": 34.7449, "longitude": 139.3600},
            "八丈島": {"prefecture": "東京", "latitude": 33.1097, "longitude": 139.7859},
            "父島": {"prefecture": "東京", "latitude": 27.0943, "longitude": 142.1918},
            "横浜": {"prefecture": "神奈川", "latitude": 35.4437, "longitude": 139.6380},
            "小田原": {"prefecture": "神奈川", "latitude": 35.2556, "longitude": 139.1545},
            "さいたま": {"prefecture": "埼玉", "latitude": 35.8570, "longitude": 139.6489},
            "熊谷": {"prefecture": "埼玉", "latitude": 36.1473, "longitude": 139.3886},
            "秩父": {"prefecture": "埼玉", "latitude": 35.9916, "longitude": 139.0824},
            "千葉": {"prefecture": "千葉", "latitude": 35.6073, "longitude": 140.1063},
            "銚子": {"prefecture": "千葉", "latitude": 35.7346, "longitude": 140.8569},
            "館山": {"prefecture": "千葉", "latitude": 34.9967, "longitude": 139.8700},
            "水戸": {"prefecture": "茨城", "latitude": 36.3418, "longitude": 140.4468},
            "土浦": {"prefecture": "茨城", "latitude": 36.0784, "longitude": 140.2016},
            "前橋": {"prefecture": "群馬", "latitude": 36.3895, "longitude": 139.0634},
            "みなかみ": {"prefecture": "群馬", "latitude": 36.7915, "longitude": 138.9993},
            "宇都宮": {"prefecture": "栃木", "latitude": 36.5551, "longitude": 139.8828},
            "大田原": {"prefecture": "栃木", "latitude": 36.8728, "longitude": 140.0156},
            # 甲信
            "長野": {"prefecture": "長野", "latitude": 36.6485, "longitude": 138.1811},
            "松本": {"prefecture": "長野", "latitude": 36.2381, "longitude": 137.9720},
            "飯田": {"prefecture": "長野", "latitude": 35.5147, "longitude": 137.8215},
            "甲府": {"prefecture": "山梨", "latitude": 35.6640, "longitude": 138.5685},
            "河口湖": {"prefecture": "山梨", "latitude": 35.5103, "longitude": 138.7728},
            # 東海
            "名古屋": {"prefecture": "愛知", "latitude": 35.1815, "longitude": 136.9066},
            "豊橋": {"prefecture": "愛知", "latitude": 34.7693, "longitude": 137.3915},
            "静岡": {"prefecture": "静岡", "latitude": 34.9769, "longitude": 138.3831},
            "網代": {"prefecture": "静岡", "latitude": 35.0459, "longitude": 139.0819},
            "三島": {"prefecture": "静岡", "latitude": 35.1183, "longitude": 138.9185},
            "浜松": {"prefecture": "静岡", "latitude": 34.7108, "longitude": 137.7261},
            "岐阜": {"prefecture": "岐阜", "latitude": 35.3912, "longitude": 136.7223},
            "高山": {"prefecture": "岐阜", "latitude": 36.1461, "longitude": 137.2521},
            "津": {"prefecture": "三重", "latitude": 34.7185, "longitude": 136.5056},
            "尾鷲": {"prefecture": "三重", "latitude": 34.0706, "longitude": 136.1902},
            # 近畿
            "大阪": {"prefecture": "大阪", "latitude": 34.6937, "longitude": 135.5023},
            "神戸": {"prefecture": "兵庫", "latitude": 34.6901, "longitude": 135.1955},
            "豊岡": {"prefecture": "兵庫", "latitude": 35.5446, "longitude": 134.8209},
            "京都": {"prefecture": "京都", "latitude": 35.0116, "longitude": 135.7681},
            "舞鶴": {"prefecture": "京都", "latitude": 35.4749, "longitude": 135.3860},
            "奈良": {"prefecture": "奈良", "latitude": 34.6851, "longitude": 135.8048},
            "風屋": {"prefecture": "奈良", "latitude": 34.0553, "longitude": 135.8607},
            "大津": {"prefecture": "滋賀", "latitude": 35.0045, "longitude": 135.8686},
            "彦根": {"prefecture": "滋賀", "latitude": 35.2745, "longitude": 136.2596},
            "和歌山": {"prefecture": "和歌山", "latitude": 34.2305, "longitude": 135.1708},
            "潮岬": {"prefecture": "和歌山", "latitude": 33.4500, "longitude": 135.7567},
            # 中国
            "広島": {"prefecture": "広島", "latitude": 34.3853, "longitude": 132.4553},
            "庄原": {"prefecture": "広島", "latitude": 34.8592, "longitude": 133.0167},
            "岡山": {"prefecture": "岡山", "latitude": 34.6555, "longitude": 133.9195},
            "津山": {"prefecture": "岡山", "latitude": 35.0703, "longitude": 134.0044},
            "下関": {"prefecture": "山口", "latitude": 33.9572, "longitude": 130.9408},
            "山口": {"prefecture": "山口", "latitude": 34.1866, "longitude": 131.4705},
            "柳井": {"prefecture": "山口", "latitude": 33.9641, "longitude": 132.1016},
            "萩": {"prefecture": "山口", "latitude": 34.4083, "longitude": 131.3991},
            "松江": {"prefecture": "島根", "latitude": 35.4723, "longitude": 133.0505},
            "浜田": {"prefecture": "島根", "latitude": 34.8996, "longitude": 132.0805},
            "西郷": {"prefecture": "島根", "latitude": 36.2064, "longitude": 133.3278},
            "鳥取": {"prefecture": "鳥取", "latitude": 35.5011, "longitude": 134.2351},
            "米子": {"prefecture": "鳥取", "latitude": 35.4283, "longitude": 133.3310},
            # 四国
            "松山": {"prefecture": "愛媛", "latitude": 33.8416, "longitude": 132.7657},
            "新居浜": {"prefecture": "愛媛", "latitude": 33.9604, "longitude": 133.2833},
            "宇和島": {"prefecture": "愛媛", "latitude": 33.2230, "longitude": 132.5612},
            "高松": {"prefecture": "香川", "latitude": 34.3428, "longitude": 134.0434},
            "徳島": {"prefecture": "徳島", "latitude": 34.0658, "longitude": 134.5594},
            "日和佐": {"prefecture": "徳島", "latitude": 33.7309, "longitude": 134.5305},
            "高知": {"prefecture": "高知", "latitude": 33.5597, "longitude": 133.5311},
            "室戸岬": {"prefecture": "高知", "latitude": 33.2652, "longitude": 134.1749},
            "清水": {"prefecture": "高知", "latitude": 32.7804, "longitude": 132.9554},
            # 九州
            "福岡": {"prefecture": "福岡", "latitude": 33.5904, "longitude": 130.4017},
            "八幡": {"prefecture": "福岡", "latitude": 33.8684, "longitude": 130.8114},
            "飯塚": {"prefecture": "福岡", "latitude": 33.6459, "longitude": 130.6917},
            "久留米": {"prefecture": "福岡", "latitude": 33.3192, "longitude": 130.5082},
            "佐賀": {"prefecture": "佐賀", "latitude": 33.2492, "longitude": 130.2988},
            "伊万里": {"prefecture": "佐賀", "latitude": 33.2711, "longitude": 129.8695},
            "長崎": {"prefecture": "長崎", "latitude": 32.7448, "longitude": 129.8737},
            "佐世保": {"prefecture": "長崎", "latitude": 33.1592, "longitude": 129.7228},
            "厳原": {"prefecture": "長崎", "latitude": 34.2017, "longitude": 129.2897},
            "福江": {"prefecture": "長崎", "latitude": 32.6957, "longitude": 128.8415},
            "大分": {"prefecture": "大分", "latitude": 33.2382, "longitude": 131.6126},
            "中津": {"prefecture": "大分", "latitude": 33.5980, "longitude": 131.1878},
            "日田": {"prefecture": "大分", "latitude": 33.3213, "longitude": 130.9409},
            "佐伯": {"prefecture": "大分", "latitude": 32.9593, "longitude": 131.9011},
            "熊本": {"prefecture": "熊本", "latitude": 32.7898, "longitude": 130.7417},
            "阿蘇乙姫": {"prefecture": "熊本", "latitude": 32.9522, "longitude": 131.0261},
            "牛深": {"prefecture": "熊本", "latitude": 32.1922, "longitude": 130.0271},
            "人吉": {"prefecture": "熊本", "latitude": 32.2143, "longitude": 130.7549},
            "宮崎": {"prefecture": "宮崎", "latitude": 31.9077, "longitude": 131.4202},
            "都城": {"prefecture": "宮崎", "latitude": 31.7280, "longitude": 131.0615},
            "延岡": {"prefecture": "宮崎", "latitude": 32.5818, "longitude": 131.6651},
            "高千穂": {"prefecture": "宮崎", "latitude": 32.7113, "longitude": 131.3086},
            "鹿児島": {"prefecture": "鹿児島", "latitude": 31.5966, "longitude": 130.5571},
            "鹿屋": {"prefecture": "鹿児島", "latitude": 31.3783, "longitude": 130.8502},
            "種子島": {"prefecture": "鹿児島", "latitude": 30.7314, "longitude": 131.0061},
            "名瀬": {"prefecture": "鹿児島", "latitude": 28.3774, "longitude": 129.4937},
            # 沖縄
            "那覇": {"prefecture": "沖縄", "latitude": 26.2124, "longitude": 127.6792},
            "名護": {"prefecture": "沖縄", "latitude": 26.5917, "longitude": 127.9772},
            "久米島": {"prefecture": "沖縄", "latitude": 26.3403, "longitude": 126.8047},
            "大東島": {"prefecture": "沖縄", "latitude": 25.8467, "longitude": 131.2328},
            "宮古島": {"prefecture": "沖縄", "latitude": 24.8053, "longitude": 125.2811},
            "石垣島": {"prefecture": "沖縄", "latitude": 24.3448, "longitude": 124.1572},
            "与那国島": {"prefecture": "沖縄", "latitude": 24.4675, "longitude": 122.9928},
        }
        
        return location_data.get(location_name)
    
    def _load_default_locations(self) -> List[Location]:
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
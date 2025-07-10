"""地点データモデル - Locationデータクラスの定義"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from math import radians, sin, cos, sqrt, atan2


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
            推定された都道府県名、推定できない場合はNone
        """
        name_lower = self.name.lower()

        # 都道府県名のパターン
        prefectures = {
            # 北海道・東北
            "北海道": ["札幌", "函館", "旭川", "釧路", "帯広", "北見", "岩見沢", "網走", "留萌", "稚内"],
            "青森": ["青森", "八戸", "弘前", "むつ"],
            "岩手": ["盛岡", "一関", "奥州", "花巻"],
            "宮城": ["仙台", "石巻", "名取", "多賀城"],
            "秋田": ["秋田", "横手", "大仙", "由利本荘"],
            "山形": ["山形", "鶴岡", "酒田", "米沢"],
            "福島": ["福島", "郡山", "いわき", "会津若松"],
            # 関東
            "茨城": ["水戸", "つくば", "土浦", "日立", "ひたちなか"],
            "栃木": ["宇都宮", "小山", "足利", "栃木", "佐野", "大田原"],
            "群馬": ["前橋", "高崎", "伊勢崎", "太田", "桐生", "渋川", "みなかみ"],
            "埼玉": ["さいたま", "川越", "熊谷", "川口", "所沢", "春日部", "秩父"],
            "千葉": ["千葉", "船橋", "市川", "松戸", "柏", "市原", "銚子", "館山"],
            "東京": ["東京", "新宿", "渋谷", "品川", "世田谷", "練馬", "八王子", "父島", "大島", "八丈島"],
            "神奈川": ["横浜", "川崎", "相模原", "横須賀", "藤沢", "小田原"],
            # 中部
            "新潟": ["新潟", "長岡", "上越", "三条", "燕"],
            "富山": ["富山", "高岡", "射水", "魚津"],
            "石川": ["金沢", "小松", "白山", "加賀"],
            "福井": ["福井", "敦賀", "小浜", "坂井"],
            "山梨": ["甲府", "富士吉田", "笛吹", "南アルプス", "河口湖"],
            "長野": ["長野", "松本", "上田", "飯田", "諏訪"],
            "岐阜": ["岐阜", "大垣", "各務原", "多治見", "高山"],
            "静岡": ["静岡", "浜松", "沼津", "熱海", "富士", "清水", "網代"],
            "愛知": ["名古屋", "豊橋", "一宮", "豊田", "岡崎"],
            # 近畿
            "三重": ["津", "四日市", "伊勢", "松阪", "鈴鹿", "尾鷲"],
            "滋賀": ["大津", "草津", "長浜", "東近江", "彦根"],
            "京都": ["京都", "宇治", "亀岡", "舞鶴", "福知山"],
            "大阪": ["大阪", "堺", "枚方", "東大阪", "豊中"],
            "兵庫": ["神戸", "姫路", "西宮", "尼崎", "明石", "豊岡"],
            "奈良": ["奈良", "橿原", "生駒", "大和郡山", "風屋"],
            "和歌山": ["和歌山", "田辺", "新宮", "海南", "潮岬", "日和佐"],
            # 中国・四国
            "鳥取": ["鳥取", "米子", "倉吉", "境港"],
            "島根": ["松江", "出雲", "浜田", "益田"],
            "岡山": ["岡山", "倉敷", "津山", "総社"],
            "広島": ["広島", "福山", "呉", "尾道"],
            "山口": ["山口", "下関", "宇部", "周南"],
            "徳島": ["徳島", "鳴門", "阿南", "吉野川"],
            "香川": ["高松", "丸亀", "坂出", "観音寺"],
            "愛媛": ["松山", "今治", "新居浜", "西条", "宇和島"],
            "高知": ["高知", "南国", "四万十", "室戸岬"],
            # 九州・沖縄
            "福岡": ["福岡", "北九州", "久留米", "飯塚"],
            "佐賀": ["佐賀", "唐津", "鳥栖", "伊万里"],
            "長崎": ["長崎", "佐世保", "諫早", "大村"],
            "熊本": ["熊本", "八代", "天草", "荒尾"],
            "大分": ["大分", "別府", "中津", "日田"],
            "宮崎": ["宮崎", "都城", "延岡", "日向"],
            "鹿児島": ["鹿児島", "霧島", "鹿屋", "指宿"],
            "沖縄": ["那覇", "沖縄", "うるま", "浦添", "宜野湾", "名護", "石垣島", "宮古島", "久米島", "与那国島", "大東島"],
        }

        # 都道府県名を含む場合
        for pref, cities in prefectures.items():
            if pref in name_lower:
                return pref

        # 市町村名から推定
        for pref, cities in prefectures.items():
            for city in cities:
                if city in name_lower:
                    return pref

        return None

    def _infer_region(self) -> Optional[str]:
        """都道府県名から地方区分を推定

        Returns:
            地方区分名、推定できない場合はNone
        """
        if not self.prefecture:
            return None

        # 地方区分の定義
        regions = {
            "北海道・東北": ["北海道", "青森", "岩手", "宮城", "秋田", "山形", "福島"],
            "関東": ["茨城", "栃木", "群馬", "埼玉", "千葉", "東京", "神奈川"],
            "中部": ["新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜", "静岡", "愛知"],
            "近畿": ["三重", "滋賀", "京都", "大阪", "兵庫", "奈良", "和歌山"],
            "中国": ["鳥取", "島根", "岡山", "広島", "山口"],
            "四国": ["徳島", "香川", "愛媛", "高知"],
            "九州": ["福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島"],
            "沖縄": ["沖縄"],
        }

        for region, prefs in regions.items():
            if self.prefecture in prefs:
                return region

        return None

    def distance_to(self, other: "Location") -> Optional[float]:
        """他の地点との距離を計算（km）

        Args:
            other: 距離を計算する対象の地点

        Returns:
            距離（km）、座標が不明な場合はNone
        """
        if not all([self.latitude, self.longitude, other.latitude, other.longitude]):
            return None

        # Haversine公式による距離計算
        R = 6371  # 地球の半径（km）

        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def matches_query(self, query: str, fuzzy: bool = True) -> bool:
        """クエリとのマッチング判定

        Args:
            query: 検索クエリ
            fuzzy: 曖昧検索を有効にするか

        Returns:
            マッチするかどうか
        """
        if not query:
            return False

        query = query.strip().lower()
        name_lower = self.name.lower()
        normalized_lower = self.normalized_name.lower()

        # 完全一致
        if query == name_lower or query == normalized_lower:
            return True

        # 部分一致
        if query in name_lower or query in normalized_lower:
            return True

        # 都道府県名でのマッチング
        if self.prefecture and query in self.prefecture.lower():
            return True

        # 曖昧検索
        if fuzzy:
            # レーベンシュタイン距離による曖昧マッチング
            max_distance = max(1, len(query) // 3)  # クエリ長の1/3までの誤差を許容
            if self._levenshtein_distance(query, name_lower) <= max_distance:
                return True
            if self._levenshtein_distance(query, normalized_lower) <= max_distance:
                return True

        return False

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """レーベンシュタイン距離（編集距離）を計算

        Args:
            s1: 文字列1
            s2: 文字列2

        Returns:
            編集距離
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # 文字が同じ場合はコスト0、異なる場合はコスト1
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            地点データの辞書表現
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
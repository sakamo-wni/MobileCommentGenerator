"""
地点関連のユーティリティ関数

地点の順序管理、フィルタリング、読み込みなど
"""

from typing import List
from pathlib import Path
import pandas as pd
import streamlit as st


def get_location_order() -> List[str]:
    """
    地点の表示順序を定義した配列を返す
    
    Returns:
        地点名の順序リスト
    """
    return [
        # 北海道
        "稚内", "旭川", "留萌",
        "札幌", "岩見沢", "倶知安",
        "網走", "北見", "紋別", "根室", "釧路", "帯広",
        "室蘭", "浦河", "函館", "江差",
        
        # 東北
        "青森", "むつ", "八戸",
        "盛岡", "宮古", "大船渡",
        "秋田", "横手",
        "仙台", "白石",
        "山形", "米沢", "酒田", "新庄",
        "福島", "小名浜", "若松",
        
        # 北陸
        "新潟", "長岡", "高田", "相川",
        "金沢", "輪島",
        "富山", "伏木",
        "福井", "敦賀",
        
        # 関東
        "東京", "大島", "八丈島", "父島",
        "横浜", "小田原",
        "さいたま", "熊谷", "秩父",
        "千葉", "銚子", "館山",
        "水戸", "土浦",
        "前橋", "みなかみ",
        "宇都宮", "大田原",
        
        # 甲信
        "長野", "松本", "飯田",
        "甲府", "河口湖",
        
        # 東海
        "名古屋", "豊橋",
        "静岡", "網代", "三島", "浜松",
        "岐阜", "高山",
        "津", "尾鷲",
        
        # 近畿
        "大阪",
        "神戸", "豊岡",
        "京都", "舞鶴",
        "奈良", "風屋",
        "大津", "彦根",
        "和歌山", "潮岬",
        
        # 中国
        "広島", "庄原",
        "岡山", "津山",
        "下関", "山口", "柳井", "萩",
        "松江", "浜田", "西郷",
        "鳥取", "米子",
        
        # 四国
        "松山", "新居浜", "宇和島",
        "高松",
        "徳島", "日和佐",
        "高知", "室戸岬", "清水",
        
        # 九州
        "福岡", "八幡", "飯塚", "久留米",
        "佐賀", "伊万里",
        "長崎", "佐世保", "厳原", "福江",
        "大分", "中津", "日田", "佐伯",
        "熊本", "阿蘇乙姫", "牛深", "人吉",
        "宮崎", "都城", "延岡", "高千穂",
        "鹿児島", "鹿屋", "種子島", "名瀬",
        
        # 沖縄
        "那覇", "名護", "久米島", "大東島", "宮古島", "石垣島", "与那国島"
    ]


def sort_locations_by_order(locations: List[str]) -> List[str]:
    """
    地点リストを指定された順序でソートする
    
    Args:
        locations: ソートする地点名のリスト
    
    Returns:
        ソートされた地点名のリスト
    """
    # 地点順序を取得
    order = get_location_order()
    
    # 順序辞書を作成（地点名 -> インデックス）
    order_dict = {loc: i for i, loc in enumerate(order)}
    
    # 順序に基づいてソート（未定義の地点は最後に）
    return sorted(
        locations, 
        key=lambda x: order_dict.get(x, len(order))
    )


def load_locations() -> List[str]:
    """
    地点データを読み込む
    
    Returns:
        地点名のリスト
    """
    # キャッシュがある場合は使用
    if 'locations' in st.session_state:
        return st.session_state.locations
    
    # CSVファイルパスを構築
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    csv_path = data_dir / "locations.csv"
    
    try:
        # S3からの地点データがある場合は優先的に使用
        from src.data.location_manager import get_location_manager
        
        location_manager = get_location_manager()
        locations = [loc.name for loc in location_manager.get_all_locations()]
        
        if locations:
            # 地点順序でソート
            locations = sort_locations_by_order(locations)
            # セッションステートにキャッシュ
            st.session_state.locations = locations
            return locations
            
    except Exception as e:
        st.warning(f"地点管理システムからの読み込みに失敗: {str(e)}")
    
    # フォールバック: CSVファイルから読み込み
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path, header=None, names=['location'])
            locations = df['location'].unique().tolist()
            
            # 地点順序でソート
            locations = sort_locations_by_order(locations)
            
            # セッションステートにキャッシュ
            st.session_state.locations = locations
            return locations
        except Exception as e:
            st.error(f"CSVファイルの読み込みエラー: {str(e)}")
    
    # デフォルトの地点リストを返す
    default_locations = get_location_order()
    st.session_state.locations = default_locations
    return default_locations


def filter_locations(locations: List[str], query: str) -> List[str]:
    """
    クエリに基づいて地点をフィルタリング
    
    Args:
        locations: 地点リスト
        query: 検索クエリ
        
    Returns:
        フィルタリングされた地点リスト
    """
    if not query:
        return locations
        
    query_lower = query.lower()
    
    # 完全一致、前方一致、部分一致の順で検索
    exact_matches = [loc for loc in locations if loc.lower() == query_lower]
    prefix_matches = [loc for loc in locations if loc.lower().startswith(query_lower) and loc not in exact_matches]
    partial_matches = [loc for loc in locations if query_lower in loc.lower() and loc not in exact_matches and loc not in prefix_matches]
    
    return exact_matches + prefix_matches + partial_matches
"""地点選択コンポーネント"""

from __future__ import annotations
import streamlit as st
from typing import Any
from src.ui.streamlit_utils import load_locations, filter_locations, sort_locations_by_order
from src.config.app_config import get_config

# 地域別地点データ
REGIONS: dict[str, list[str]] = {
    "北海道": [
        "稚内", "旭川", "留萌",
        "札幌", "岩見沢", "倶知安", 
        "網走", "北見", "紋別", "根室", "釧路", "帯広",
        "室蘭", "浦河", "函館", "江差"
    ],
    "東北": [
        "青森", "むつ", "八戸",
        "盛岡", "宮古", "大船渡",
        "秋田", "横手",
        "仙台", "白石",
        "山形", "米沢", "酒田", "新庄",
        "福島", "小名浜", "若松"
    ],
    "北陸": [
        "新潟", "長岡", "高田", "相川",
        "金沢", "輪島",
        "富山", "伏木",
        "福井", "敦賀"
    ],
    "関東": [
        "東京", "大島", "八丈島", "父島",
        "横浜", "小田原",
        "さいたま", "熊谷", "秩父",
        "千葉", "銚子", "館山",
        "水戸", "土浦",
        "前橋", "みなかみ",
        "宇都宮", "大田原"
    ],
    "甲信": [
        "長野", "松本", "飯田",
        "甲府", "河口湖"
    ],
    "東海": [
        "名古屋", "豊橋",
        "静岡", "網代", "三島", "浜松",
        "岐阜", "高山",
        "津", "尾鷲"
    ],
    "近畿": [
        "大阪",
        "神戸", "豊岡",
        "京都", "舞鶴",
        "奈良", "風屋",
        "大津", "彦根",
        "和歌山", "潮岬"
    ],
    "中国": [
        "広島", "庄原",
        "岡山", "津山",
        "下関", "山口", "柳井", "萩",
        "松江", "浜田", "西郷",
        "鳥取", "米子"
    ],
    "四国": [
        "松山", "新居浜", "宇和島",
        "高松",
        "徳島", "日和佐",
        "高知", "室戸岬", "清水"
    ],
    "九州": [
        "福岡", "八幡", "飯塚", "久留米",
        "大分", "中津", "日田",
        "長崎", "佐世保", "厳原", "福江",
        "佐賀", "伊万里",
        "熊本", "阿蘇乙姫", "牛深",
        "宮崎", "延岡", "都城", "高千穂",
        "鹿児島", "鹿屋", "種子島", "名瀬", "沖永良部"
    ],
    "沖縄": [
        "那覇", "名護", "久米島",
        "宮古島", "石垣島", "与那国島", "大東島"
    ]
}

DEFAULT_FAVORITES = ["東京", "大阪", "札幌", "福岡", "那覇"]
PRESET_GROUPS = {
    "主要都市": ["東京", "大阪", "名古屋", "札幌", "福岡", "横浜", "神戸", "京都", "仙台", "広島"],
    "県庁所在地（東日本）": ["札幌", "青森", "盛岡", "仙台", "秋田", "山形", "福島", "東京", "横浜", "さいたま", "千葉", "水戸", "前橋", "宇都宮", "長野", "新潟", "金沢", "富山", "福井", "甲府"],
    "県庁所在地（西日本）": ["名古屋", "岐阜", "静岡", "津", "大阪", "神戸", "京都", "大津", "奈良", "和歌山", "鳥取", "松江", "岡山", "広島", "山口", "徳島", "高松", "松山", "高知", "福岡", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島", "那覇"],
    "日本海側": ["稚内", "留萌", "札幌", "秋田", "酒田", "新潟", "金沢", "福井", "敦賀", "舞鶴", "豊岡", "鳥取", "松江", "浜田", "下関", "福岡"],
    "太平洋側": ["釧路", "浦河", "八戸", "宮古", "仙台", "小名浜", "東京", "横浜", "静岡", "浜松", "名古屋", "津", "尾鷲", "和歌山", "潮岬", "高知", "室戸岬", "宮崎", "鹿児島"],
    "離島": ["大島", "八丈島", "父島", "種子島", "名瀬", "沖永良部", "久米島", "宮古島", "石垣島", "与那国島", "大東島"]
}


def location_selector() -> list[str]:
    """
    地点選択コンポーネント（複数選択対応）

    Returns:
        選択された地点名のリスト
    """
    config = get_config()
    
    # 地点データの読み込み
    locations = load_locations()

    # 検索機能
    search_query = st.text_input(
        "🔍 地点名で検索",
        key="location_search",
        placeholder="例: 東京、大阪、札幌...",
        help="地点名の一部を入力して検索できます",
    )

    # フィルタリング
    if search_query:
        filtered_locations = filter_locations(locations, search_query)
    else:
        filtered_locations = locations

    # よく使う地点（セッション状態から）
    if "favorite_locations" not in st.session_state:
        st.session_state.favorite_locations = DEFAULT_FAVORITES

    # お気に入り地点の表示
    if st.checkbox("⭐ よく使う地点のみ表示"):
        filtered_locations = [
            loc for loc in filtered_locations if loc in st.session_state.favorite_locations
        ]

    # 地域選択オプション
    region_filter = st.selectbox(
        "🗾 地域で絞り込み",
        ["全国"] + list(REGIONS.keys()),
        key="region_filter"
    )

    if region_filter != "全国":
        region_locations = REGIONS.get(region_filter, [])
        filtered_locations = [loc for loc in filtered_locations if loc in region_locations]

    # プリセットグループ
    preset_group = st.selectbox(
        "📋 プリセットグループ",
        ["カスタム選択"] + list(PRESET_GROUPS.keys()),
        key="preset_group"
    )

    if preset_group != "カスタム選択":
        preset_locations = PRESET_GROUPS[preset_group]
        # プリセットと現在のフィルターの積集合
        filtered_locations = [loc for loc in preset_locations if loc in filtered_locations]

    # クイック選択ボタン
    st.write("**クイック選択:**")
    col1, col2, col3 = st.columns(3)
    
    quick_select_all = col1.button("全て選択", use_container_width=True)
    quick_select_none = col2.button("全て解除", use_container_width=True)
    quick_select_favorites = col3.button("お気に入りを選択", use_container_width=True)

    # 選択地点数の表示と制限警告
    if filtered_locations:
        max_locations = config.ui_settings.max_locations_per_generation
        if len(filtered_locations) > max_locations:
            st.warning(f"⚠️ 一度に生成できる地点数は最大{max_locations}地点です。")

    # 複数選択UI
    if quick_select_all:
        default_selection = filtered_locations[:config.ui_settings.max_locations_per_generation]
    elif quick_select_none:
        default_selection = []
    elif quick_select_favorites:
        default_selection = [loc for loc in st.session_state.favorite_locations if loc in filtered_locations]
    else:
        # セッション状態から選択を復元
        if "last_selected_locations" in st.session_state:
            default_selection = [loc for loc in st.session_state.last_selected_locations if loc in filtered_locations]
        else:
            default_selection = []

    # ソート（よく使う地点を上に）
    sorted_locations = sort_locations_by_order(filtered_locations)

    selected_locations = st.multiselect(
        "📍 地点を選択",
        sorted_locations,
        default=default_selection,
        key="location_multiselect",
        help=f"最大{config.ui_settings.max_locations_per_generation}地点まで選択可能です"
    )

    # 選択した地点を保存
    st.session_state.last_selected_locations = selected_locations

    # 選択地点数の表示
    if selected_locations:
        st.success(f"✅ {len(selected_locations)}地点を選択中")
        
        # お気に入りに追加オプション
        if st.checkbox("選択した地点をお気に入りに追加"):
            for loc in selected_locations:
                if loc not in st.session_state.favorite_locations:
                    st.session_state.favorite_locations.append(loc)
            st.rerun()
    else:
        st.info("👆 生成する地点を選択してください")

    return selected_locations
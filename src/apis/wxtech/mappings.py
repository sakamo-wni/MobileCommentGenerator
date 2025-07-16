"""
WxTech API 天気コードマッピング

天気コードと風向きの変換定義を管理
"""

from __future__ import annotations
from src.data.weather_data import WeatherCondition, WindDirection


def convert_weather_code(weather_code: str) -> WeatherCondition:
    """WxTech天気コードを標準的な天気状況に変換
    
    Args:
        weather_code: WxTech API の天気コード
        
    Returns:
        標準化された天気状況
    """
    # WxTech APIの天気コードマッピング（完全版）
    code_mapping = {
        # 晴れ系
        "100": WeatherCondition.CLEAR,
        "101": WeatherCondition.PARTLY_CLOUDY,  # 晴れ時々くもり
        "102": WeatherCondition.RAIN,           # 晴れ一時雨
        "103": WeatherCondition.RAIN,           # 晴れ時々雨
        "104": WeatherCondition.SNOW,           # 晴れ一時雪
        "105": WeatherCondition.SNOW,           # 晴れ時々雪
        "110": WeatherCondition.PARTLY_CLOUDY,
        "111": WeatherCondition.CLOUDY,         # 晴れのちくもり
        "112": WeatherCondition.RAIN,           # 晴れのち一時雨
        "113": WeatherCondition.RAIN,           # 晴れのち時々雨
        "114": WeatherCondition.RAIN,           # 晴れのち雨
        "115": WeatherCondition.SNOW,           # 晴れのち一時雪
        "116": WeatherCondition.SNOW,           # 晴れのち時々雪
        "117": WeatherCondition.SNOW,           # 晴れのち雪
        "119": WeatherCondition.THUNDER,        # 晴れのち雨か雷雨
        "123": WeatherCondition.THUNDER,        # 晴れ山沿い雷雨
        "125": WeatherCondition.THUNDER,        # 晴れ午後は雷雨
        "126": WeatherCondition.RAIN,           # 晴れ昼頃から雨
        "127": WeatherCondition.RAIN,           # 晴れ夕方から雨
        "128": WeatherCondition.RAIN,           # 晴れ夜は雨
        "129": WeatherCondition.RAIN,           # 晴れ夜半から雨
        "130": WeatherCondition.FOG,            # 朝の内霧のち晴れ
        "131": WeatherCondition.FOG,            # 晴れ朝方霧
        "132": WeatherCondition.PARTLY_CLOUDY,  # 晴れ時々くもり
        "140": WeatherCondition.RAIN,           # 晴れ時々雨
        
        # 曇り系
        "200": WeatherCondition.CLOUDY,
        "201": WeatherCondition.PARTLY_CLOUDY,  # くもり時々晴れ
        "202": WeatherCondition.RAIN,           # くもり一時雨
        "203": WeatherCondition.RAIN,           # くもり時々雨
        "204": WeatherCondition.SNOW,           # くもり一時雪
        "205": WeatherCondition.SNOW,           # くもり時々雪
        "208": WeatherCondition.THUNDER,        # くもり一時雨か雷雨
        "209": WeatherCondition.FOG,            # 霧
        "210": WeatherCondition.PARTLY_CLOUDY,  # くもりのち時々晴れ
        "211": WeatherCondition.CLEAR,          # くもりのち晴れ
        "212": WeatherCondition.RAIN,           # くもりのち一時雨
        "213": WeatherCondition.RAIN,           # くもりのち時々雨
        "214": WeatherCondition.RAIN,           # くもりのち雨
        "219": WeatherCondition.THUNDER,        # くもりのち雨か雷雨
        "224": WeatherCondition.RAIN,           # くもり昼頃から雨
        "225": WeatherCondition.RAIN,           # くもり夕方から雨
        "226": WeatherCondition.RAIN,           # くもり夜は雨
        "227": WeatherCondition.RAIN,           # くもり夜半から雨
        "231": WeatherCondition.FOG,            # くもり海上海岸は霧か霧雨
        "240": WeatherCondition.THUNDER,        # くもり時々雨で雷を伴う
        "250": WeatherCondition.THUNDER,        # くもり時々雪で雷を伴う
        
        # 雨系
        "300": WeatherCondition.RAIN,
        "301": WeatherCondition.RAIN,           # 雨時々晴れ
        "302": WeatherCondition.RAIN,           # 雨時々止む
        "303": WeatherCondition.RAIN,           # 雨時々雪
        "306": WeatherCondition.HEAVY_RAIN,     # 大雨
        "308": WeatherCondition.SEVERE_STORM,   # 雨で暴風を伴う
        "309": WeatherCondition.RAIN,           # 雨一時雪
        "311": WeatherCondition.RAIN,           # 雨のち晴れ
        "313": WeatherCondition.RAIN,           # 雨のちくもり
        "314": WeatherCondition.RAIN,           # 雨のち時々雪
        "315": WeatherCondition.RAIN,           # 雨のち雪
        "320": WeatherCondition.RAIN,           # 朝の内雨のち晴れ
        "321": WeatherCondition.RAIN,           # 朝の内雨のちくもり
        "323": WeatherCondition.RAIN,           # 雨昼頃から晴れ
        "324": WeatherCondition.RAIN,           # 雨夕方から晴れ
        "325": WeatherCondition.RAIN,           # 雨夜は晴れ
        "328": WeatherCondition.HEAVY_RAIN,     # 雨一時強く降る
        
        # 雪系
        "400": WeatherCondition.SNOW,
        "401": WeatherCondition.SNOW,           # 雪時々晴れ
        "402": WeatherCondition.SNOW,           # 雪時々止む
        "403": WeatherCondition.SNOW,           # 雪時々雨
        "405": WeatherCondition.HEAVY_SNOW,     # 大雪
        "406": WeatherCondition.SEVERE_STORM,   # 風雪強い
        "407": WeatherCondition.SEVERE_STORM,   # 暴風雪
        "409": WeatherCondition.SNOW,           # 雪一時雨
        "411": WeatherCondition.SNOW,           # 雪のち晴れ
        "413": WeatherCondition.SNOW,           # 雪のちくもり
        "414": WeatherCondition.SNOW,           # 雪のち雨
        "420": WeatherCondition.SNOW,           # 朝の内雪のち晴れ
        "421": WeatherCondition.SNOW,           # 朝の内雪のちくもり
        "422": WeatherCondition.SNOW,           # 雪昼頃から雨
        "423": WeatherCondition.SNOW,           # 雪夕方から雨
        "424": WeatherCondition.SNOW,           # 雪夜半から雨
        "425": WeatherCondition.HEAVY_SNOW,     # 雪一時強く降る
        "450": WeatherCondition.THUNDER,        # 雪で雷を伴う
        
        # 特殊系
        "350": WeatherCondition.THUNDER,        # 雷
        "500": WeatherCondition.CLEAR,          # 快晴
        "550": WeatherCondition.EXTREME_HEAT,   # 猛暑
        "552": WeatherCondition.EXTREME_HEAT,   # 猛暑時々曇り
        "553": WeatherCondition.EXTREME_HEAT,   # 猛暑時々雨
        "558": WeatherCondition.SEVERE_STORM,   # 猛暑時々大雨・嵐
        "562": WeatherCondition.EXTREME_HEAT,   # 猛暑のち曇り
        "563": WeatherCondition.EXTREME_HEAT,   # 猛暑のち雨
        "568": WeatherCondition.SEVERE_STORM,   # 猛暑のち大雨・嵐
        "572": WeatherCondition.EXTREME_HEAT,   # 曇り時々猛暑
        "573": WeatherCondition.EXTREME_HEAT,   # 雨時々猛暑
        "582": WeatherCondition.EXTREME_HEAT,   # 曇りのち猛暑
        "583": WeatherCondition.EXTREME_HEAT,   # 雨のち猛暑
        "600": WeatherCondition.CLOUDY,         # うすぐもり
        "650": WeatherCondition.RAIN,           # 小雨
        "800": WeatherCondition.THUNDER,        # 雷
        "850": WeatherCondition.SEVERE_STORM,   # 大雨・嵐
        "851": WeatherCondition.SEVERE_STORM,   # 大雨・嵐時々晴れ
        "852": WeatherCondition.SEVERE_STORM,   # 大雨・嵐時々曇り
        "853": WeatherCondition.SEVERE_STORM,   # 大雨・嵐時々雨
        "854": WeatherCondition.SEVERE_STORM,   # 大雨・嵐時々雪
        "855": WeatherCondition.SEVERE_STORM,   # 大雨・嵐時々猛暑
        "859": WeatherCondition.SEVERE_STORM,   # 大雨・嵐のち曇り
        "860": WeatherCondition.SEVERE_STORM,   # 大雨・嵐のち雪
        "861": WeatherCondition.SEVERE_STORM,   # 大雨・嵐のち雨
        "862": WeatherCondition.SEVERE_STORM,   # 大雨・嵐のち雪
        "863": WeatherCondition.SEVERE_STORM,   # 大雨・嵐のち猛暑
    }
    
    return code_mapping.get(weather_code, WeatherCondition.UNKNOWN)


def get_weather_description(weather_code: str) -> str:
    """天気コードから日本語説明を取得
    
    特殊気象条件（雷、霧）を含む完全版マッピング
    
    Args:
        weather_code: WxTech API の天気コード
        
    Returns:
        日本語の天気説明
    """
    # 完全な天気コードマッピング
    descriptions = {
        "100": "晴れ",
        "101": "晴れ時々くもり",
        "102": "晴れ一時雨",
        "103": "晴れ時々雨",
        "104": "晴れ一時雪",
        "105": "晴れ時々雪",
        "106": "晴れ一時雨か雪",
        "107": "晴れ時々雨か雪",
        "108": "晴れ一時雨",
        "110": "晴れのち時々くもり",
        "111": "晴れのちくもり",
        "112": "晴れのち一時雨",
        "113": "晴れのち時々雨",
        "114": "晴れのち雨",
        "115": "晴れのち一時雪",
        "116": "晴れのち時々雪",
        "117": "晴れのち雪",
        "118": "晴れのち雨か雪",
        "119": "晴れのち雨か雷雨",
        "120": "晴れ一時雨",
        "121": "晴れ一時雨",
        "122": "晴れ夕方一時雨",
        "123": "晴れ山沿い雷雨",
        "124": "晴れ山沿い雪",
        "125": "晴れ午後は雷雨",
        "126": "晴れ昼頃から雨",
        "127": "晴れ夕方から雨",
        "128": "晴れ夜は雨",
        "129": "晴れ夜半から雨",
        "130": "朝の内霧のち晴れ",
        "131": "晴れ朝方霧",
        "132": "晴れ時々くもり",
        "140": "晴れ時々雨",
        "160": "晴れ一時雪か雨",
        "170": "晴れ時々雪か雨",
        "181": "晴れのち雪か雨",
        "200": "くもり",
        "201": "くもり時々晴れ",
        "202": "くもり一時雨",
        "203": "くもり時々雨",
        "204": "くもり一時雪",
        "205": "くもり時々雪",
        "206": "くもり一時雨か雪",
        "207": "くもり時々雨か雪",
        "208": "くもり一時雨か雷雨",
        "209": "霧",
        "210": "くもりのち時々晴れ",
        "211": "くもりのち晴れ",
        "212": "くもりのち一時雨",
        "213": "くもりのち時々雨",
        "214": "くもりのち雨",
        "215": "くもりのち一時雪",
        "216": "くもりのち時々雪",
        "217": "くもりのち雪",
        "218": "くもりのち雨か雪",
        "219": "くもりのち雨か雷雨",
        "220": "くもり朝夕一時雨",
        "221": "くもり朝の内一時雨",
        "222": "くもり夕方一時雨",
        "223": "くもり日中時々晴れ",
        "224": "くもり昼頃から雨",
        "225": "くもり夕方から雨",
        "226": "くもり夜は雨",
        "227": "くもり夜半から雨",
        "228": "くもり昼頃から雪",
        "229": "くもり夕方から雪",
        "230": "くもり夜は雪",
        "231": "くもり海上海岸は霧か霧雨",
        "240": "くもり時々雨で雷を伴う",
        "250": "くもり時々雪で雷を伴う",
        "260": "くもり一時雪か雨",
        "270": "くもり時々雪か雨",
        "281": "くもりのち雪か雨",
        "300": "雨",
        "301": "雨時々晴れ",
        "302": "雨時々止む",
        "303": "雨時々雪",
        "304": "雨か雪",
        "306": "大雨",
        "308": "雨で暴風を伴う",
        "309": "雨一時雪",
        "311": "雨のち晴れ",
        "313": "雨のちくもり",
        "314": "雨のち時々雪",
        "315": "雨のち雪",
        "316": "雨か雪のち晴れ",
        "317": "雨か雪のちくもり",
        "320": "朝の内雨のち晴れ",
        "321": "朝の内雨のちくもり",
        "322": "雨朝晩一時雪",
        "323": "雨昼頃から晴れ",
        "324": "雨夕方から晴れ",
        "325": "雨夜は晴れ",
        "326": "雨夕方から雪",
        "327": "雨夜は雪",
        "328": "雨一時強く降る",
        "329": "雨一時みぞれ",
        "340": "雪か雨",
        "350": "雷",
        "361": "雪か雨のち晴れ",
        "371": "雪か雨のちくもり",
        "400": "雪",
        "401": "雪時々晴れ",
        "402": "雪時々止む",
        "403": "雪時々雨",
        "405": "大雪",
        "406": "風雪強い",
        "407": "暴風雪",
        "409": "雪一時雨",
        "411": "雪のち晴れ",
        "413": "雪のちくもり",
        "414": "雪のち雨",
        "420": "朝の内雪のち晴れ",
        "421": "朝の内雪のちくもり",
        "422": "雪昼頃から雨",
        "423": "雪夕方から雨",
        "424": "雪夜半から雨",
        "425": "雪一時強く降る",
        "426": "雪のちみぞれ",
        "427": "雪一時みぞれ",
        "430": "みぞれ",
        "450": "雪で雷を伴う",
        "500": "快晴",
        "550": "猛暑",
        "552": "猛暑時々曇り",
        "553": "猛暑時々雨",
        "558": "猛暑時々大雨・嵐",
        "562": "猛暑のち曇り",
        "563": "猛暑のち雨",
        "568": "猛暑のち大雨・嵐",
        "572": "曇り時々猛暑",
        "573": "雨時々猛暑",
        "582": "曇りのち猛暑",
        "583": "雨のち猛暑",
        "600": "うすぐもり",
        "650": "小雨",
        "800": "雷",
        "850": "大雨・嵐",
        "851": "大雨・嵐時々晴れ",
        "852": "大雨・嵐時々曇り",
        "853": "大雨・嵐時々雨",
        "854": "大雨・嵐時々雪",
        "855": "大雨・嵐時々猛暑",
        "859": "大雨・嵐のち曇り",
        "860": "大雨・嵐のち雪",
        "861": "大雨・嵐のち雨",
        "862": "大雨・嵐のち雪",
        "863": "大雨・嵐のち猛暑",
    }
    
    return descriptions.get(weather_code, "不明")


def convert_wind_direction(wind_dir_index: int) -> tuple[WindDirection, int]:
    """風向きインデックスを風向きと度数に変換
    
    Args:
        wind_dir_index: WxTech API の風向きインデックス
        
    Returns:
        (風向き, 度数) のタプル
    """
    direction_mapping = {
        0: (WindDirection.CALM, 0),
        1: (WindDirection.N, 0),
        2: (WindDirection.NE, 45),
        3: (WindDirection.E, 90),
        4: (WindDirection.SE, 135),
        5: (WindDirection.S, 180),
        6: (WindDirection.SW, 225),
        7: (WindDirection.W, 270),
        8: (WindDirection.NW, 315),
    }
    
    return direction_mapping.get(wind_dir_index, (WindDirection.UNKNOWN, 0))
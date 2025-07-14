#!/usr/bin/env python3
"""地点検索の警告を修正するスクリプト"""

import pandas as pd
from pathlib import Path

def check_location_data():
    """地点データを確認"""
    # 地点データファイルのパス
    csv_files = [
        "src/data/Chiten.csv",
        "src/data/location_coordinates.csv",
        "frontend/public/地点名.csv"
    ]
    
    target_lat = 36.238
    target_lon = 137.972
    tolerance = 0.1  # 許容誤差
    
    print(f"目標座標: lat={target_lat}, lon={target_lon}")
    print("=" * 50)
    
    for csv_file in csv_files:
        if Path(csv_file).exists():
            print(f"\n{csv_file} を確認中...")
            try:
                # CSVを読み込み
                df = pd.read_csv(csv_file, encoding='utf-8')
                print(f"カラム: {df.columns.tolist()}")
                print(f"データ数: {len(df)}")
                
                # 緯度経度のカラムを探す
                lat_cols = [col for col in df.columns if 'lat' in col.lower() or '緯度' in col]
                lon_cols = [col for col in df.columns if 'lon' in col.lower() or '経度' in col]
                
                if lat_cols and lon_cols:
                    lat_col = lat_cols[0]
                    lon_col = lon_cols[0]
                    
                    # 近い地点を探す
                    df['distance'] = ((df[lat_col] - target_lat)**2 + (df[lon_col] - target_lon)**2)**0.5
                    nearby = df[df['distance'] < tolerance].sort_values('distance')
                    
                    if not nearby.empty:
                        print(f"\n近い地点が見つかりました:")
                        print(nearby.head())
                    else:
                        print(f"\n最も近い地点:")
                        print(df.nsmallest(5, 'distance'))
                        
            except Exception as e:
                print(f"エラー: {e}")
        else:
            print(f"\n{csv_file} が存在しません")

def suggest_fix():
    """修正方法を提案"""
    print("\n\n修正方法の提案:")
    print("1. 地点データに該当座標の地点を追加")
    print("2. 地点検索のキャッシュを実装")
    print("3. バリデーション処理でのログ出力を最適化")
    print("\n推奨される即時対応:")
    print("- ログレベルをWARNINGからDEBUGに変更")
    print("- 同じ座標の検索結果をキャッシュ")

if __name__ == "__main__":
    check_location_data()
    suggest_fix()
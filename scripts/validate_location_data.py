#!/usr/bin/env python3
"""地点データの検証スクリプト"""

import os
import csv
import sys

# 期待される地点数
EXPECTED_COUNT = 142

def find_file(paths: list[str]) -> str | None:
    """ファイルパスを探す"""
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def load_csv_locations(file_path: str) -> list[str] | None:
    """CSVファイルから地点名を読み込む"""
    if not file_path:
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return [row.get('location_name', row.get('地点名', '')) 
                   for row in reader if row]
    except Exception as e:
        print(f"エラー: {file_path} の読み込みに失敗: {e}")
        return None

def main():
    """メイン処理"""
    # Chiten.csvのパスを探す
    chiten_paths = ['src/data/Chiten.csv', 'data/Chiten.csv', 'Chiten.csv']
    chiten_path = find_file(chiten_paths)
    
    # location_coordinates.csvのパスを探す
    csv_paths = ['src/data/location_coordinates.csv', 'data/location_coordinates.csv', 
                 'location_coordinates.csv']
    csv_path = find_file(csv_paths)
    
    # ファイル存在確認
    if chiten_path:
        print(f"✓ Chiten.csv が見つかりました: {chiten_path}")
    else:
        print("✗ Chiten.csv が見つかりません")
    
    if csv_path:
        print(f"✓ location_coordinates.csv が見つかりました: {csv_path}")
    else:
        print("✗ location_coordinates.csv が見つかりません")
    
    # データ読み込み
    chiten_locations = load_csv_locations(chiten_path) if chiten_path else None
    csv_locations = load_csv_locations(csv_path) if csv_path else None
    
    # 検証結果
    validation_passed = True
    
    if chiten_locations and len(chiten_locations) != EXPECTED_COUNT:
        print(f"❌ 検証失敗: Chiten.csvに {len(chiten_locations)} 地点、期待値は {EXPECTED_COUNT}")
        validation_passed = False
    
    if csv_locations and len(csv_locations) != EXPECTED_COUNT:
        print(f"❌ 検証失敗: location_coordinates.csvに {len(csv_locations)} 地点、期待値は {EXPECTED_COUNT}")
        validation_passed = False
    
    if validation_passed and (chiten_locations or csv_locations):
        print("✅ 検証成功: 地点データが正しく設定されています")
    elif not chiten_locations and not csv_locations:
        print("⚠️ 警告: 地点データファイルが見つかりません")
    
    # 終了コード
    sys.exit(0 if validation_passed else 1)

if __name__ == '__main__':
    main()
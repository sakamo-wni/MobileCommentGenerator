#!/usr/bin/env python3
"""location_coordinates.csvから余分な地点を削除するスクリプト"""

import csv

# 削除する地点のリスト
EXTRA_LOCATIONS = {
    "一関", "三重", "二戸", "古川", "呉", "姫路", "御前崎", "枕崎",
    "気仙沼", "池田", "油津", "洲本", "深浦", "白河", "相馬", "石巻",
    "福山", "苫小牧", "諏訪", "軽井沢", "阿久根"
}

def clean_csv():
    input_file = "src/data/location_coordinates.csv"
    output_file = "src/data/location_coordinates_clean.csv"
    
    kept_rows = []
    removed_rows = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            if row['location_name'] in EXTRA_LOCATIONS:
                removed_rows.append(row)
            else:
                kept_rows.append(row)
    
    # 新しいファイルに書き込み
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept_rows)
    
    print(f"削除された地点数: {len(removed_rows)}")
    print(f"残った地点数: {len(kept_rows)}")
    print(f"削除された地点: {[row['location_name'] for row in removed_rows]}")
    
    # 元のファイルを置き換え
    import shutil
    shutil.move(output_file, input_file)
    print(f"\n{input_file} を更新しました")

if __name__ == "__main__":
    clean_csv()
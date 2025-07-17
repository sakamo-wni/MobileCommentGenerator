#!/usr/bin/env python3
"""地域リストの表示テスト"""

from src.ui.components.location_selector import REGIONS

print("REGIONS辞書の内容:")
print("=" * 50)

for i, (region, locations) in enumerate(REGIONS.items()):
    print(f"{i + 1}. {region}: {len(locations)}地点")
    
print("\n" + "=" * 50)
print(f"総地域数: {len(REGIONS)}")

# 辞書のキーの順序を確認
print("\nキーの順序:")
print(list(REGIONS.keys()))

# 特定の地域が含まれているか確認
missing_regions = []
for region in ["中国", "九州", "沖縄"]:
    if region in REGIONS:
        print(f"\n✓ '{region}'地域は存在します（{len(REGIONS[region])}地点）")
    else:
        print(f"\n✗ '{region}'地域が見つかりません！")
        missing_regions.append(region)

if missing_regions:
    print(f"\n警告: 以下の地域が見つかりません: {missing_regions}")
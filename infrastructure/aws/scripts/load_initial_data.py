"""
DynamoDB初期データロードスクリプト

地点情報とその他の初期データをDynamoDBにロード
"""

import json
import boto3
import csv
from pathlib import Path
from typing import Dict, List, Any

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')


def load_locations_data(table_name: str, csv_path: Path) -> None:
    """地点データをDynamoDBにロード"""
    table = dynamodb.Table(table_name)
    
    print(f"Loading locations from {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        with table.batch_writer() as batch:
            for idx, row in enumerate(reader):
                # 地点IDの生成（地域_地点名）
                location_id = f"{row['region']}_{row['location']}"
                
                item = {
                    'location_id': location_id,
                    'location_name': row['location'],
                    'coordinates': {
                        'lat': float(row['latitude']),
                        'lon': float(row['longitude'])
                    },
                    'region': row['region'],
                    'access_count': 0,
                    'popular_rank': idx + 1,  # 初期は順番通り
                    'metadata': {
                        'timezone': 'Asia/Tokyo',
                        'elevation': float(row.get('elevation', 0))
                    }
                }
                
                batch.put_item(Item=item)
    
    print(f"✅ Loaded {idx + 1} locations")


def create_popular_locations_list(table_name: str) -> List[Dict[str, Any]]:
    """人気地点リストを作成"""
    # 主要都市のリスト
    popular_cities = [
        "東京", "大阪", "名古屋", "札幌", "福岡", 
        "仙台", "広島", "京都", "横浜", "神戸",
        "新潟", "静岡", "那覇", "金沢", "高松"
    ]
    
    table = dynamodb.Table(table_name)
    popular_locations = []
    
    for rank, city in enumerate(popular_cities, 1):
        # 地点を検索
        response = table.scan(
            FilterExpression='contains(location_name, :city)',
            ExpressionAttributeValues={':city': city}
        )
        
        if response['Items']:
            location = response['Items'][0]
            # 人気ランクを更新
            table.update_item(
                Key={'location_id': location['location_id']},
                UpdateExpression='SET popular_rank = :rank, access_count = :count',
                ExpressionAttributeValues={
                    ':rank': rank,
                    ':count': 1000 - (rank * 50)  # 仮の初期アクセス数
                }
            )
            
            popular_locations.append({
                'name': location['location_name'],
                'latitude': location['coordinates']['lat'],
                'longitude': location['coordinates']['lon'],
                'priority': 10 - (rank // 2),
                'access_count': 1000 - (rank * 50)
            })
    
    return popular_locations


def save_popular_locations_json(locations: List[Dict[str, Any]], output_path: Path) -> None:
    """人気地点リストをJSONファイルに保存"""
    data = {
        'updated_at': boto3.datetime.datetime.now().isoformat(),
        'locations': locations
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved popular locations to {output_path}")


def initialize_sample_comments(table_name: str) -> None:
    """サンプルコメントデータを投入"""
    table = dynamodb.Table(table_name)
    
    sample_comments = [
        {
            'location_id': '関東_東京',
            'generated_at': '2024-01-01T09:00:00',
            'comment_id': 'sample-001',
            'location_name': '東京',
            'weather_data': {
                'temperature': 10.5,
                'weather_condition': '晴れ',
                'precipitation': 0
            },
            'generated_comment': '今日の東京は晴れて過ごしやすい一日となりそうです。',
            'advice_comment': '日中は暖かくなりますが、朝晩は冷えるので調整できる服装がおすすめです。',
            'llm_provider': 'gemini',
            'generation_metadata': {
                'model': 'gemini-pro',
                'execution_time_ms': 1200
            },
            'comment_date': '2024-01-01',
            'ttl': 9999999999  # 削除されないように遠い未来
        }
    ]
    
    with table.batch_writer() as batch:
        for comment in sample_comments:
            batch.put_item(Item=comment)
    
    print(f"✅ Loaded {len(sample_comments)} sample comments")


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load initial data to DynamoDB')
    parser.add_argument('--stack-name', required=True, help='CloudFormation stack name')
    parser.add_argument('--locations-csv', required=True, help='Path to locations CSV file')
    parser.add_argument('--output-dir', default='./output', help='Output directory for generated files')
    
    args = parser.parse_args()
    
    # CloudFormationから出力を取得
    cf = boto3.client('cloudformation', region_name='ap-northeast-1')
    response = cf.describe_stacks(StackName=args.stack_name)
    
    outputs = {}
    for output in response['Stacks'][0]['Outputs']:
        outputs[output['OutputKey']] = output['OutputValue']
    
    # テーブル名を取得
    locations_table = outputs.get('LocationsTableName') or f"{args.stack_name}-locations"
    comments_table = outputs.get('CommentsTableName') or f"{args.stack_name}-comments"
    
    print(f"🚀 Loading initial data to stack: {args.stack_name}")
    print(f"   Locations table: {locations_table}")
    print(f"   Comments table: {comments_table}")
    
    # 地点データをロード
    locations_csv = Path(args.locations_csv)
    if locations_csv.exists():
        load_locations_data(locations_table, locations_csv)
    else:
        print(f"❌ Locations CSV not found: {locations_csv}")
        return
    
    # 人気地点リストを作成
    popular_locations = create_popular_locations_list(locations_table)
    
    # 出力ディレクトリを作成
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 人気地点リストを保存
    save_popular_locations_json(
        popular_locations, 
        output_dir / 'popular_locations.json'
    )
    
    # サンプルコメントを投入
    initialize_sample_comments(comments_table)
    
    print("\n✅ Initial data loading completed!")
    print(f"\n📁 Generated files:")
    print(f"   - {output_dir / 'popular_locations.json'}")
    print(f"\n💡 Upload popular_locations.json to S3 for cache warmer to use")


if __name__ == '__main__':
    main()
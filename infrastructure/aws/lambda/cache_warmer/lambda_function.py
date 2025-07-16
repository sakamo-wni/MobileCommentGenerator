"""
AWS Lambda Cache Warmer

人気地点の天気データを定期的に取得してキャッシュを事前に温める
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Any, List, Optional
import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# AWS Lambda Powertools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# AWS Resources
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Environment variables
WEATHER_FETCHER_FUNCTION = os.environ['WEATHER_FETCHER_FUNCTION']
LOCATIONS_TABLE = os.environ['DYNAMODB_LOCATIONS_TABLE']
POPULAR_LOCATIONS_BUCKET = os.environ.get('POPULAR_LOCATIONS_BUCKET', '')
POPULAR_LOCATIONS_KEY = os.environ.get('POPULAR_LOCATIONS_KEY', 'config/popular_locations.json')

# DynamoDB table
locations_table = dynamodb.Table(LOCATIONS_TABLE)


@tracer.capture_method
def get_popular_locations(limit: int = 20) -> List[Dict[str, Any]]:
    """人気地点のリストを取得"""
    try:
        # S3から人気地点リストを取得（存在する場合）
        if POPULAR_LOCATIONS_BUCKET:
            try:
                response = s3.get_object(
                    Bucket=POPULAR_LOCATIONS_BUCKET,
                    Key=POPULAR_LOCATIONS_KEY
                )
                data = json.loads(response['Body'].read())
                locations = data.get('locations', [])
                if locations:
                    logger.info(f"Loaded {len(locations)} popular locations from S3")
                    return locations[:limit]
            except Exception as e:
                logger.warning(f"Failed to load from S3: {str(e)}")
        
        # DynamoDBから人気順で取得
        response = locations_table.scan(
            ProjectionExpression='location_id,location_name,coordinates,popular_rank,access_count',
            Limit=100
        )
        
        items = response.get('Items', [])
        
        # popular_rankまたはaccess_countでソート
        sorted_items = sorted(
            items,
            key=lambda x: (x.get('popular_rank', 999), -x.get('access_count', 0))
        )
        
        logger.info(f"Found {len(sorted_items)} locations from DynamoDB")
        return sorted_items[:limit]
        
    except Exception as e:
        logger.error(f"Failed to get popular locations: {str(e)}")
        return []


@tracer.capture_method
def invoke_weather_fetcher(location_id: str) -> Optional[Dict[str, Any]]:
    """Weather Fetcher Lambda関数を呼び出し"""
    try:
        payload = {
            'location_id': location_id,
            'use_spatial_cache': False  # 必ず新しいデータを取得
        }
        
        response = lambda_client.invoke(
            FunctionName=WEATHER_FETCHER_FUNCTION,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        if response['StatusCode'] == 200:
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                logger.info(f"Successfully fetched weather for {location_id}")
                metrics.add_metric(name="WeatherFetchSuccess", unit=MetricUnit.Count, value=1)
                return result
            else:
                logger.error(f"Weather fetch failed for {location_id}: {result}")
                metrics.add_metric(name="WeatherFetchError", unit=MetricUnit.Count, value=1)
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to invoke weather fetcher for {location_id}: {str(e)}")
        metrics.add_metric(name="InvokeError", unit=MetricUnit.Count, value=1)
        return None


@tracer.capture_method
def warm_cache_parallel(locations: List[Dict[str, Any]], max_workers: int = 10) -> Dict[str, Any]:
    """並列で複数地点のキャッシュを温める"""
    results = {
        'success': 0,
        'failed': 0,
        'total': len(locations),
        'details': []
    }
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 各地点に対してweather fetcherを呼び出し
        future_to_location = {
            executor.submit(invoke_weather_fetcher, loc['location_id']): loc
            for loc in locations
        }
        
        for future in as_completed(future_to_location):
            location = future_to_location[future]
            location_id = location['location_id']
            
            try:
                result = future.result()
                if result:
                    results['success'] += 1
                    results['details'].append({
                        'location_id': location_id,
                        'status': 'success'
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'location_id': location_id,
                        'status': 'failed'
                    })
            except Exception as e:
                logger.error(f"Error processing {location_id}: {str(e)}")
                results['failed'] += 1
                results['details'].append({
                    'location_id': location_id,
                    'status': 'error',
                    'error': str(e)
                })
    
    return results


@tracer.capture_method
def update_location_metrics(results: Dict[str, Any]) -> None:
    """地点の統計情報を更新"""
    try:
        # 成功した地点のcache_warmed_atを更新
        for detail in results['details']:
            if detail['status'] == 'success':
                locations_table.update_item(
                    Key={'location_id': detail['location_id']},
                    UpdateExpression='SET cache_warmed_at = :now',
                    ExpressionAttributeValues={
                        ':now': datetime.utcnow().isoformat()
                    }
                )
    except Exception as e:
        logger.error(f"Failed to update location metrics: {str(e)}")


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    キャッシュウォーマーLambda
    
    トリガー:
    - EventBridge (定期実行)
    - Manual invoke
    
    パラメータ:
    - max_locations: 最大取得地点数 (default: 20)
    - max_workers: 並列実行数 (default: 10)
    """
    
    try:
        # パラメータ取得
        max_locations = event.get('max_locations', 20)
        max_workers = event.get('max_workers', 10)
        
        logger.info(f"Starting cache warmer: max_locations={max_locations}, max_workers={max_workers}")
        
        # 人気地点を取得
        popular_locations = get_popular_locations(limit=max_locations)
        
        if not popular_locations:
            logger.warning("No popular locations found")
            return {
                'statusCode': 200,
                'message': 'No locations to warm',
                'warmed_count': 0
            }
        
        # キャッシュを温める
        start_time = datetime.utcnow()
        results = warm_cache_parallel(popular_locations, max_workers=max_workers)
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 統計情報を更新
        update_location_metrics(results)
        
        # メトリクスを記録
        metrics.add_metric(name="LocationsWarmed", unit=MetricUnit.Count, value=results['success'])
        metrics.add_metric(name="WarmingExecutionTime", unit=MetricUnit.Seconds, value=execution_time)
        
        logger.info(f"Cache warming completed: {results['success']}/{results['total']} locations in {execution_time:.2f}s")
        
        return {
            'statusCode': 200,
            'message': 'Cache warming completed',
            'warmed_count': results['success'],
            'failed_count': results['failed'],
            'total_count': results['total'],
            'execution_time_seconds': execution_time,
            'details': results.get('details', [])
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        metrics.add_metric(name="Errors", unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 500,
            'error': 'Internal server error'
        }
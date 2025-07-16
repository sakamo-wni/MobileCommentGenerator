"""
AWS Lambda Weather Fetcher

天気APIからデータを取得し、DynamoDBにキャッシュ
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import boto3
import httpx
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# AWS Lambda Powertools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# AWS Resources
dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')

# Environment variables
WEATHER_CACHE_TABLE = os.environ['DYNAMODB_WEATHER_CACHE_TABLE']
LOCATIONS_TABLE = os.environ['DYNAMODB_LOCATIONS_TABLE']
SECRETS_ARN = os.environ['SECRETS_ARN']

# DynamoDB tables
weather_cache_table = dynamodb.Table(WEATHER_CACHE_TABLE)
locations_table = dynamodb.Table(LOCATIONS_TABLE)


def geohash_encode(lat: float, lon: float, precision: int = 5) -> str:
    """簡易的なGeohashエンコード"""
    # 実際の実装では python-geohash ライブラリを使用
    return hashlib.md5(f"{lat:.{precision}f},{lon:.{precision}f}".encode()).hexdigest()[:precision]


@tracer.capture_method
def get_weather_api_key() -> str:
    """Secrets ManagerからWeather APIキーを取得"""
    try:
        response = secrets_manager.get_secret_value(SecretId=SECRETS_ARN)
        secrets = json.loads(response['SecretString'])
        return secrets['WXTECH_API_KEY']
    except Exception as e:
        logger.error(f"Failed to retrieve API key: {str(e)}")
        raise


@tracer.capture_method
def get_location_info(location_id: str) -> Optional[Dict[str, Any]]:
    """位置情報を取得"""
    try:
        response = locations_table.get_item(Key={'location_id': location_id})
        if 'Item' in response:
            # アクセスカウントを更新
            locations_table.update_item(
                Key={'location_id': location_id},
                UpdateExpression='SET access_count = access_count + :inc, last_accessed = :now',
                ExpressionAttributeValues={
                    ':inc': 1,
                    ':now': datetime.utcnow().isoformat()
                }
            )
            return response['Item']
        return None
    except Exception as e:
        logger.error(f"Failed to get location info: {str(e)}")
        return None


@tracer.capture_method
async def fetch_weather_data(lat: float, lon: float, api_key: str) -> Dict[str, Any]:
    """Weather APIから天気データを取得"""
    try:
        url = f"https://wxtech.weathernews.com/api/v1/ss1wxpro/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'lang': 'ja',
            'product': 'forecast'
        }
        headers = {
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'MobileCommentGenerator-Lambda/1.0'
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
        data = response.json()
        metrics.add_metric(name="WeatherAPISuccess", unit=MetricUnit.Count, value=1)
        return data
        
    except httpx.TimeoutException:
        logger.error("Weather API timeout")
        metrics.add_metric(name="WeatherAPITimeout", unit=MetricUnit.Count, value=1)
        raise
    except Exception as e:
        logger.error(f"Weather API error: {str(e)}")
        metrics.add_metric(name="WeatherAPIError", unit=MetricUnit.Count, value=1)
        raise


@tracer.capture_method
def save_to_cache(location_id: str, location_info: Dict[str, Any], weather_data: Dict[str, Any]) -> None:
    """天気データをDynamoDBにキャッシュ"""
    try:
        # 予報データを時系列で保存
        forecasts = weather_data.get('forecasts', [])
        geohash = geohash_encode(
            location_info['coordinates']['lat'],
            location_info['coordinates']['lon']
        )
        
        with weather_cache_table.batch_writer() as batch:
            for forecast in forecasts:
                item = {
                    'location_id': location_id,
                    'forecast_time': forecast['datetime'],
                    'cached_at': datetime.utcnow().isoformat(),
                    'weather_data': forecast,
                    'geohash': geohash,
                    'ttl': int((datetime.utcnow() + timedelta(hours=6)).timestamp())  # 6時間後に削除
                }
                batch.put_item(Item=item)
        
        logger.info(f"Cached {len(forecasts)} forecasts for {location_id}")
        metrics.add_metric(name="ForecastsCached", unit=MetricUnit.Count, value=len(forecasts))
        
    except Exception as e:
        logger.error(f"Failed to cache weather data: {str(e)}")
        raise


@tracer.capture_method
def check_spatial_cache(lat: float, lon: float, max_distance_km: float = 10.0) -> Optional[Dict[str, Any]]:
    """近隣地点のキャッシュを確認"""
    try:
        # Geohashで近隣を検索
        geohash = geohash_encode(lat, lon, precision=4)  # 粗い精度で検索
        
        response = weather_cache_table.query(
            IndexName='GeohashIndex',
            KeyConditionExpression='geohash = :gh AND forecast_time > :now',
            ExpressionAttributeValues={
                ':gh': geohash,
                ':now': datetime.utcnow().isoformat()
            },
            Limit=10
        )
        
        if response['Items']:
            # 最も近い地点のデータを返す
            logger.info(f"Spatial cache hit: {len(response['Items'])} items")
            metrics.add_metric(name="SpatialCacheHits", unit=MetricUnit.Count, value=1)
            return response['Items'][0]
        
        metrics.add_metric(name="SpatialCacheMisses", unit=MetricUnit.Count, value=1)
        return None
        
    except Exception as e:
        logger.error(f"Spatial cache error: {str(e)}")
        return None


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    天気データ取得Lambda
    
    トリガー:
    - Step Functions
    - EventBridge (定期実行)
    - Direct invoke
    """
    
    try:
        # リクエストパラメータ
        location_id = event.get('location_id')
        use_spatial_cache = event.get('use_spatial_cache', True)
        
        if not location_id:
            raise ValueError("location_id is required")
        
        # 位置情報取得
        location_info = get_location_info(location_id)
        if not location_info:
            raise ValueError(f"Location not found: {location_id}")
        
        lat = location_info['coordinates']['lat']
        lon = location_info['coordinates']['lon']
        
        # 空間キャッシュチェック
        if use_spatial_cache:
            cached_data = check_spatial_cache(lat, lon)
            if cached_data:
                return {
                    'statusCode': 200,
                    'location_id': location_id,
                    'weather_data': cached_data['weather_data'],
                    'cached': True,
                    'cache_type': 'spatial'
                }
        
        # APIキー取得
        api_key = get_weather_api_key()
        
        # 天気データ取得
        import asyncio
        weather_data = asyncio.run(fetch_weather_data(lat, lon, api_key))
        
        # キャッシュに保存
        save_to_cache(location_id, location_info, weather_data)
        
        return {
            'statusCode': 200,
            'location_id': location_id,
            'weather_data': weather_data,
            'cached': False
        }
        
    except ValueError as e:
        return {
            'statusCode': 400,
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        metrics.add_metric(name="Errors", unit=MetricUnit.Count, value=1)
        return {
            'statusCode': 500,
            'error': 'Internal server error'
        }
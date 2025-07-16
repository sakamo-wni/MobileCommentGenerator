"""
AWS Lambda Comment Processor

SQSキューからメッセージを受信し、
天気コメントを生成してDynamoDBに保存
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

# プロジェクトルートをパスに追加
sys.path.insert(0, '/opt/python')

# AWS Lambda Powertools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# AWS Resources
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
secrets_manager = boto3.client('secretsmanager')

# Environment variables
COMMENTS_TABLE = os.environ['DYNAMODB_COMMENTS_TABLE']
WEATHER_CACHE_TABLE = os.environ['DYNAMODB_WEATHER_CACHE_TABLE']
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
SECRETS_ARN = os.environ['SECRETS_ARN']

# DynamoDB tables
comments_table = dynamodb.Table(COMMENTS_TABLE)
weather_cache_table = dynamodb.Table(WEATHER_CACHE_TABLE)


@tracer.capture_method
def get_api_keys() -> Dict[str, str]:
    """Secrets Managerから APIキーを取得"""
    try:
        response = secrets_manager.get_secret_value(SecretId=SECRETS_ARN)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Failed to retrieve secrets: {str(e)}")
        raise


@tracer.capture_method
def get_weather_from_cache(location_id: str) -> Dict[str, Any]:
    """キャッシュから天気データを取得"""
    try:
        # 現在時刻から12時間先までのデータを取得
        current_time = datetime.utcnow()
        forecast_time = current_time + timedelta(hours=12)
        
        response = weather_cache_table.query(
            KeyConditionExpression='location_id = :location AND forecast_time <= :time',
            ExpressionAttributeValues={
                ':location': location_id,
                ':time': forecast_time.isoformat()
            },
            Limit=1
        )
        
        if response['Items']:
            logger.info(f"Weather cache hit for {location_id}")
            metrics.add_metric(name="WeatherCacheHits", unit=MetricUnit.Count, value=1)
            return response['Items'][0]['weather_data']
        
        logger.info(f"Weather cache miss for {location_id}")
        metrics.add_metric(name="WeatherCacheMisses", unit=MetricUnit.Count, value=1)
        return None
        
    except Exception as e:
        logger.error(f"Error accessing weather cache: {str(e)}")
        return None


@tracer.capture_method
def generate_comment(location: str, weather_data: Dict[str, Any], llm_provider: str) -> Dict[str, Any]:
    """コメントを生成"""
    try:
        # Import at runtime to reduce cold start
        from src.workflows.comment_generation_workflow import run_comment_generation
        
        # APIキーを環境変数に設定
        api_keys = get_api_keys()
        os.environ.update(api_keys)
        
        # コメント生成実行
        result = run_comment_generation(
            location_name=location,
            llm_provider=llm_provider,
            pre_fetched_weather={'weather_data': weather_data} if weather_data else None
        )
        
        metrics.add_metric(name="CommentsGenerated", unit=MetricUnit.Count, value=1)
        metrics.add_metric(name=f"CommentsBy{llm_provider.title()}", unit=MetricUnit.Count, value=1)
        
        return result
        
    except Exception as e:
        logger.error(f"Comment generation failed: {str(e)}")
        metrics.add_metric(name="CommentGenerationErrors", unit=MetricUnit.Count, value=1)
        raise


@tracer.capture_method
def save_to_dynamodb(request_id: str, location: str, result: Dict[str, Any]) -> None:
    """生成結果をDynamoDBに保存"""
    try:
        item = {
            'location_id': location,
            'generated_at': datetime.utcnow().isoformat(),
            'comment_id': request_id,
            'location_name': location,
            'weather_data': result.get('weather_data', {}),
            'generated_comment': result.get('final_comment', ''),
            'advice_comment': result.get('advice_comment', ''),
            'llm_provider': result.get('generation_metadata', {}).get('llm_provider', 'unknown'),
            'generation_metadata': result.get('generation_metadata', {}),
            'ttl': int((datetime.utcnow() + timedelta(days=7)).timestamp())  # 7日後に自動削除
        }
        
        comments_table.put_item(Item=item)
        logger.info(f"Saved comment to DynamoDB: {request_id}")
        
    except Exception as e:
        logger.error(f"Failed to save to DynamoDB: {str(e)}")
        raise


@tracer.capture_method
def send_notification(request_id: str, location: str, status: str, result: Dict[str, Any] = None) -> None:
    """SNSで完了通知を送信"""
    if not SNS_TOPIC_ARN:
        return
    
    try:
        message = {
            'request_id': request_id,
            'location': location,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if status == 'completed' and result:
            message['comment'] = result.get('final_comment', '')
            message['advice'] = result.get('advice_comment', '')
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message),
            MessageAttributes={
                'status': {'DataType': 'String', 'StringValue': status},
                'location': {'DataType': 'String', 'StringValue': location}
            }
        )
        
        logger.info(f"Notification sent for {request_id}")
        
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    SQSイベントを処理してコメントを生成
    """
    
    batch_item_failures = []
    
    for record in event.get('Records', []):
        try:
            # SQSメッセージを解析
            message = json.loads(record['body'])
            request_id = message['request_id']
            location = message['location']
            llm_provider = message.get('llm_provider', 'gemini')
            use_cache = message.get('use_cache', True)
            
            logger.info(f"Processing request: {request_id} for {location}")
            
            # 天気データ取得（キャッシュ優先）
            weather_data = None
            if use_cache:
                weather_data = get_weather_from_cache(location)
            
            # コメント生成
            start_time = datetime.utcnow()
            result = generate_comment(location, weather_data, llm_provider)
            
            # 生成時間を記録
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            metrics.add_metric(name="GenerationTime", unit=MetricUnit.Seconds, value=generation_time)
            
            # DynamoDBに保存
            save_to_dynamodb(request_id, location, result)
            
            # 完了通知
            send_notification(request_id, location, 'completed', result)
            
            logger.info(f"Successfully processed: {request_id}")
            
        except Exception as e:
            logger.error(f"Failed to process record: {str(e)}", exc_info=True)
            
            # 失敗通知
            if 'message' in locals():
                send_notification(
                    message.get('request_id', 'unknown'),
                    message.get('location', 'unknown'),
                    'failed'
                )
            
            # バッチアイテム失敗として記録
            batch_item_failures.append({
                'itemIdentifier': record['messageId']
            })
    
    # 部分的なバッチ失敗をレポート
    return {
        'batchItemFailures': batch_item_failures
    }
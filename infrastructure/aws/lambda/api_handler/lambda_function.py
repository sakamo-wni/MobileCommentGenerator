"""
AWS Lambda API Handler for Weather Comment Generator

APIゲートウェイからのリクエストを処理し、
非同期でコメント生成を実行
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.logging import correlation_paths
from pydantic import BaseModel, ValidationError

# AWS Lambda Powertools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# AWS Resources
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# Environment variables
COMMENTS_TABLE = os.environ['DYNAMODB_COMMENTS_TABLE']
QUEUE_URL = os.environ['SQS_QUEUE_URL']
CORS_ORIGIN = os.environ.get('CORS_ORIGIN', '*')

# DynamoDB table
comments_table = dynamodb.Table(COMMENTS_TABLE)


class CommentRequest(BaseModel):
    """コメント生成リクエストモデル"""
    location: str
    llm_provider: str = "gemini"
    use_cache: bool = True
    priority: str = "normal"  # normal, high
    metadata: Optional[Dict[str, Any]] = None


class CommentResponse(BaseModel):
    """コメント生成レスポンスモデル"""
    request_id: str
    status: str  # pending, processing, completed, failed
    message: str
    estimated_time: int  # seconds
    result_url: Optional[str] = None


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Lambda response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': CORS_ORIGIN,
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body, ensure_ascii=False)
    }


@tracer.capture_method
def validate_request(event: Dict[str, Any]) -> CommentRequest:
    """リクエストのバリデーション"""
    try:
        body = json.loads(event.get('body', '{}'))
        return CommentRequest(**body)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error(f"Invalid request: {str(e)}")
        raise ValueError(f"Invalid request format: {str(e)}")


@tracer.capture_method
def send_to_sqs(request_id: str, request: CommentRequest) -> None:
    """SQSキューにメッセージを送信"""
    message = {
        'request_id': request_id,
        'location': request.location,
        'llm_provider': request.llm_provider,
        'use_cache': request.use_cache,
        'timestamp': datetime.utcnow().isoformat(),
        'metadata': request.metadata or {}
    }
    
    # 優先度に応じてメッセージ属性を設定
    message_attributes = {
        'priority': {
            'StringValue': request.priority,
            'DataType': 'String'
        }
    }
    
    # メッセージ送信
    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message),
        MessageAttributes=message_attributes,
        MessageGroupId=request.location if request.priority == 'high' else None
    )
    
    logger.info(f"Message sent to SQS: {response['MessageId']}")
    metrics.add_metric(name="MessagesSentToSQS", unit=MetricUnit.Count, value=1)


@tracer.capture_method
def check_existing_comment(location: str, use_cache: bool) -> Optional[Dict[str, Any]]:
    """キャッシュから既存のコメントを確認"""
    if not use_cache:
        return None
    
    try:
        # 直近1時間以内のコメントを検索
        response = comments_table.query(
            KeyConditionExpression='location_id = :location',
            ExpressionAttributeValues={
                ':location': location
            },
            ScanIndexForward=False,  # 新しい順
            Limit=1
        )
        
        if response['Items']:
            item = response['Items'][0]
            # TTLチェック（1時間以内）
            generated_at = datetime.fromisoformat(item['generated_at'])
            age_minutes = (datetime.utcnow() - generated_at).total_seconds() / 60
            
            if age_minutes < 60:
                logger.info(f"Cache hit for location: {location}")
                metrics.add_metric(name="CacheHits", unit=MetricUnit.Count, value=1)
                return item
        
        metrics.add_metric(name="CacheMisses", unit=MetricUnit.Count, value=1)
        return None
        
    except Exception as e:
        logger.error(f"Error checking cache: {str(e)}")
        return None


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for API requests
    
    POST /generate - 新規コメント生成リクエスト
    GET /status/{request_id} - 生成状況確認
    GET /result/{request_id} - 生成結果取得
    """
    
    try:
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        logger.info(f"Request: {http_method} {path}")
        
        if http_method == 'POST' and path == '/generate':
            # 新規コメント生成リクエスト
            request = validate_request(event)
            
            # キャッシュチェック
            cached_comment = check_existing_comment(request.location, request.use_cache)
            if cached_comment:
                return create_response(200, {
                    'request_id': cached_comment.get('comment_id'),
                    'status': 'completed',
                    'message': 'Retrieved from cache',
                    'result': {
                        'comment': cached_comment.get('generated_comment'),
                        'advice': cached_comment.get('advice_comment'),
                        'weather_data': cached_comment.get('weather_data'),
                        'cached': True
                    }
                })
            
            # 新規生成リクエスト
            request_id = str(uuid.uuid4())
            
            # SQSに送信
            send_to_sqs(request_id, request)
            
            # レスポンス
            response = CommentResponse(
                request_id=request_id,
                status='pending',
                message='Comment generation request accepted',
                estimated_time=30,  # 推定30秒
                result_url=f"/result/{request_id}"
            )
            
            metrics.add_metric(name="NewRequests", unit=MetricUnit.Count, value=1)
            return create_response(202, response.dict())
            
        elif http_method == 'GET' and path.startswith('/status/'):
            # ステータス確認
            request_id = path.split('/')[-1]
            
            # DynamoDBから状態を確認
            # 実装は省略
            
            return create_response(200, {
                'request_id': request_id,
                'status': 'processing',
                'message': 'Comment generation in progress'
            })
            
        elif http_method == 'GET' and path.startswith('/result/'):
            # 結果取得
            request_id = path.split('/')[-1]
            
            # DynamoDBから結果を取得
            # 実装は省略
            
            return create_response(200, {
                'request_id': request_id,
                'status': 'completed',
                'result': {
                    'comment': 'Generated comment',
                    'advice': 'Advice comment',
                    'weather_data': {}
                }
            })
            
        else:
            return create_response(404, {'error': 'Not found'})
            
    except ValueError as e:
        return create_response(400, {'error': str(e)})
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        metrics.add_metric(name="Errors", unit=MetricUnit.Count, value=1)
        return create_response(500, {'error': 'Internal server error'})
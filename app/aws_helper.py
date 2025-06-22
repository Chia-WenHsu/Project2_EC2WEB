import json
from aiobotocore.session import get_session
from aiohttp import TCPConnector

INPUT_BUCKET = "nicoproject2input"
REQUEST_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-request-q"

_session = get_session()

def get_connector():
    return TCPConnector(limit=128)

async def upload_img_to_s3(file_bytes: bytes, key: str):
    """非同步上傳圖片到 S3 input bucket"""
    async with _session.create_client(
        's3',
        region_name='ap-northeast-2',
        connector=get_connector()
    ) as s3:
        await s3.put_object(
            Bucket=INPUT_BUCKET,
            Key=key,
            Body=file_bytes
        )

async def send_request_to_q(request_id: str, s3_key: str):
    """非同步送訊息到 SQS request queue"""
    async with _session.create_client(
        'sqs',
        region_name='ap-northeast-2',
        connector=get_connector()
    ) as client:
        message = json.dumps({
            "requestId": request_id,
            "s3Key": s3_key
        })
        await client.send_message(
            QueueUrl=REQUEST_QUEUE_URL,
            MessageBody=message
        )
import json
from aiobotocore.session import get_session

INPUT_BUCKET = "nicoproject2input"
REQUEST_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-request-q"

_session = get_session()

async def upload_img_to_s3(file_bytes: bytes, key: str):
    async with _session.create_client('s3', region_name='ap-northeast-2') as s3:
        await s3.put_object(
            Bucket=INPUT_BUCKET,
            Key=key,
            Body=file_bytes
        )

async def send_request_to_q(request_id: str, s3_key: str):
    async with _session.create_client('sqs', region_name='ap-northeast-2') as client:
        message = json.dumps({
            "requestId": request_id,
            "s3Key": s3_key
        })
        await client.send_message(
            QueueUrl=REQUEST_QUEUE_URL,
            MessageBody=message
        )

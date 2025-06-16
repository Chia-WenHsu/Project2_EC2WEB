from fastapi import APIRouter, UploadFile, File
from fastapi.responses import PlainTextResponse
import uuid
import time
import boto3
import json
from .aws_helper import upload_img_to_s3, send_request_to_q
from datetime import datetime
from aiobotocore.session import get_session
import time
import os

router = APIRouter()

# 回應 queue URL
RESPONSE_QUEUE_URL = 'https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-response-q'

async def wait_for_result_async(request_id: str, timeout_seconds=30) -> str | None:
    session = get_session()
    async with session.create_client('sqs', region_name='ap-northeast-2') as client:
        start = time.time()
        while time.time() - start < timeout_seconds:
            response = await client.receive_message(
                QueueUrl=RESPONSE_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=5
            )

            messages = response.get("Messages", [])
            for message in messages:
                body = message["Body"]

                if not body.startswith(request_id + ","):
                    continue

                _, result = body.split(",", 1)

                await client.delete_message(
                    QueueUrl=RESPONSE_QUEUE_URL,
                    ReceiptHandle=message["ReceiptHandle"]
                )

                return result
    return None

@router.post("/predict")
async def predict(image: UploadFile = File(...)):
    filename_wo_ext = os.path.splitext(image.filename)[0]
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    s3_key = f"{filename_wo_ext}_{timestamp}.jpeg"
    request_id = s3_key

    try:
        await upload_img_to_s3(image.file, s3_key)
        await send_request_to_q(request_id, s3_key)

        result = await wait_for_result_async(request_id)

        if result:
            return PlainTextResponse(f"{s3_key} uploaded!\nClassification result: {result}")
        else:
            return PlainTextResponse(f"{s3_key} uploaded!\nClassification result: TIMEOUT")
    except Exception as e:
        return PlainTextResponse(f"Error during processing: {str(e)}", status_code=500)
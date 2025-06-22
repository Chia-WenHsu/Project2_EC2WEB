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
import traceback  
import asyncio

router = APIRouter()

# 回應 queue URL
RESPONSE_QUEUE_URL = 'https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-response-q'

async def wait_for_result_async(request_id: str, timeout_seconds=480) -> str | None:
    session = get_session()
    async with session.create_client('sqs', region_name='ap-northeast-2') as client:
        start = time.time()
        attempt = 0
        while time.time() - start < timeout_seconds:
            attempt += 1
            print(f"[{request_id}] polling attempt {attempt}")
            response = await client.receive_message(
                QueueUrl=RESPONSE_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=1
            )

            messages = response.get("Messages", [])
            print(f"[{request_id}] received {len(messages)} messages")

            for message in messages:
                body = message.get("Body", "")
                parts = body.split(",")
                if len(parts) != 3:
                    print(f"[{request_id}] Skip invalid format: {body}")
                    continue

                msg_request_id, _, result = parts
                print(f"[{request_id}] Got msg_request_id={msg_request_id}")

                if msg_request_id != request_id:
                    print(f"[{request_id}] Not match → skip (do not delete)")
                    continue

                # 匹配成功 → 刪除並回傳結果
                await client.delete_message(
                    QueueUrl=RESPONSE_QUEUE_URL,
                    ReceiptHandle=message["ReceiptHandle"]
                )
                print(f"[{request_id}] Matched. Returning result.")
                return result

            await asyncio.sleep(0.1)  # 防止 CPU 過載

        print(f"[{request_id}] Timeout after {timeout_seconds}s")
        return None

@router.post("/predict")
async def predict(image: UploadFile = File(..., alias="myfile")):
    filename_wo_ext = os.path.splitext(image.filename)[0]
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    s3_key = f"{filename_wo_ext}_{timestamp}.jpeg"
    request_id = f"{filename_wo_ext}_{timestamp}"

    try:
        file_bytes = await image.read()  # 這是 async 方式
        await upload_img_to_s3(file_bytes, s3_key)
        await send_request_to_q(request_id, s3_key)

        await asyncio.sleep(2.0)

        result = await wait_for_result_async(request_id)

        if result:
            return PlainTextResponse(f"{s3_key} uploaded!\nClassification result: {result}")
        else:
            return PlainTextResponse(f"{s3_key} uploaded!\nClassification result: TIMEOUT")
    except Exception as e:
        traceback.print_exc()  
        return PlainTextResponse(f"Error during processing: {str(e)}", status_code=500)
import json
from aiobotocore.session import get_session
import time
import asyncio


INPUT_BUCKET = "nicoproject2input"
REQUEST_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-request-q"
RESPONSE_QUEUE_URL = 'https://sqs.ap-northeast-2.amazonaws.com/530751794867/project2-response-q'

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

        
async def wait_for_result_async(request_id: str, timeout_seconds=60) -> str | None:
    
    async with _session.create_client('sqs', region_name='ap-northeast-2') as client:
        start = time.time()
        attempt = 0
        while time.time() - start < timeout_seconds:
            attempt += 1
            print(f"[{request_id}] polling attempt {attempt}")
            response = await client.receive_message(
                QueueUrl=RESPONSE_QUEUE_URL,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=5
            )

            messages = response.get("Messages", [])
            print(f"[{request_id}] received {len(messages)} messages")

            for message in messages:
                body = message.get("Body", "")
                parts = body.split(",")
                if len(parts) != 3:
                    ##print(f"[{request_id}] Skip invalid format: {body}")
                    continue

                msg_request_id, _, result = parts
                ##print(f"[{request_id}] Got msg_request_id={msg_request_id}")

                if msg_request_id != request_id:
                    print(f"[{request_id}] Not match → skip (do not delete)")
                    await client.change_message_visibility(
                        QueueUrl=RESPONSE_QUEUE_URL,
                        ReceiptHandle=message["ReceiptHandle"],
                        VisibilityTimeout=5
                    )
                    continue

                # 匹配成功 → 刪除並回傳結果
                await client.delete_message(
                    QueueUrl=RESPONSE_QUEUE_URL,
                    ReceiptHandle=message["ReceiptHandle"]
                )
                print(f"[{request_id}] Matched. Returning result.")
                return result

            await asyncio.sleep(0.5)  # 防止 CPU 過載

        print(f"[{request_id}] Timeout after {timeout_seconds}s")
        return None

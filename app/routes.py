from fastapi import APIRouter, UploadFile, File
from fastapi.responses import PlainTextResponse
import uuid
import time
import boto3
import json
from .aws_helper import upload_img_to_s3, send_request_to_q,wait_for_result_async
from datetime import datetime
from aiobotocore.session import get_session
import time
import os
import traceback  
import asyncio
from .globalResponseCache import response_cache, response_cache_lock

router = APIRouter()



@router.post("/predict")
async def predict(image: UploadFile = File(..., alias="myfile")):
    filename_wo_ext = os.path.splitext(image.filename)[0]
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    s3_key = f"{filename_wo_ext}_{timestamp}.jpeg"
    request_id = f"{filename_wo_ext}_{timestamp}"

    try:
        file_bytes = await image.read()  
        await upload_img_to_s3(file_bytes, s3_key)
        await send_request_to_q(request_id, s3_key)

        for _ in range(120):
            with response_cache_lock:
                if request_id in response_cache:
                    result = response_cache.pop(request_id)
                    return PlainTextResponse(f"{s3_key} uploaded!\nClassification result: {result}")
            await asyncio.sleep(1)  

        ##result = await wait_for_result_async(request_id)

        return PlainTextResponse(f"{s3_key} uploaded!\nClassification result: TIMEOUT")
    
    except Exception as e:
        traceback.print_exc()  
        return PlainTextResponse(f"Error during processing: {str(e)}", status_code=500)
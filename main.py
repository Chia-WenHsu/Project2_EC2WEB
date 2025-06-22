from fastapi import FastAPI
from app.routes import router
from app.test_route import test_router
from app.AutoScaler import scale_app_instances
from app.AutoScaler import get_sqs_q_depth
from app.AutoScaler import get_current_app_instance
import asyncio
import os

app = FastAPI()  

app.include_router(router)
app.include_router(test_router)

main_pid = os.getpid()

@app.on_event("startup")
async def startup_event():
    await asyncio.sleep(5)
    print("System ready. Web API starting...")

    if os.getpid() == main_pid:
        print(" This is the main process, launching AutoScaler...")
        asyncio.create_task(start_autoscaler_loop())
    else:
        print(" Not main process, skipping AutoScaler.")

async def start_autoscaler_loop():
    print(" AutoScaler background task started.")
    while True:
        try:
            await scale_app_instances()
        except Exception as e:
            print(f"[AutoScaler Error] {e}")
        await asyncio.sleep(5)

async def status():
    depth = await get_sqs_q_depth()
    current_instances = await get_current_app_instance()
    current = len(current_instances)
    return {
        "queue_depth": depth,
        "current_instances": current
    }